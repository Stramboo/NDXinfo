# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 数据获取模块
封装 yfinance API 调用，处理限流、重试、异常、数据清洗
"""

import yfinance as yf
import pandas as pd
import time
import logging
from config import (
    HISTORY_PERIOD, HISTORY_INTERVAL, REQUEST_INTERVAL,
    MAX_RETRIES, RETRY_BACKOFF, SCREENER_TOP_N
)

logger = logging.getLogger(__name__)


class DataFetcher:
    """yfinance 数据获取封装类"""

    def __init__(self):
        self._last_request_time = 0

    def _rate_limit(self):
        """请求间隔，避免触发 Yahoo 速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _retry(self, func, *args, **kwargs):
        """带指数退避的重试机制"""
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                self._rate_limit()
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                wait = RETRY_BACKOFF ** attempt
                logger.warning(f"第{attempt + 1}次尝试失败: {e}，{wait}秒后重试...")
                time.sleep(wait)
        logger.error(f"重试{MAX_RETRIES}次后仍失败: {last_exception}")
        return None

    def _normalize_columns(self, df, ticker=None):
        """标准化列名，处理 MultiIndex"""
        if df is None or df.empty:
            return df

        # 处理 MultiIndex 列（批量下载时）
        if isinstance(df.columns, pd.MultiIndex):
            # 如果是单 ticker 的 MultiIndex，取第一层
            if ticker and ticker in df.columns.get_level_values(0):
                df = df[ticker]
            else:
                df.columns = df.columns.get_level_values(0)

        # 确保列名是字符串
        df.columns = [str(col).capitalize() for col in df.columns]

        # 去除可能的重复列
        df = df.loc[:, ~df.columns.duplicated()]

        return df

    def fetch_index_history(self, ticker, period=HISTORY_PERIOD):
        """
        获取指数历史数据，返回含 OHLCV 的 DataFrame
        ticker: 如 "^IXIC", "^NDX", "^VIX"
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

    def fetch_stocks_batch(self, tickers, period=HISTORY_PERIOD):
        """
        批量下载多只股票，利用多线程
        返回: dict[str, DataFrame]
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

    def fetch_stock_info(self, ticker):
        """获取股票基本信息（名称、板块、市值）"""
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

    def screen_top_nasdaq_gainers(self, top_n=SCREENER_TOP_N):
        """
        动态筛选 NASDAQ 涨幅榜 Top N
        使用 yf.screen 预定义查询 day_gainers
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

    def _parse_screen_result(self, result, top_n):
        """解析 yf.screen 返回结果"""
        gainers = []

        # yf.screen 返回格式可能因版本不同有变化
        # 尝试多种可能的返回结构
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
        """降级方案：从已知热门股票中获取当日表现"""
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
