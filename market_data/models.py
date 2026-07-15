# -*- coding: utf-8 -*-
"""
market_data/models.py — 统一市场数据模型

所有 Provider 返回标准化的数据结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Bar:
    """单根 K 线"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Quote:
    """实时报价"""
    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    change_pct: float = 0.0
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "unknown"


@dataclass
class MarketStatus:
    """市场状态"""
    is_open: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    exchange: str = "NASDAQ"


@dataclass
class BarsResult:
    """历史 K 线查询结果"""
    symbol: str
    bars: list[Bar]
    source: str
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_stale: bool = False

    def to_dataframe(self):
        """转为 pandas DataFrame（兼容现有指标计算）"""
        import pandas as pd
        if not self.bars:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        data = {
            "Date": [b.timestamp for b in self.bars],
            "Open": [b.open for b in self.bars],
            "High": [b.high for b in self.bars],
            "Low": [b.low for b in self.bars],
            "Close": [b.close for b in self.bars],
            "Volume": [b.volume for b in self.bars],
        }
        df = pd.DataFrame(data)
        df = df.set_index("Date")
        return df
