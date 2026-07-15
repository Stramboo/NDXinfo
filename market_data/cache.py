# -*- coding: utf-8 -*-
"""
market_data/cache.py — 行情数据内存缓存

支持 TTL 过期、新鲜度标记、自动失效。
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from market_data.models import BarsResult, Quote

logger = logging.getLogger(__name__)


@dataclass
class _CacheEntry:
    data: object
    cached_at: float  # epoch seconds


class MarketDataCache:
    """线程安全的行情数据内存缓存

    TTL 规则:
      - 报价 (Quote): 30 秒
      - K 线 (BarsResult): 5 分钟
      - 市场状态: 60 秒
    """

    QUOTE_TTL = 30       # seconds
    BARS_TTL = 300       # 5 minutes
    STATUS_TTL = 60      # 1 minute

    def __init__(self):
        self._quotes: dict[str, _CacheEntry] = {}
        self._bars: dict[str, _CacheEntry] = {}      # key: "SYMBOL:period:interval"
        self._status: Optional[_CacheEntry] = None
        self._lock = threading.Lock()

    def get_quote(self, symbol: str) -> Optional[Quote]:
        with self._lock:
            entry = self._quotes.get(symbol.upper())
            if entry and time.time() - entry.cached_at < self.QUOTE_TTL:
                return entry.data
        return None

    def set_quote(self, symbol: str, quote: Quote) -> None:
        with self._lock:
            self._quotes[symbol.upper()] = _CacheEntry(
                data=quote, cached_at=time.time(),
            )

    def get_bars(self, symbol: str, period: str, interval: str) -> Optional[BarsResult]:
        key = f"{symbol.upper()}:{period}:{interval}"
        with self._lock:
            entry = self._bars.get(key)
            if entry and time.time() - entry.cached_at < self.BARS_TTL:
                return entry.data
        return None

    def set_bars(self, symbol: str, period: str, interval: str, result: BarsResult) -> None:
        key = f"{symbol.upper()}:{period}:{interval}"
        with self._lock:
            self._bars[key] = _CacheEntry(data=result, cached_at=time.time())

    def get_status(self) -> Optional[object]:
        with self._lock:
            if self._status and time.time() - self._status.cached_at < self.STATUS_TTL:
                return self._status.data
        return None

    def set_status(self, status: object) -> None:
        with self._lock:
            self._status = _CacheEntry(data=status, cached_at=time.time())

    def invalidate(self) -> None:
        """清除所有缓存"""
        with self._lock:
            self._quotes.clear()
            self._bars.clear()
            self._status = None
