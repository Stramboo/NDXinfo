# -*- coding: utf-8 -*-
"""
market_data/providers/base.py — Provider 抽象基类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from market_data.models import BarsResult, Quote, MarketStatus


class MarketDataProvider(ABC):
    """所有行情数据提供者的抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称（如 'yahoo', 'mock', 'alpaca'）"""
        ...

    @abstractmethod
    def get_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> BarsResult:
        """获取历史 K 线数据"""
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """获取实时报价"""
        ...

    @abstractmethod
    def get_market_status(self) -> MarketStatus:
        """获取市场交易状态"""
        ...

    def get_batch_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """批量获取报价（默认实现，子类可覆盖优化）"""
        result: dict[str, Quote] = {}
        for sym in symbols:
            q = self.get_quote(sym)
            if q:
                result[sym] = q
        return result

    def supports_symbol(self, symbol: str) -> bool:
        """判断是否支持该标的（默认 True）"""
        return True
