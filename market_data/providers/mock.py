# -*- coding: utf-8 -*-
"""
market_data/providers/mock.py — Mock 行情数据提供者

基于 MockEngine 的随机价格数据，用于开发和测试环境。
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

from market_data.models import Bar, BarsResult, Quote, MarketStatus
from market_data.providers.base import MarketDataProvider

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# Mock 支持的标的
MOCK_SYMBOLS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
MOCK_BASE_PRICES = {
    "NVDA": 480.00, "AAPL": 175.00, "MSFT": 420.00,
    "GOOGL": 142.00, "AMZN": 178.00, "TSLA": 248.00,
}


class MockProvider(MarketDataProvider):
    """基于 MockEngine 的离线行情数据提供者"""

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from webapp.backend.adapters.mock_engine import MockEngine
            self._engine = MockEngine()
        return self._engine

    @property
    def name(self) -> str:
        return "mock"

    def get_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> BarsResult:
        try:
            engine = self._get_engine()
            df = engine.fetch_history(symbol, period=period)
            bars: list[Bar] = []
            for idx, row in df.iterrows():
                try:
                    ts = idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx
                    bars.append(Bar(
                        timestamp=ts,
                        open=float(row.get("Open", 0)),
                        high=float(row.get("High", 0)),
                        low=float(row.get("Low", 0)),
                        close=float(row.get("Close", 0)),
                        volume=int(row.get("Volume", 0)),
                    ))
                except Exception:
                    pass
            return BarsResult(
                symbol=symbol, bars=bars, source=self.name,
                fetched_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Mock get_bars({symbol}) 失败: {e}")
            return BarsResult(symbol=symbol, bars=[], source=self.name, is_stale=True)

    def get_quote(self, symbol: str) -> Optional[Quote]:
        engine = self._get_engine()
        if symbol not in engine.prices:
            return None
        price = engine.prices[symbol]
        # Mock 无涨跌幅，生成一个随机的
        import random
        change_pct = random.uniform(-2, 2)
        return Quote(
            symbol=symbol, price=price, change_pct=change_pct,
            source=self.name,
        )

    def get_batch_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        engine = self._get_engine()
        import random
        result: dict[str, Quote] = {}
        for sym in symbols:
            if sym.upper() in engine.prices:
                price = engine.prices[sym.upper()]
                result[sym] = Quote(
                    symbol=sym, price=price,
                    change_pct=random.uniform(-2, 2),
                    source=self.name,
                )
        return result

    def get_market_status(self) -> MarketStatus:
        return MarketStatus(is_open=True, exchange="MOCK")

    def supports_symbol(self, symbol: str) -> bool:
        return symbol.upper() in MOCK_SYMBOLS
