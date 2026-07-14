# -*- coding: utf-8 -*-
"""
回测指标计算（MetricsCalculator）

基于 Portfolio 的 equity_curve 与 trades 计算：
- total_return / annual_return / max_drawdown / sharpe_ratio
- calmar_ratio / profit_factor
- win_rate / avg_win / avg_loss
- exposure_time_pct / turnover
"""

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from backtest.portfolio import Portfolio


@dataclass
class MetricsReport:
    """指标快照（便于序列化）"""
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    trade_count: int = 0
    exposure_time_pct: float = 0.0
    turnover: float = 0.0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d.update(d.pop("extra"))
        return d


class MetricsCalculator:
    """指标计算器。无 IO，纯函数。"""

    @staticmethod
    def compute(
        portfolio: Portfolio,
        risk_free_rate: float = 0.0,
        trading_days_per_year: int = 252,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None,
    ) -> MetricsReport:
        equity_curve = portfolio.equity_curve
        if not equity_curve:
            return MetricsReport()

        # ---- 基本收益 ----
        initial = portfolio.initial_cash
        final_equity = equity_curve[-1][1]
        total_return = (final_equity / initial - 1.0) if initial > 0 else 0.0

        # ---- 年化 ----
        n_days = len(equity_curve)
        if n_days > 1 and start_ts and end_ts:
            try:
                d0 = datetime.strptime(start_ts, "%Y-%m-%d")
                d1 = datetime.strptime(end_ts, "%Y-%m-%d")
                span_days = max(1, (d1 - d0).days)
                years = span_days / 365.25
            except Exception:
                years = max(n_days / trading_days_per_year, 1e-6)
        else:
            years = max(n_days / trading_days_per_year, 1e-6)
        annual_return = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0.0

        # ---- 最大回撤 / Sharpe ----
        peak = equity_curve[0][1]
        max_dd = 0.0
        daily_returns: list[float] = []
        prev = equity_curve[0][1]
        for _, v in equity_curve:
            if v > peak:
                peak = v
            dd = (v / peak - 1.0) if peak > 0 else 0.0
            if dd < max_dd:
                max_dd = dd
            if prev > 0:
                daily_returns.append(v / prev - 1.0)
            prev = v

        sharpe = 0.0
        if len(daily_returns) > 1:
            try:
                mean = statistics.fmean(daily_returns)
                std = statistics.pstdev(daily_returns)
                if std > 0:
                    sharpe = (mean - risk_free_rate / trading_days_per_year) / std * math.sqrt(trading_days_per_year)
            except Exception:
                sharpe = 0.0

        calmar = (annual_return / abs(max_dd)) if max_dd < 0 else 0.0

        # ---- 交易统计 ----
        round_trips: list[float] = []
        open_pos: dict[str, float] = {}        # symbol -> 累计成本
        open_qty: dict[str, int] = {}
        gross_profit = 0.0
        gross_loss = 0.0
        for t in portfolio.trades:
            sym = t.symbol
            if t.side == "BUY":
                open_pos[sym] = open_pos.get(sym, 0.0) + t.quantity * t.price + t.commission
                open_qty[sym] = open_qty.get(sym, 0) + t.quantity
            else:  # SELL
                total_cost = open_pos.get(sym, 0.0)
                qty_total = open_qty.get(sym, 0)
                if qty_total > 0:
                    avg_cost = total_cost / qty_total
                    pnl = (t.price - avg_cost) * t.quantity - t.commission
                    round_trips.append(pnl)
                    if pnl >= 0:
                        gross_profit += pnl
                    else:
                        gross_loss += pnl
                # 从累计里扣掉
                sold = min(qty_total, t.quantity)
                if sold > 0:
                    avg_cost2 = (total_cost / qty_total) if qty_total else 0.0
                    open_pos[sym] = max(0.0, total_cost - avg_cost2 * sold)
                    open_qty[sym] = max(0, qty_total - sold)

        wins = [p for p in round_trips if p > 0]
        losses = [p for p in round_trips if p < 0]
        n_trades = len(round_trips)
        win_rate = len(wins) / n_trades if n_trades else 0.0
        avg_win = statistics.fmean(wins) if wins else 0.0
        avg_loss = statistics.fmean(losses) if losses else 0.0
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else 0.0

        # ---- 暴露时间 ----
        invested_steps = 0
        for sym, pos in portfolio.positions.items():
            invested_steps += int(pos.quantity > 0)
        # 这里仅以"回测结束时仍有持仓的标的数 / 标的总数" 作为静态近似
        # 完整版可在循环里统计，模板先给出实现，循环整合在 engine.py 中
        exposure_time_pct = 0.0

        turnover = (
            sum(abs(t.quantity * t.price) for t in portfolio.trades) / 2.0 / initial
            if initial > 0 else 0.0
        )

        return MetricsReport(
            total_return=round(total_return, 4),
            annual_return=round(annual_return, 4),
            max_drawdown=round(max_dd, 4),
            sharpe_ratio=round(sharpe, 4),
            calmar_ratio=round(calmar, 4),
            profit_factor=round(profit_factor, 4),
            win_rate=round(win_rate, 4),
            avg_win=round(avg_win, 4),
            avg_loss=round(avg_loss, 4),
            trade_count=n_trades,
            exposure_time_pct=round(exposure_time_pct, 4),
            turnover=round(turnover, 4),
        )
