# -*- coding: utf-8 -*-
"""
数据缓存（HistoryCache）

按 (symbol, period, interval, today) 对历史数据建立 LRU 缓存，
减少对 yfinance 的重复请求。仅缓存不可变结果；当日自然过期。
"""

from collections import OrderedDict
from datetime import date
from threading import Lock
from typing import Optional

import pandas as pd


class HistoryCache:
    """简单的 LRU + 自然日过期 缓存"""

    def __init__(self, max_entries: int = 64):
        self._max = max_entries
        self._cache: "OrderedDict[tuple, pd.DataFrame]" = OrderedDict()
        self._lock = Lock()
        self.hits = 0
        self.misses = 0

    def _key(self, symbol: str, period: str, interval: str, today: Optional[date] = None) -> tuple:
        return (
            symbol.upper(),
            period,
            interval,
            (today or date.today()).isoformat(),
        )

    def get(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        key = self._key(symbol, period, interval)
        with self._lock:
            df = self._cache.get(key)
            if df is not None:
                self._cache.move_to_end(key)
                self.hits += 1
                return df.copy()
            self.misses += 1
            return None

    def put(self, symbol: str, period: str, interval: str, df: pd.DataFrame) -> None:
        if df is None or df.empty:
            return
        key = self._key(symbol, period, interval)
        with self._lock:
            self._cache[key] = df.copy()
            self._cache.move_to_end(key)
            while len(self._cache) > self._max:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "entries": len(self._cache),
            "max": self._max,
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": round(self.hits / total, 4) if total else 0.0,
        }
