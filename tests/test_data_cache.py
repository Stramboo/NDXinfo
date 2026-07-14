# -*- coding: utf-8 -*-
"""HistoryCache / TokenBucket 单测"""
import time

import pandas as pd
import pytest

from trading.data_cache import HistoryCache
from trading.rate_limiter import TokenBucket


class TestHistoryCache:
    def test_put_and_get(self):
        c = HistoryCache(max_entries=8)
        df = pd.DataFrame({"Close": [1.0, 2.0, 3.0]})
        c.put("AAPL", "6mo", "1d", df)
        got = c.get("AAPL", "6mo", "1d")
        assert got is not None
        assert got.shape == (3, 1)
        s = c.stats()
        assert s["hits"] == 1
        assert s["misses"] == 0

    def test_lru_eviction(self):
        c = HistoryCache(max_entries=2)
        c.put("A", "p", "i", pd.DataFrame({"x": [1]}))
        c.put("B", "p", "i", pd.DataFrame({"x": [2]}))
        c.put("C", "p", "i", pd.DataFrame({"x": [3]}))
        # A 应被淘汰
        assert c.get("A", "p", "i") is None
        assert c.get("B", "p", "i") is not None
        assert c.get("C", "p", "i") is not None


class TestTokenBucket:
    def test_burst_then_block(self):
        b = TokenBucket(rate=1.0, burst=2)
        assert b.try_acquire() is True
        assert b.try_acquire() is True
        assert b.try_acquire() is False

    def test_refill_after_wait(self):
        b = TokenBucket(rate=50.0, burst=2)   # 50/s 高频
        b.try_acquire()
        b.try_acquire()
        # 等 100ms 应该可再拿一枚
        time.sleep(0.05)
        assert b.try_acquire() is True
