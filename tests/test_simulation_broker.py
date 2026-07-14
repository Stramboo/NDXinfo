# -*- coding: utf-8 -*-
"""SimulationBroker 行为测试（含向后兼容默认 + 仿真规则）。"""
import pytest

from trading.broker import (
    SimulationBroker,
    OrderSide,
    OrderType,
    REJECT_INSUFFICIENT_CASH,
    REJECT_INSUFFICIENT_POSITION,
    REJECT_T_PLUS_ONE,
)
from trading.sim_rules import SimExecutionRules


class TestSimulationBrokerBackwardCompat:
    """默认规则下应与旧版完全一致：no slip / no fee / immediate"""

    def test_default_buy_sell_round_trip(self):
        b = SimulationBroker(initial_cash=100000.0)
        b.set_price("AAPL", 180.0)
        o = b.place_order("AAPL", 10, OrderSide.BUY, OrderType.MARKET)
        assert o.status.value == "filled"
        assert o.avg_fill_price == pytest.approx(180.0)
        assert o.commission == 0.0

        o2 = b.place_order("AAPL", 10, OrderSide.SELL, OrderType.MARKET)
        assert o2.status.value == "filled"
        assert o2.avg_fill_price == pytest.approx(180.0)

    def test_reset_clears_state(self):
        b = SimulationBroker(initial_cash=100000.0)
        b.set_price("AAPL", 100.0)
        b.place_order("AAPL", 5, OrderSide.BUY, OrderType.MARKET)
        b.reset()
        acc = b.get_account()
        assert acc.cash == pytest.approx(100000.0)
        assert b.get_positions() == []


class TestSimulationBrokerRules:
    def test_slippage_applied_on_buy(self):
        b = SimulationBroker(
            initial_cash=100000.0,
            rules=SimExecutionRules(slippage_bps=5),
        )
        b.set_price("NVDA", 500.0)
        o = b.place_order("NVDA", 10, OrderSide.BUY, OrderType.MARKET)
        assert o.avg_fill_price == pytest.approx(500.0 * 1.0005)

    def test_t_plus_one_rejects_buy_using_unsettled_cash(self):
        b = SimulationBroker(
            initial_cash=100000.0,
            rules=SimExecutionRules(t_plus_one=True),
        )
        b.set_price("AAPL", 100.0)
        b.place_order("AAPL", 800, OrderSide.BUY, OrderType.MARKET)   # 用掉 80000 资金
        # settled 现金此时 = 20000；再次买入 30000 应被拦截
        b.set_price("MSFT", 100.0)
        r = b.place_order("MSFT", 300, OrderSide.BUY, OrderType.MARKET)
        assert r.status.value == "rejected"
        assert r.rejection_code == REJECT_T_PLUS_ONE or "T+1" in r.note

    def test_insufficient_cash_rejection_code(self):
        b = SimulationBroker(initial_cash=1000.0)
        b.set_price("X", 100.0)
        r = b.place_order("X", 100, OrderSide.BUY, OrderType.MARKET)
        assert r.status.value == "rejected"
        assert r.rejection_code == REJECT_INSUFFICIENT_CASH

    def test_insufficient_position_rejection_code(self):
        b = SimulationBroker(initial_cash=100000.0)
        b.set_price("X", 100.0)
        r = b.place_order("X", 10, OrderSide.SELL, OrderType.MARKET)
        assert r.status.value == "rejected"
        assert r.rejection_code == REJECT_INSUFFICIENT_POSITION
