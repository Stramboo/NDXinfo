# -*- coding: utf-8 -*-
"""
数据提供者抽象基类模块

定义统一的数据获取接口 DataProvider，所有具体数据源
（yfinance、akshare 等）均需实现该接口。
基类同时提供限流、重试、列名标准化等通用工具方法，
供各子类复用。
"""

import time
import logging
import pandas as pd
from abc import ABC, abstractmethod

from config import REQUEST_INTERVAL, MAX_RETRIES, RETRY_BACKOFF

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """
    数据提供者抽象基类

    所有具体数据源提供者需继承此类并实现以下抽象方法：
        - fetch_history(ticker, period)    获取单只标的历史行情
        - fetch_batch(tickers, period)     批量获取多只标的历史行情
        - fetch_info(ticker)               获取标的基本信息
        - screen_gainers(top_n)            筛选涨幅榜

    子类可直接复用 _rate_limit / _retry / _normalize_columns 工具方法。
    """

    def __init__(self):
        # 记录最近一次请求时间戳，用于限流控制
        self._last_request_time = 0

    # ============================================================
    # 抽象方法 - 子类必须实现
    # ============================================================

    @abstractmethod
    def fetch_history(self, ticker, period="1y"):
        """
        获取单只标的历史行情数据

        参数:
            ticker: 标的代码
            period: 数据周期，如 "1y"、"3mo"

        返回:
            pd.DataFrame，含 OHLCV 列（Open, High, Low, Close, Volume）
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_batch(self, tickers, period="1y"):
        """
        批量获取多只标的历史行情数据

        参数:
            tickers: 标的代码列表
            period: 数据周期

        返回:
            dict[str, pd.DataFrame]，键为标的代码，值为对应 DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_info(self, ticker):
        """
        获取标的基本信息

        参数:
            ticker: 标的代码

        返回:
            dict，至少包含 name、sector、market_cap 字段
        """
        raise NotImplementedError

    @abstractmethod
    def screen_gainers(self, top_n=10):
        """
        筛选涨幅榜

        参数:
            top_n: 返回前 N 只

        返回:
            list[dict]，每项含 ticker、name、price、change_pct 等字段
        """
        raise NotImplementedError

    # ============================================================
    # 通用工具方法 - 子类可直接复用
    # ============================================================

    def _rate_limit(self):
        """请求间隔控制，避免触发数据源速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _retry(self, func, *args, **kwargs):
        """
        带指数退避的重试机制

        参数:
            func: 需要重试的可调用对象
            *args, **kwargs: 传递给 func 的参数

        返回:
            func 的返回值；若重试 MAX_RETRIES 次后仍失败，返回 None
        """
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
        """
        标准化 DataFrame 列名，处理 MultiIndex 情况

        参数:
            df: 原始 DataFrame
            ticker: 当列为 MultiIndex 时，指定提取哪个 ticker 的子表

        返回:
            列名标准化（首字母大写）后的 DataFrame
        """
        if df is None or df.empty:
            return df

        # 处理 MultiIndex 列（批量下载时常见）
        if isinstance(df.columns, pd.MultiIndex):
            # 如果是单 ticker 的 MultiIndex，取该 ticker 对应的子表
            if ticker and ticker in df.columns.get_level_values(0):
                df = df[ticker]
            else:
                df.columns = df.columns.get_level_values(0)

        # 确保列名为字符串并首字母大写
        df.columns = [str(col).capitalize() for col in df.columns]

        # 去除可能的重复列
        df = df.loc[:, ~df.columns.duplicated()]

        return df
