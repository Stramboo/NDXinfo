# -*- coding: utf-8 -*-
"""BacktestEngine 与 metrics 的无网单测"""
import numpy as np
import pandas as pd
import pytest

from backtest import BacktestEngine
from backtest.metrics import MetricsCalculator
from backtest.portfolio import Portfolio
from trading.sim_rules import SimExecutionRules
from trading.strategy import create_strategy
from indicators import calc_all_indicators


def _trend(n=200, slope=0.5, noise=0.2):
    np.random.seed(1)
    prices = np.linspace(100, 100 + slope * n, n) + np.random.normal(0, noise, n)
    df = pd.DataFrame({
        "Open": prices, "High": prices + 0.5,
        "Low": prices - 0.5, "Close": prices,
        "Volume": np.ones(n) * 1e6,
    })
    df.index = pd.date_range("2024-01-01", periods=n, freq="D")
    return df


class TestPortfolio:
    def test_apply_fill_buy_then_sell(self):
        p = Portfolio(initial_cash=10000.0)
        p.apply_fill("AAPL", "BUY", 10, 100.0, commission=1.0)
        assert abs(p.cash - (10000 - 1000 - 1)) < 1e-2
        # mark_to_market：以当前价重算 market_value，并更新 equity_curve；.equity 还是 cost basis
        p.mark_to_market("2024-01-02", {"AAPL": 110.0})
        assert abs(p.equity - (10000 - 1)) < 1e-2      # cash 8999 + qty*avg_cost 1000
        # equity_curve 末点应等于 cash + 当前价 × qty = 8999 + 1100 = 10099
        assert abs(p.equity_curve[-1][1] - (10099.0)) < 1e-2
        p.apply_fill("AAPL", "SELL", 10, 110.0, commission=1.0)
        # 卖出收入 1100 - 1 = 1099 → final cash = 8999 + 1099 = 10098
        assert abs(p.cash - 10098.0) < 1e-2


class TestBacktestEngine:
    def test_trending_strategy_triggers_and_metrics(self):
        df = calc_all_indicators(_trend())
        engine = BacktestEngine(
            df_by_symbol={"AAPL": df},
            strategy=create_strategy("ma_trend"),
            initial_cash=100000.0,
            rules=SimExecutionRules(slippage_bps=5, commission_per_share=0.01, min_commission=1.0),
        )
        res = engine.run()
        assert len(res.portfolio.trades) > 0
        m = res.metrics
        assert m.total_return >= 0.0   # 上升趋势应不亏损
        assert res.start_ts is not None and res.end_ts is not None

    def test_metrics_keys_present(self):
        df = calc_all_indicators(_trend())
        engine = BacktestEngine(
            df_by_symbol={"AAPL": df},
            strategy=create_strategy("ma_trend"),
            initial_cash=100000.0,
        )
        res = engine.run()
        for key in [
            "total_return", "annual_return", "max_drawdown",
            "sharpe_ratio", "calmar_ratio", "profit_factor",
            "win_rate", "avg_win", "avg_loss",
            "trade_count", "exposure_time_pct", "turnover",
        ]:
            assert key in res.metrics.to_dict()

    def test_empty_df_raises(self):
        with pytest.raises(ValueError):
            BacktestEngine(
                df_by_symbol={}, strategy=create_strategy("ma_trend"),
                initial_cash=100000.0,
            )
