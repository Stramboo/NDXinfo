# -*- coding: utf-8 -*-
"""
yfinance 数据提供者模块

基于 yfinance 实现美股数据获取，是 DataProvider 的具体实现。
本模块从原 data_fetcher.py 迁移全部 yfinance 相关逻辑，
包括指数历史数据、批量股票下载、股票基本信息、NASDAQ 涨幅榜筛选等。
"""

import yfinance as yf
import pandas as pd
import logging

from config import (
    HISTORY_PERIOD, HISTORY_INTERVAL, SCREENER_TOP_N,
)
from providers.base import DataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(DataProvider):
    """
    基于 yfinance 的美股数据提供者

    实现 DataProvider 接口，封装 yfinance API 调用，
    处理限流、重试、异常、数据清洗等通用逻辑。
    """

    def __init__(self):
        super().__init__()

    # ============================================================
    # 接口方法实现
    # ============================================================

    def fetch_history(self, ticker, period=HISTORY_PERIOD):
        """
        获取标的（指数/股票）历史数据，返回含 OHLCV 的 DataFrame

        参数:
            ticker: 标的代码，如 "^IXIC"、"^NDX"、"^VIX"、"AAPL"
            period: 数据周期，如 "1y"、"3mo"

        返回:
            pd.DataFrame，含 Open、High、Low、Close、Volume 列
        """
        def _download():
            df = yf.download(
                ticker, period=period, interval=HISTORY_INTERVAL,
                auto_adjust=True, progress=False, repair=True
            )
            return df

        result = self._retry(_download)
        if result is None or result.empty:
            logger.warning(f"获取 {ticker} 数据失败，返回空 DataFrame")
            return pd.DataFrame()

        result = self._normalize_columns(result, ticker)
        logger.info(f"获取 {ticker} 数据成功: {len(result)} 条记录")
        return result

    def fetch_index_history(self, ticker, period=HISTORY_PERIOD):
        """
        获取指数历史数据（向后兼容别名）

        sector.py 等旧调用方通过 fetcher.fetch_index_history() 访问，
        此方法作为 fetch_history 的别名，保持向后兼容。

        参数:
            ticker: 指数代码，如 "^IXIC"、"^NDX"、"^VIX"
            period: 数据周期

        返回:
            pd.DataFrame，含 OHLCV 列
        """
        return self.fetch_history(ticker, period)

    def fetch_batch(self, tickers, period=HISTORY_PERIOD):
        """
        批量下载多只股票，利用 yfinance 多线程

        参数:
            tickers: 股票代码列表
            period: 数据周期

        返回:
            dict[str, pd.DataFrame]，键为股票代码，值为对应 DataFrame
        """
        def _download():
            df = yf.download(
                tickers, period=period, interval=HISTORY_INTERVAL,
                auto_adjust=True, progress=False, threads=True,
                group_by='ticker', repair=True
            )
            return df

        result = self._retry(_download)
        if result is None or result.empty:
            logger.warning("批量下载股票数据失败")
            return {t: pd.DataFrame() for t in tickers}

        stocks = {}
        for ticker in tickers:
            try:
                if isinstance(result.columns, pd.MultiIndex):
                    if ticker in result.columns.get_level_values(0):
                        stock_df = result[ticker].copy()
                        stock_df.columns = [str(c).capitalize() for c in stock_df.columns]
                        stock_df = stock_df.loc[:, ~stock_df.columns.duplicated()]
                        stocks[ticker] = stock_df
                    else:
                        stocks[ticker] = pd.DataFrame()
                else:
                    # 单只股票时不是 MultiIndex
                    stock_df = result.copy()
                    stock_df.columns = [str(c).capitalize() for c in stock_df.columns]
                    stocks[ticker] = stock_df
            except Exception as e:
                logger.warning(f"解析 {ticker} 数据失败: {e}")
                stocks[ticker] = pd.DataFrame()

        logger.info(f"批量下载 {len(tickers)} 只股票完成，成功 {sum(1 for v in stocks.values() if not v.empty)} 只")
        return stocks

    def fetch_info(self, ticker):
        """
        获取股票基本信息（名称、板块、市值）

        参数:
            ticker: 股票代码

        返回:
            dict，含 name、sector、market_cap 字段
        """
        def _get_info():
            t = yf.Ticker(ticker)
            info = t.info
            return {
                "name": info.get("shortName") or info.get("longName") or ticker,
                "sector": info.get("sector", "N/A"),
                "market_cap": info.get("marketCap"),
            }

        result = self._retry(_get_info)
        if result is None:
            return {"name": ticker, "sector": "N/A", "market_cap": None}
        return result

    def screen_gainers(self, top_n=SCREENER_TOP_N):
        """
        动态筛选 NASDAQ 涨幅榜 Top N

        优先使用 yf.screen 预定义查询 day_gainers，
        若不可用则降级为从已知热门股票中获取当日表现。

        参数:
            top_n: 返回前 N 只涨幅股

        返回:
            list[dict]，每项含 ticker、name、price、change_pct、volume、market_cap
        """
        def _screen():
            # 尝试使用预定义查询
            try:
                result = yf.screen("day_gainers", size=top_n * 3)
                return self._parse_screen_result(result, top_n)
            except Exception:
                # 降级方案：使用 Ticker 逐个获取（效率较低但更稳定）
                logger.warning("yf.screen 不可用，使用降级方案获取热门股票")
                return self._fallback_screen(top_n)

        result = self._retry(_screen)
        if result is None:
            return []
        return result

    # ============================================================
    # 内部辅助方法
    # ============================================================

    def _parse_screen_result(self, result, top_n):
        """
        解析 yf.screen 返回结果

        yf.screen 返回格式可能因版本不同有变化，
        此方法尝试多种可能的返回结构进行解析。

        参数:
            result: yf.screen 的原始返回值
            top_n: 需要返回的条目数

        返回:
            list[dict]，筛选后的涨幅榜
        """
        gainers = []

        if isinstance(result, dict):
            quotes = result.get("quotes") or result.get("finance", {}).get("result", [{}])[0].get("quotes", [])
        elif isinstance(result, list):
            quotes = result
        else:
            quotes = []

        for q in quotes[:top_n * 2]:
            try:
                exchange = q.get("exchange", "")
                # 过滤 NASDAQ 交易所 (NMS)
                if exchange not in ("NMS", "NGM", "NCM", "Nasdaq"):
                    continue
                ticker = q.get("symbol", "")
                if not ticker:
                    continue
                gainers.append({
                    "ticker": ticker,
                    "name": q.get("shortName") or q.get("longName") or ticker,
                    "price": q.get("regularMarketPrice", 0),
                    "change_pct": round(q.get("regularMarketChangePercent", 0), 2),
                    "volume": q.get("regularMarketVolume", 0),
                    "market_cap": q.get("marketCap"),
                })
                if len(gainers) >= top_n:
                    break
            except Exception:
                continue

        return gainers

    def _fallback_screen(self, top_n):
        """
        降级方案：从已知热门股票中获取当日表现

        当 yf.screen 不可用时，下载一组热门 NASDAQ 股票近5日数据，
        计算当日涨幅并排序取 Top N。

        参数:
            top_n: 返回前 N 只

        返回:
            list[dict]，涨幅榜
        """
        # 使用一组热门 NASDAQ 股票作为备选
        fallback_tickers = [
            "NVDA", "TSLA", "AMD", "META", "AMZN", "AAPL", "MSFT",
            "GOOGL", "NFLX", "AVGO", "COST", "PEP", "ADBE", "INTC",
            "CMCSA", "CSCO", "TMUS", "QCOM", "TXN", "AMGN"
        ]

        def _download():
            df = yf.download(
                fallback_tickers, period="5d", interval="1d",
                auto_adjust=True, progress=False, threads=True,
                group_by='ticker', repair=True
            )
            return df

        result = self._retry(_download)
        if result is None or result.empty:
            return []

        gainers = []
        for ticker in fallback_tickers:
            try:
                if isinstance(result.columns, pd.MultiIndex) and ticker in result.columns.get_level_values(0):
                    stock_df = result[ticker].copy()
                else:
                    continue

                if stock_df.empty or len(stock_df) < 2:
                    continue

                last_close = float(stock_df["Close"].iloc[-1])
                prev_close = float(stock_df["Close"].iloc[-2])
                if prev_close == 0:
                    continue
                change_pct = round((last_close - prev_close) / prev_close * 100, 2)

                gainers.append({
                    "ticker": ticker,
                    "name": ticker,
                    "price": round(last_close, 2),
                    "change_pct": change_pct,
                    "volume": int(stock_df["Volume"].iloc[-1]),
                    "market_cap": None,
                })
            except Exception:
                continue

        # 按涨幅降序排列，取 Top N
        gainers.sort(key=lambda x: x["change_pct"], reverse=True)
        return gainers[:top_n]
