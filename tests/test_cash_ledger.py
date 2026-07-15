# -*- coding: utf-8 -*-
"""
test_cash_ledger.py — 交易账本测试

验证 CashLedger、订单重构、资金对账。
"""
import os
import sys
import tempfile

import pytest

# Ensure project root in path
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
    # 确保关闭数据库连接再删除文件
    if hasattr(st, '_conn') and st._conn:
        st._conn.close()
    import gc
    gc.collect()
    try:
        os.unlink(path)
    except PermissionError:
        pass  # Windows 文件锁，pytest 结束后会自动清理 temp


class TestCashLedger:
    """现金账本基本功能"""

    def test_buy_creates_ledger_entry(self, store):
        store.sandbox_buy("NVDA", 10, 480.0, "buy-001", 1000)
        ledger = store.cash_ledger_list()
        assert len(ledger) == 1
        assert ledger[0]["entry_type"] == "BUY"
        assert ledger[0]["amount"] == -4800.0  # 10 * 480

    def test_sell_creates_ledger_entry(self, store):
        store.sandbox_buy("NVDA", 10, 480.0, "buy-001", 1000)
        store.sandbox_sell("NVDA", 10, 500.0, "sell-001", 2000)
        ledger = store.cash_ledger_list()
        assert len(ledger) == 2
        assert ledger[0]["entry_type"] == "SELL"  # 最新的在前
        assert ledger[0]["amount"] == 5000.0

    def test_ledger_balance_consistent(self, store):
        """账面余额应等于 ledger 累加"""
        store.sandbox_buy("AAPL", 5, 175.0, "buy-a", 1000)
        store.sandbox_sell("AAPL", 3, 180.0, "sell-a", 2000)
        account = store.sandbox_get()
        total_change = sum(e["amount"] for e in store.cash_ledger_list())
        assert abs((100000 + total_change) - account["cash"]) < 0.01


class TestRebuildPositions:
    """从订单重建持仓"""

    def test_rebuild_matches_actual(self, store):
        store.sandbox_buy("NVDA", 10, 480.0, "b1", 1000)
        store.sandbox_buy("NVDA", 5, 490.0, "b2", 2000)
        store.sandbox_buy("AAPL", 20, 175.0, "b3", 3000)

        rebuilt = store.sandbox_rebuild_positions()
        assert "NVDA" in rebuilt
        assert rebuilt["NVDA"]["quantity"] == 15
        # 加权成本: (10*480 + 5*490) / 15 = 483.33
        assert abs(rebuilt["NVDA"]["avg_cost"] - 483.3333) < 0.01

    def test_rebuild_after_partial_sell(self, store):
        store.sandbox_buy("NVDA", 10, 480.0, "b1", 1000)
        store.sandbox_sell("NVDA", 6, 500.0, "s1", 2000)

        rebuilt = store.sandbox_rebuild_positions()
        assert rebuilt["NVDA"]["quantity"] == 4
        # 成本不变(480): sell 不影响 avg_cost 的计算方式

    def test_rebuild_after_full_sell(self, store):
        store.sandbox_buy("NVDA", 10, 480.0, "b1", 1000)
        store.sandbox_sell("NVDA", 10, 500.0, "s1", 2000)

        rebuilt = store.sandbox_rebuild_positions()
        assert "NVDA" not in rebuilt


class TestAccountState:
    """账户状态一致性"""

    def test_reset_clears_all(self, store):
        store.sandbox_buy("NVDA", 10, 480.0, "b1", 1000)
        store.sandbox_reset()
        account = store.sandbox_get()
        assert account["cash"] == 100000
        assert len(account["positions"]) == 0
        assert len(store.cash_ledger_list()) == 0

    def test_double_reset(self, store):
        """连续重置不报错"""
        store.sandbox_buy("NVDA", 10, 480.0, "b1", 1000)
        store.sandbox_reset()
        store.sandbox_reset()
        account = store.sandbox_get()
        assert account["cash"] == 100000
