# -*- coding: utf-8 -*-
"""
回测框架（package）

模块清单:
    portfolio   虚拟账户与权益曲线
    metrics     绩效指标（Sharpe / MaxDD / Calmar / Profit Factor / Win Rate ...）
    engine      逐 bar 回测循环
    reporter    JSON / HTML / CSV 输出
    cli         python -m backtest.cli ...
    legacy      旧 backtest.py 的 compat 入口
"""

from backtest.engine import BacktestEngine, BacktestResult   # noqa: F401
from backtest.portfolio import Portfolio, Trade              # noqa: F401
from backtest.metrics import MetricsCalculator, MetricsReport  # noqa: F401
from backtest.reporter import ReportWriter                   # noqa: F401

__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "Portfolio",
    "Trade",
    "MetricsCalculator",
    "MetricsReport",
    "ReportWriter",
]
