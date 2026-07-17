# -*- coding: utf-8 -*-
"""test_v24_foundation.py — v2.4 Phase 1 数据基座测试"""

import os
import tempfile
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.xp_service import award_xp, get_level_info, LEVELS


@pytest.fixture
def store():
    """每个测试用独立临时数据库"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    s = UserStore(db_path=path)
    yield s
    try:
        os.unlink(path)
    except OSError:
        pass


# ---------- 新表 CRUD ----------

class TestNewTables:
    def test_review_save_and_list(self, store):
        store.review_save({
            "trade_id": "t1", "symbol": "NVDA", "side": "SELL",
            "quantity": 10, "price": 500, "pnl": 200, "pnl_pct": 4.2,
            "holding_days": 5, "score": 75,
            "mistakes": [{"pattern": "panic_sell", "confidence": 0.8, "detail": "test"}],
            "summary": "测试复盘",
        })
        reviews = store.review_list()
        assert len(reviews) == 1
        assert reviews[0]["symbol"] == "NVDA"
        assert reviews[0]["score"] == 75
        assert reviews[0]["mistakes"][0]["pattern"] == "panic_sell"

    def test_review_get_by_trade(self, store):
        store.review_save({"trade_id": "t2", "symbol": "AAPL", "side": "SELL",
                           "quantity": 5, "price": 180, "pnl": -50, "pnl_pct": -2.0,
                           "holding_days": 1, "score": 40, "mistakes": [], "summary": ""})
        r = store.review_get_by_trade("t2")
        assert r is not None
        assert r["pnl"] == -50
        assert store.review_get_by_trade("nonexistent") is None

    def test_chat_history(self, store):
        store.chat_save("user", "什么是止损？")
        store.chat_save("assistant", "止损是...", "concept")
        history = store.chat_history_list()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["qtype"] == "concept"

    def test_xp_log_idempotent_check(self, store):
        assert not store.xp_log_exists("quest", "q1")
        store.xp_log_add("quest", "q1", 50, 50)
        assert store.xp_log_exists("quest", "q1")
        assert not store.xp_log_exists("quest", "q2")

    def test_checkin_touch_and_get(self, store):
        store.checkin_touch("2026-07-18", "lessons_done", 1)
        store.checkin_touch("2026-07-18", "lessons_done", 1)
        store.checkin_touch("2026-07-18", "xp_earned", 50)
        c = store.checkin_get("2026-07-18")
        assert c["lessons_done"] == 2
        assert c["xp_earned"] == 50
        assert store.checkin_get("2020-01-01") is None

    def test_checkin_invalid_field_ignored(self, store):
        store.checkin_touch("2026-07-18", "evil_field", 999)
        c = store.checkin_get("2026-07-18")
        assert c is None  # 非法字段不创建记录

    def test_sandbox_snapshots(self, store):
        store.sandbox_snapshot_add(1000, 100000, 80000, 20000)
        store.sandbox_snapshot_add(2000, 101000, 80000, 21000)
        snaps = store.sandbox_snapshots_list()
        assert len(snaps) == 2
        assert snaps[0]["ts"] == 1000  # 正序
        assert snaps[1]["equity"] == 101000

    def test_quiz_result_best(self, store):
        store.quiz_result_save("ch01", "lesson_quiz", 60, 2, 3, False)
        store.quiz_result_save("ch01", "lesson_quiz", 100, 3, 3, True)
        best = store.quiz_result_best("ch01")
        assert best["score"] == 100
        assert best["passed"] is True

    def test_quiz_results_passed(self, store):
        store.quiz_result_save("stage1", "stage_exam", 90, 9, 10, True)
        store.quiz_result_save("stage2", "stage_exam", 50, 5, 10, False)
        passed = store.quiz_results_passed("stage_exam")
        assert len(passed) == 1
        assert passed[0]["quiz_id"] == "stage1"


# ---------- XP 服务 ----------

class TestXpService:
    def test_level_boundaries(self):
        assert get_level_info(0)["level_name"] == "学徒"
        assert get_level_info(99)["level"] == 1
        assert get_level_info(100)["level_name"] == "见习"
        assert get_level_info(300)["level_name"] == "初级"
        assert get_level_info(10000)["level_name"] == "大师"
        assert get_level_info(99999)["level"] == 7

    def test_level_progress(self):
        info = get_level_info(150)  # 见习 (100-300)
        assert info["level"] == 2
        assert info["progress_pct"] == 25  # 50/200

    def test_max_level_progress(self):
        info = get_level_info(15000)
        assert info["progress_pct"] == 100

    def test_award_xp_basic(self, store):
        result = award_xp(store, "lesson", "ch01", 50)
        assert result["awarded"] is True
        assert result["total"] == 50
        assert result["level_name"] == "学徒"

    def test_award_xp_idempotent(self, store):
        r1 = award_xp(store, "lesson", "ch01", 50)
        r2 = award_xp(store, "lesson", "ch01", 50)
        assert r1["awarded"] is True
        assert r2["awarded"] is False
        assert r2["total"] == 50  # 未重复加

    def test_award_xp_level_up(self, store):
        award_xp(store, "lesson", "ch01", 80)
        result = award_xp(store, "lesson", "ch02", 50)
        assert result["total"] == 130
        assert result["level_up"] is True  # 学徒 → 见习
        assert result["level_name"] == "见习"

    def test_award_xp_updates_checkin(self, store):
        from datetime import date
        award_xp(store, "quest", "q1", 30)
        today = date.today().isoformat()
        c = store.checkin_get(today)
        assert c is not None
        assert c["xp_earned"] == 30
