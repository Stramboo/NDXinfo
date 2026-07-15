# -*- coding: utf-8 -*-
"""
market_data/providers/yahoo.py — Yahoo Finance Provider

封装现有 providers/yfinance_provider.py 到新的统一接口。
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from market_data.models import Bar, BarsResult, Quote, MarketStatus
from market_data.providers.base import MarketDataProvider

logger = logging.getLogger(__name__)

# 确保项目根在 path 中
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class YahooProvider(MarketDataProvider):
    """Yahoo Finance 行情数据提供者"""

    @property
    def name(self) -> str:
        return "yahoo"

    def get_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> BarsResult:
        try:
            from providers.yfinance_provider import YFinanceProvider
            provider = YFinanceProvider()
            df = provider.fetch_history(symbol, period=period)
            df = df.copy()
            # 统一列名
            if "open" in df.columns:
                df = df.rename(columns={
                    "open": "Open", "high": "High",
                    "low": "Low", "close": "Close", "volume": "Volume",
                })
            bars = _df_to_bars(df, symbol)
            return BarsResult(
                symbol=symbol, bars=bars, source=self.name,
                fetched_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Yahoo get_bars({symbol}) 失败: {e}")
            return BarsResult(symbol=symbol, bars=[], source=self.name, is_stale=True)

    def get_quote(self, symbol: str) -> Optional[Quote]:
        try:
            from providers.yfinance_provider import YFinanceProvider
            info = YFinanceProvider().fetch_info(symbol)
            df = YFinanceProvider().fetch_history(symbol, period="5d")
            price = float(df["Close"].iloc[-1]) if not df.empty else 0
            change_pct = 0.0
            if not df.empty and len(df) >= 2:
                prev = float(df["Close"].iloc[-2])
                if prev > 0:
                    change_pct = (price / prev - 1) * 100
            return Quote(
                symbol=symbol, price=price, change_pct=change_pct,
                source=self.name,
            )
        except Exception as e:
            logger.warning(f"Yahoo get_quote({symbol}) 失败: {e}")
            return None

    def get_market_status(self) -> MarketStatus:
        # 美股交易时间粗略判断
        from datetime import datetime as dt
        now = dt.now()
        # 美东时间 9:30-16:00 周一至周五
        wd = now.weekday()
        h = now.hour
        # 简化: 北京时间 21:30 - 次日 4:00 约等于美股开盘
        is_open = 0 <= wd <= 4 and (h >= 21 or h <= 4)
        return MarketStatus(is_open=is_open, exchange="NASDAQ")


def _df_to_bars(df: pd.DataFrame, symbol: str) -> list[Bar]:
    """将 pandas DataFrame 转为 Bar 列表"""
    bars: list[Bar] = []
    for idx, row in df.iterrows():
        try:
            ts = idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx
            bars.append(Bar(
                timestamp=ts,
                open=float(row.get("Open", row.get("open", 0))),
                high=float(row.get("High", row.get("high", 0))),
                low=float(row.get("Low", row.get("low", 0))),
                close=float(row.get("Close", row.get("close", 0))),
                volume=int(row.get("Volume", row.get("volume", 0))),
            ))
        except Exception:
            pass
    return bars
