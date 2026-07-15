# -*- coding: utf-8 -*-
"""
test_trade_plan.py — 交易计划测试

验证 trade_plan_create / trade_plan_list / 字段完整性。
"""
import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def store():
    """临时 UserStore 实例"""
    from webapp.backend.userstore import UserStore
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    st = UserStore(path)
    yield st
    if hasattr(st, '_conn') and st._conn:
        st._conn.close()
    import gc
    gc.collect()
    try:
        os.unlink(path)
    except PermissionError:
        pass


class TestTradePlanCreate:
    """交易计划创建"""

    def test_create_basic_plan(self, store):
        """创建基本交易计划"""
        plan = store.trade_plan_create(
            symbol="NVDA", direction="long",
            reason="MACD金叉 + 突破前高",
            entry_price=450.0, max_loss_pct=5, position_pct=10,
            planned_holding="短期(1-5天)",
        )
        assert plan["id"] > 0
        assert plan["symbol"] == "NVDA"
        assert plan["direction"] == "long"
        assert "created_at" in plan

    def test_create_with_minimal_fields(self, store):
        """仅必填字段创建计划"""
        plan = store.trade_plan_create(
            symbol="AAPL", direction="long",
            reason="简单测试",
        )
        assert plan["id"] > 0
        assert plan["symbol"] == "AAPL"

    def test_symbol_uppercased(self, store):
        """symbol 强制转大写"""
        plan = store.trade_plan_create(
            symbol="tsla", direction="long", reason="test",
        )
        assert plan["symbol"] == "TSLA"

    def test_multiple_plans_auto_increment(self, store):
        """多个计划 ID 递增"""
        p1 = store.trade_plan_create(symbol="NVDA", direction="long", reason="r1")
        p2 = store.trade_plan_create(symbol="AAPL", direction="short", reason="r2")
        p3 = store.trade_plan_create(symbol="TSLA", direction="long", reason="r3")
        assert p1["id"] < p2["id"] < p3["id"]


class TestTradePlanList:
    """交易计划列表"""

    def test_list_empty(self, store):
        """空列表"""
        plans = store.trade_plan_list()
        assert plans == []

    def test_list_returns_newest_first(self, store):
        """按创建时间倒序"""
        store.trade_plan_create(symbol="NVDA", direction="long", reason="first")
        store.trade_plan_create(symbol="AAPL", direction="long", reason="second")
        plans = store.trade_plan_list()
        assert len(plans) == 2
        assert plans[0]["symbol"] == "AAPL"  # newest first
        assert plans[1]["symbol"] == "NVDA"

    def test_list_respects_limit(self, store):
        """limit 参数生效"""
        for s in ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"]:
            store.trade_plan_create(symbol=s, direction="long", reason="test")
        plans = store.trade_plan_list(limit=3)
        assert len(plans) == 3

    def test_list_field_completeness(self, store):
        """返回字段完整"""
        store.trade_plan_create(
            symbol="NVDA", direction="long",
            reason="MACD金叉",
            entry_price=450.0, target_price=500.0,
            stop_loss_price=430.0, max_loss_pct=5,
            position_pct=10, planned_holding="短期(1-5天)",
        )
        plans = store.trade_plan_list()
        p = plans[0]
        assert p["symbol"] == "NVDA"
        assert p["direction"] == "long"
        assert p["reason"] == "MACD金叉"
        assert p["entry_price"] == 450.0
        assert p["target_price"] == 500.0
        assert p["stop_loss_price"] == 430.0
        assert p["max_loss_pct"] == 5
        assert p["position_pct"] == 10
        assert p["planned_holding"] == "短期(1-5天)"
        assert p["plan_type"] == "quick"
        assert "created_at" in p
