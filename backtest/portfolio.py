# -*- coding: utf-8 -*-
"""
Portfolio：回测用的虚拟账户。
维护 cash / positions / equity_curve / trades，对外提供
apply_fill() 与 mark_to_market() 两种状态变更。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Trade:
    """单笔成交记录"""
    symbol: str
    side: str                 # "BUY" | "SELL"
    quantity: int
    price: float
    commission: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    reason: str = ""


@dataclass
class Position:
    """持仓快照"""
    quantity: int = 0
    avg_cost: float = 0.0


class Portfolio:
    """
    回测虚拟账户

    用法示例:
        p = Portfolio(initial_cash=100000.0)
        p.apply_fill(symbol="AAPL", side="BUY", qty=10, price=180.0, commission=1.0)
        p.mark_to_market(timestamp="2024-01-02", price_map={"AAPL": 185.0})
        print(p.equity)
    """

    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        # equity_curve: [(ts, equity), ...]
        self.equity_curve: list[tuple[str, float]] = []

    # ---------- 状态 ----------

    @property
    def equity(self) -> float:
        return self.cash + sum(p.quantity * p.avg_cost for p in self.positions.values())

    @property
    def realized_pnl(self) -> float:
        return self.cash + sum(p.quantity * p.avg_cost for p in self.positions.values()) - self.initial_cash

    # ---------- 操作 ----------

    def apply_fill(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: float,
        commission: float = 0.0,
        timestamp: Optional[str] = None,
        reason: str = "",
    ) -> Trade:
        """登记一笔成交并更新现金 / 持仓"""
        symbol = symbol.upper()
        side = side.upper()
        cost = qty * price

        if side == "BUY":
            self.cash -= (cost + commission)
            pos = self.positions.setdefault(symbol, Position())
            new_total = pos.quantity * pos.avg_cost + cost
            pos.quantity += qty
            pos.avg_cost = new_total / pos.quantity if pos.quantity else 0.0
        else:  # SELL
            pos = self.positions.get(symbol)
            if pos and pos.quantity > 0:
                realized = (price - pos.avg_cost) * qty
            else:
                realized = 0.0
            self.cash += (cost - commission)
            if pos:
                pos.quantity -= qty
                if pos.quantity <= 0:
                    self.positions.pop(symbol, None)

        trade = Trade(
            symbol=symbol,
            side=side,
            quantity=qty,
            price=price,
            commission=commission,
            timestamp=timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            reason=reason,
        )
        self.trades.append(trade)
        return trade

    def mark_to_market(self, timestamp: str, price_map: dict[str, float]):
        """用最新价更新权益曲线（不会改变仓位 / 现金）"""
        market_value = sum(
            p.quantity * price_map.get(sym, p.avg_cost)
            for sym, p in self.positions.items()
        )
        equity = self.cash + market_value
        self.equity_curve.append((timestamp, round(equity, 2)))
