# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 数据获取门面模块（Facade）

本模块作为多数据源的统一入口（门面模式），保持与原有调用方
（nasdaq_analyzer.py、sector.py 等）完全兼容的公共 API。

数据路由规则：
    - 美股（无前缀，如 "AAPL"、"^IXIC"）-> YFinanceProvider
    - 港股（HK: 前缀，如 "HK:0700"）    -> AkshareProvider
    - A 股（SH:/SZ: 前缀，如 "SH:600519"）-> AkshareProvider

当 ENABLE_HK_A_SHARE 配置为 false 时，不初始化 AkshareProvider，
所有 HK:/SH:/SZ: 前缀的标的将返回空数据。
"""

import logging
import pandas as pd

from config import (
    HISTORY_PERIOD, SCREENER_TOP_N, ENABLE_HK_A_SHARE,
)
from providers import YFinanceProvider, AkshareProvider

logger = logging.getLogger(__name__)

# 需要路由到 AkshareProvider 的前缀
_AKSHARE_PREFIXES = ("HK:", "SH:", "SZ:")


class DataFetcher:
    """
    数据获取门面类（Facade）

    封装 YFinanceProvider 和 AkshareProvider，根据标的代码前缀
    自动路由到对应的数据源。对外保持与旧版 DataFetcher 完全一致的
    公共 API，确保 nasdaq_analyzer.py、sector.py 等调用方无需修改。

    公共方法:
        - fetch_index_history(ticker, period)   获取指数历史数据（美股专用）
        - fetch_stocks_batch(tickers, period)   批量获取股票数据（自动路由）
        - fetch_stock_info(ticker)              获取股票基本信息（自动路由）
        - screen_top_nasdaq_gainers(top_n)      筛选 NASDAQ 涨幅榜（美股专用）
    """

    def __init__(self):
        # 保持向后兼容：记录最近一次请求时间戳
        self._last_request_time = 0

        # 美股数据源（始终初始化）
        self._yf_provider = YFinanceProvider()

        # 港股/A股数据源（仅在开启时初始化）
        if ENABLE_HK_A_SHARE:
            self._ak_provider = AkshareProvider()
            logger.info("已启用港股/A股数据支持（AkshareProvider）")
        else:
            self._ak_provider = None

    # ============================================================
    # 路由辅助方法
    # ============================================================

    @staticmethod
    def _is_akshare_ticker(ticker):
        """
        判断标的是否应路由到 AkshareProvider

        参数:
            ticker: 标的代码

        返回:
            bool，若以 HK:/SH:/SZ: 开头则返回 True
        """
        if not isinstance(ticker, str):
            return False
        return ticker.upper().startswith(_AKSHARE_PREFIXES)

    def _get_provider(self, ticker):
        """
        根据标的代码前缀选择数据提供者

        参数:
            ticker: 标的代码

        返回:
            对应的 DataProvider 实例
        """
        if self._is_akshare_ticker(ticker):
            if self._ak_provider is not None:
                return self._ak_provider
            else:
                logger.warning(
                    f"标的 {ticker} 需要 AkshareProvider，但港股/A股支持未启用"
                    "（请在配置中设置 ENABLE_HK_A_SHARE=true）"
                )
                return self._yf_provider
        return self._yf_provider

    # ============================================================
    # 公共 API（向后兼容）
    # ============================================================

    def fetch_index_history(self, ticker, period=HISTORY_PERIOD):
        """
        获取指数历史数据（美股专用，始终使用 YFinanceProvider）

        参数:
            ticker: 指数代码，如 "^IXIC"、"^NDX"、"^VIX"
            period: 数据周期，如 "1y"、"3mo"

        返回:
            pd.DataFrame，含 Open、High、Low、Close、Volume 列
        """
        return self._yf_provider.fetch_history(ticker, period)

    def fetch_stocks_batch(self, tickers, period=HISTORY_PERIOD):
        """
        批量获取多只股票数据（自动按前缀路由）

        将传入的标的列表按前缀分组，分别路由到对应的数据提供者，
        最后合并结果返回。

        参数:
            tickers: 标的代码列表
            period: 数据周期

        返回:
            dict[str, pd.DataFrame]，键为标的代码，值为对应 DataFrame
        """
        if not tickers:
            return {}

        # 按数据源分组
        us_tickers = []
        ak_tickers = []
        for ticker in tickers:
            if self._is_akshare_ticker(ticker):
                ak_tickers.append(ticker)
            else:
                us_tickers.append(ticker)

        result = {}

        # 美股批量下载
        if us_tickers:
            us_result = self._yf_provider.fetch_batch(us_tickers, period)
            result.update(us_result)

        # 港股/A股逐只下载
        if ak_tickers:
            if self._ak_provider is not None:
                ak_result = self._ak_provider.fetch_batch(ak_tickers, period)
                result.update(ak_result)
            else:
                logger.warning(
                    f"存在港股/A股标的 {ak_tickers}，但港股/A股支持未启用"
                )
                for t in ak_tickers:
                    result[t] = pd.DataFrame()

        total = len(tickers)
        success = sum(1 for v in result.values() if not v.empty)
        logger.info(f"批量下载 {total} 只标的完成，成功 {success} 只")
        return result

    def fetch_stock_info(self, ticker):
        """
        获取股票基本信息（自动按前缀路由）

        参数:
            ticker: 标的代码

        返回:
            dict，含 name、sector、market_cap 字段
        """
        provider = self._get_provider(ticker)
        return provider.fetch_info(ticker)

    def screen_top_nasdaq_gainers(self, top_n=SCREENER_TOP_N):
        """
        筛选 NASDAQ 涨幅榜（美股专用，始终使用 YFinanceProvider）

        参数:
            top_n: 返回前 N 只涨幅股

        返回:
            list[dict]，每项含 ticker、name、price、change_pct 等字段
        """
        return self._yf_provider.screen_gainers(top_n)
