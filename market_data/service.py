# -*- coding: utf-8 -*-
"""
market_data/service.py — 统一市场数据服务

所有模块获取行情数据的唯一入口。
禁止直接调用 yfinance / Alpaca 等底层 Provider。
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from market_data.cache import MarketDataCache
from market_data.models import BarsResult, Quote, MarketStatus
from market_data.providers.base import MarketDataProvider
from market_data.providers.mock import MockProvider

logger = logging.getLogger(__name__)


class MarketDataService:
    """统一市场数据服务

    根据环境自动选择 Provider:
      - Demo/Dev/Test → MockProvider
      - 有 DEEPSEEK/REAL 标记 → YahooProvider（需要时）
      - 默认 → YahooProvider（回退 MockProvider）

    所有方法返回标准化的 market_data.models 类型。
    """

    _instance: Optional["MarketDataService"] = None

    def __init__(self, provider: MarketDataProvider | None = None):
        self._provider: MarketDataProvider = provider or self._create_provider()
        self._cache = MarketDataCache()

    @staticmethod
    def _create_provider() -> MarketDataProvider:
        backend = os.environ.get("NDXINFO_BACKEND", "mock").lower()
        if backend in ("demo", "dev", "test", "mock"):
            return MockProvider()
        try:
            from market_data.providers.yahoo import YahooProvider
            return YahooProvider()
        except Exception:
            logger.info("YahooProvider 不可用，回退 MockProvider")
            return MockProvider()

    @classmethod
    def get_instance(cls) -> "MarketDataService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ---- 公开 API ----

    def get_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d",
        use_cache: bool = True,
    ) -> BarsResult:
        """获取历史 K 线"""
        sym = symbol.upper()
        if use_cache:
            cached = self._cache.get_bars(sym, period, interval)
            if cached:
                return cached

        result = self._provider.get_bars(sym, period, interval)
        self._cache.set_bars(sym, period, interval, result)
        return result

    def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[Quote]:
        """获取实时报价"""
        sym = symbol.upper()
        if use_cache:
            cached = self._cache.get_quote(sym)
            if cached:
                return cached

        quote = self._provider.get_quote(sym)
        if quote:
            self._cache.set_quote(sym, quote)
        return quote

    def get_batch_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """批量获取报价"""
        result: dict[str, Quote] = {}
        uncached: list[str] = []
        for sym in symbols:
            cached = self._cache.get_quote(sym.upper())
            if cached:
                result[sym] = cached
            else:
                uncached.append(sym)

        if uncached:
            batch = self._provider.get_batch_quotes(uncached)
            for sym, quote in batch.items():
                result[sym] = quote
                self._cache.set_quote(sym, quote)
        return result

    def get_bars_as_dataframe(
        self, symbol: str, period: str = "1y", interval: str = "1d",
    ) -> pd.DataFrame:
        """获取 K 线并转为 DataFrame（兼容现有代码）"""
        return self.get_bars(symbol, period, interval).to_dataframe()

    def get_market_status(self) -> MarketStatus:
        cached = self._cache.get_status()
        if cached:
            return cached
        status = self._provider.get_market_status()
        self._cache.set_status(status)
        return status

    def supports_symbol(self, symbol: str) -> bool:
        return self._provider.supports_symbol(symbol.upper())

    def invalidate_cache(self) -> None:
        self._cache.invalidate()


__all__ = ["MarketDataService"]
