# -*- coding: utf-8 -*-
"""
回测引擎（BacktestEngine）

逐 bar 调用 StrategyBase.generate_signal()，
经 RiskManager 风控后写入 Portfolio。

与实盘共用 StrategyBase / RiskManager；SimExecutionRules 提供滑点 / 手续费。
"""

import logging
from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd

from backtest.metrics import MetricsCalculator, MetricsReport
from backtest.portfolio import Portfolio
from trading.risk_manager import RiskLimits
from trading.sim_rules import SimExecutionRules, DEFAULT_RULES
from trading.strategy import SignalAction, StrategyBase

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """回测结果汇总"""
    portfolio: Portfolio
    metrics: MetricsReport
    strategy_name: str
    symbols: list[str]
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None

    def summary(self) -> dict:
        return {
            "strategy": self.strategy_name,
            "symbols": self.symbols,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "metrics": self.metrics.to_dict(),
        }


class BacktestEngine:
    """
    回测引擎

    使用方式:
        engine = BacktestEngine(
            df_by_symbol={"AAPL": df_aapl, "NVDA": df_nvda},
            strategy=create_strategy("multi"),
            initial_cash=100000.0,
            rules=SimExecutionRules(slippage_bps=5, commission_per_share=0.01),
        )
        result = engine.run()
        print(result.metrics.sharpe_ratio)
    """

    def __init__(
        self,
        df_by_symbol: dict[str, pd.DataFrame],
        strategy: StrategyBase,
        initial_cash: float = 100000.0,
        rules: Optional[SimExecutionRules] = None,
        risk_limits: Optional[RiskLimits] = None,
        position_size_pct: float = 0.10,
        on_event: Optional[Callable] = None,
    ):
        if not df_by_symbol:
            raise ValueError("df_by_symbol 不能为空")
        self.df_by_symbol = {s.upper(): df for s, df in df_by_symbol.items()}
        self.strategy = strategy
        self.initial_cash = float(initial_cash)
        self.rules = rules or DEFAULT_RULES
        self.position_size_pct = float(position_size_pct)
        self.on_event = on_event
        # 默认风控关闭（回测场景依靠仓位 % 与回测专用规则）
        self.risk_limits = risk_limits or RiskLimits(
            max_position_pct=position_size_pct,
            max_daily_trades=9999,
            stop_loss_pct=-1.0,    # 关闭严格止损
            trailing_stop_pct=-1.0,
        )
        # 延迟导入避免循环依赖
        from trading.risk_manager import RiskManager
        self.risk = RiskManager(limits=self.risk_limits)

    @staticmethod
    def _make_positions_view(portfolio: Portfolio, price_map: dict[str, float]) -> list:
        """构造 RiskManager.check_buy 期望的 position-shape 列表。"""
        @dataclass
        class _Pos:
            symbol: str
            quantity: int
            avg_cost: float
            market_value: float

        view: list = []
        for sym, p in portfolio.positions.items():
            view.append(
                _Pos(
                    symbol=sym,
                    quantity=p.quantity,
                    avg_cost=p.avg_cost,
                    market_value=p.quantity * price_map.get(sym, p.avg_cost),
                )
            )
        return view

    # -------------- 主入口 --------------

    def run(self) -> BacktestResult:
        portfolio = Portfolio(initial_cash=self.initial_cash)
        symbols = list(self.df_by_symbol.keys())

        # 对齐时间轴：以第一个标的为主时钟
        first_df = self.df_by_symbol[symbols[0]]
        timestamps = list(first_df.index)
        start_ts = str(timestamps[0])[:10] if len(timestamps) else None
        end_ts = str(timestamps[-1])[:10] if len(timestamps) else None

        # 是否启用 ATR 止损（H 任务后续会接入）
        use_atr_stop = getattr(self.risk_limits, "use_atr_stop", False)

        # 仓位上限（每股最多花多少资金）
        max_pos_cash = self.initial_cash * self.position_size_pct

        for i, ts in enumerate(timestamps):
            price_map: dict[str, float] = {}
            for sym, df in self.df_by_symbol.items():
                if i >= len(df):
                    continue
                row = df.iloc[i]
                if "Close" in row and not pd.isna(row["Close"]):
                    price_map[sym] = float(row["Close"])

            # ---- mark to market ----
            portfolio.mark_to_market(str(ts)[:10], price_map)

            # ---- 横扫每个标的生成信号 ----
            for sym, df in self.df_by_symbol.items():
                if sym not in price_map:
                    continue
                # 用到当前 bar 的历史窗口
                window = df.iloc[: i + 1]
                if len(window) < 30:
                    continue

                try:
                    sig = self.strategy.generate_signal(sym, window)
                except Exception as e:
                    logger.debug(f"策略 {sym} 异常: {e}")
                    continue

                if not sig or sig.action == SignalAction.HOLD:
                    continue

                price = price_map[sym]

                if sig.action == SignalAction.BUY:
                    # 现金分配
                    cash_for_trade = min(
                        portfolio.cash * self.position_size_pct,
                        max_pos_cash,
                        portfolio.cash,
                    )
                    if cash_for_trade < price:
                        continue
                    qty = int(cash_for_trade // price)
                    if qty <= 0:
                        continue
                    fill_price = self.rules.compute_fill_price(price, True)
                    commission = self.rules.compute_commission(qty, fill_price)
                    # 构造 RiskManager 期望的 positions 形状（含 .symbol/.market_value）
                    pos_view = self._make_positions_view(portfolio, price_map)
                    account_equity = portfolio.cash + sum(
                        p.quantity * price_map.get(sym, p.avg_cost)
                        for sym, p in portfolio.positions.items()
                    )
                    check = self.risk.check_buy(
                        symbol=sym, quantity=qty, price=fill_price,
                        positions=pos_view,
                        account_equity=account_equity,
                        account_cash=portfolio.cash,
                    )
                    if not check.allowed:
                        continue
                    portfolio.apply_fill(
                        symbol=sym, side="BUY", qty=qty,
                        price=fill_price, commission=commission,
                        timestamp=str(ts)[:10], reason=sig.reason,
                    )
                    if self.on_event:
                        self.on_event(("BUY", sym, qty, fill_price, str(ts)[:10]))

                else:  # SELL
                    pos = portfolio.positions.get(sym)
                    if not pos or pos.quantity <= 0:
                        continue
                    qty = pos.quantity
                    fill_price = self.rules.compute_fill_price(price, False)
                    commission = self.rules.compute_commission(qty, fill_price)
                    portfolio.apply_fill(
                        symbol=sym, side="SELL", qty=qty,
                        price=fill_price, commission=commission,
                        timestamp=str(ts)[:10], reason=sig.reason,
                    )
                    if self.on_event:
                        self.on_event(("SELL", sym, qty, fill_price, str(ts)[:10]))

        # 最后一帧
        if timestamps:
            portfolio.mark_to_market(str(timestamps[-1])[:10], price_map)

        metrics = MetricsCalculator.compute(
            portfolio,
            start_ts=start_ts,
            end_ts=end_ts,
        )
        return BacktestResult(
            portfolio=portfolio,
            metrics=metrics,
            strategy_name=self.strategy.name,
            symbols=symbols,
            start_ts=start_ts,
            end_ts=end_ts,
        )
