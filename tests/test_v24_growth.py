# -*- coding: utf-8 -*-
"""test_v24_growth.py — v2.4 Phase 3 挑战/签到/成就闭环测试"""

import os
import tempfile
from datetime import date, datetime, timedelta
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.growth_service import (
    collect_today_activity, daily_checkin,
    evaluate_achievements, get_achievements_with_status,
)
from webapp.backend.daily_challenge import check_challenge_completion


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    s = UserStore(db_path=path)
    yield s
    try:
        os.unlink(path)
    except OSError:
        pass


class TestDailyCheckin:
    def test_first_checkin(self, store):
        result = daily_checkin(store)
        assert result["streak"] == 1
        assert result["xp_awarded"] == 10
        assert result["is_new"] is True

    def test_checkin_idempotent_xp(self, store):
        r1 = daily_checkin(store)
        r2 = daily_checkin(store)
        assert r1["xp_awarded"] == 10
        assert r2["xp_awarded"] == 0  # 同日不重复发 XP
        stats = store.get_learning_stats()
        assert stats["total_xp"] == 10

    def test_checkin_creates_record(self, store):
        daily_checkin(store)
        today = date.today().isoformat()
        c = store.checkin_get(today)
        assert c is not None


class TestCollectActivity:
    def test_empty_activity(self, store):
        activity = collect_today_activity(store)
        assert activity["lessons_completed_today"] == 0
        assert activity["trades_today"] == 0

    def test_activity_aggregation(self, store):
        today = date.today().isoformat()
        store.checkin_touch(today, "lessons_done", 2)
        store.checkin_touch(today, "trades_done", 3)
        activity = collect_today_activity(store)
        assert activity["lessons_completed_today"] == 2
        assert activity["trades_today"] == 3


class TestChallengeCompletion:
    def test_learning_challenge(self):
        assert check_challenge_completion("learn_1", {"lessons_completed_today": 1}) is True
        assert check_challenge_completion("learn_1", {"lessons_completed_today": 0}) is False

    def test_practice_challenge(self):
        assert check_challenge_completion("practice_1", {"trades_today": 1}) is True
        assert check_challenge_completion("practice_1", {"trades_today": 0}) is False

    def test_explore_challenge(self):
        assert check_challenge_completion("explore_1", {"markets_viewed_today": 2}) is True
        assert check_challenge_completion("explore_1", {"markets_viewed_today": 1}) is False

    def test_unknown_challenge(self):
        assert check_challenge_completion("nonexistent", {}) is False


class TestAchievements:
    def test_first_trade_unlock(self, store):
        store.sandbox_buy("NVDA", 10, 400, "b1", 1000)
        newly = evaluate_achievements(store)
        keys = [a["key"] for a in newly]
        assert "first_trade" in keys

    def test_no_duplicate_unlock(self, store):
        store.sandbox_buy("NVDA", 10, 400, "b1", 1000)
        evaluate_achievements(store)
        newly2 = evaluate_achievements(store)
        assert len(newly2) == 0  # 不重复解锁

    def test_first_profit_unlock(self, store):
        store.sandbox_buy("NVDA", 10, 400, "b1", 1000)
        store.sandbox_sell("NVDA", 10, 440, "s1", 2000)
        # 手动写一条盈利复盘
        store.review_save({"trade_id": "s1", "symbol": "NVDA", "side": "SELL",
                           "quantity": 10, "price": 440, "pnl": 400, "pnl_pct": 10,
                           "holding_days": 1, "score": 80, "mistakes": [], "summary": ""})
        newly = evaluate_achievements(store)
        keys = [a["key"] for a in newly]
        assert "first_profit" in keys

    def test_achievement_xp_awarded(self, store):
        store.sandbox_buy("NVDA", 10, 400, "b1", 1000)
        evaluate_achievements(store)
        stats = store.get_learning_stats()
        assert stats["total_xp"] >= 20  # first_trade 奖励 20 XP

    def test_get_achievements_with_status(self, store):
        store.sandbox_buy("NVDA", 10, 400, "b1", 1000)
        evaluate_achievements(store)
        all_ach = get_achievements_with_status(store)
        assert len(all_ach) == 10
        first_trade = next(a for a in all_ach if a["key"] == "first_trade")
        assert first_trade["unlocked"] is True
        locked = next(a for a in all_ach if a["key"] == "trade_50")
        assert locked["unlocked"] is False

    def test_trade_10_unlock(self, store):
        for i in range(10):
            store.sandbox_buy("NVDA", 1, 400, f"b{i}", 1000 + i)
        newly = evaluate_achievements(store)
        keys = [a["key"] for a in newly]
        assert "trade_10" in keys
