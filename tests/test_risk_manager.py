# -*- coding: utf-8 -*-
"""RiskManager 单元测试"""
import pytest

from trading.risk_manager import RiskManager, RiskLimits, RiskCheckResult


class _FakePosition:
    def __init__(self, symbol, qty, avg_cost, market_value=None):
        self.symbol = symbol
        self.quantity = qty
        self.avg_cost = avg_cost
        self.market_value = market_value if market_value is not None else qty * avg_cost


def test_buy_passes_baseline():
    rm = RiskManager()
    res = rm.check_buy(
        symbol="AAPL", quantity=10, price=180.0,
        positions=[], account_equity=100000, account_cash=100000,
    )
    assert res.allowed is True


def test_buy_rejected_on_insufficient_cash():
    rm = RiskManager()
    res = rm.check_buy(
        symbol="AAPL", quantity=100, price=2000.0,
        positions=[], account_equity=100000, account_cash=100000,
    )
    assert res.allowed is False
    assert "资金不足" in res.reason or "上限" in res.reason or "金额" in res.reason


def test_buy_rejected_on_position_size_limit():
    rm = RiskManager(RiskLimits(max_position_pct=0.10))
    res = rm.check_buy(
        symbol="AAPL", quantity=200, price=180.0,
        positions=[], account_equity=100000, account_cash=200000,
    )
    # 200 * 180 = 36000  > 100000 * 0.10 = 10000 必被拦截
    assert res.allowed is False


def test_stop_loss_triggers():
    rm = RiskManager(RiskLimits(stop_loss_pct=-5.0))
    pos = _FakePosition("AAPL", 10, avg_cost=100.0)
    reason = rm.check_stop_conditions("AAPL", current_price=94.0, position=pos)
    assert reason is not None and "止损" in reason


def test_stop_loss_no_trigger_above():
    rm = RiskManager(RiskLimits(stop_loss_pct=-5.0))
    pos = _FakePosition("AAPL", 10, avg_cost=100.0)
    reason = rm.check_stop_conditions("AAPL", current_price=99.0, position=pos)
    assert reason is None


def test_calculate_position_size_basic():
    rm = RiskManager()
    shares = rm.calculate_position_size(
        price=100.0, account_equity=100000.0,
        risk_per_trade=0.02, stop_loss_pct=0.10,
    )
    # 风险 = 2000, 每股风险 = 10  →  200 股；上限 = equity * 0.25 / 100 = 250 股
    assert shares == 200


def test_record_trade_increments():
    rm = RiskManager()
    rm.record_trade("AAPL", pnl=-100)
    rm.record_trade("MSFT", pnl=50)
    st = rm.get_status()
    assert st["daily_trades"] == 2
    assert st["daily_pnl"] == -50
