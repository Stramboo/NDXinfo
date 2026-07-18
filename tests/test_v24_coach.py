# -*- coding: utf-8 -*-
"""test_v24_coach.py — v2.4 Phase 6 AI 教练测试"""

import os
import tempfile
from datetime import date, timedelta
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.coach_chat import chat_with_llm, classify_question
from webapp.backend.coach_proactive import generate_proactive_messages


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


class TestChatHistory:
    def test_history_persisted(self, store):
        store.chat_save("user", "什么是止损？")
        store.chat_save("assistant", "止损是...", "concept")
        history = store.chat_history_list()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_history_order(self, store):
        for i in range(5):
            store.chat_save("user", f"消息{i}")
        history = store.chat_history_list()
        assert history[0]["message"] == "消息0"  # 正序
        assert history[-1]["message"] == "消息4"


class TestLLMFallback:
    def test_no_api_key_returns_empty(self):
        """无 API Key 时返回空串（降级规则引擎）"""
        os.environ.pop("DEEPSEEK_API_KEY", None)
        result = chat_with_llm("你好", [], {})
        assert result == ""

    def test_classify_still_works(self):
        assert classify_question("什么是PE") == "concept"
        assert classify_question("你好") == "greeting"


class TestProactiveMessages:
    def test_no_messages_for_new_user(self, store):
        """全新用户无关怀消息"""
        msgs = generate_proactive_messages(store)
        assert isinstance(msgs, list)

    def test_streak_warning(self, store):
        """昨天活跃今天未签到 → streak 警告"""
        # 先确保记录存在，再模拟 streak=3
        store.get_learning_stats()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        with store._lock:
            store._get_conn().execute(
                "UPDATE learning_stats SET streak_days=3, last_active_date=? WHERE id=1",
                (yesterday,),
            )
            store._get_conn().commit()
        store.checkin_touch(yesterday, "lessons_done", 1)
        msgs = generate_proactive_messages(store)
        types = [m["type"] for m in msgs]
        assert "streak_warning" in types

    def test_low_score_comfort(self, store):
        """复盘评分 <50 → 安慰消息"""
        store.review_save({"trade_id": "t1", "symbol": "NVDA", "side": "SELL",
                           "quantity": 10, "price": 400, "pnl": -200, "pnl_pct": -5,
                           "holding_days": 1, "score": 35, "mistakes": [], "summary": ""})
        msgs = generate_proactive_messages(store)
        types = [m["type"] for m in msgs]
        assert "review_comfort" in types

    def test_practice_reminder(self, store):
        """3 天未交易 → 练习提醒"""
        import time as _time
        old_ts = int((_time.time() - 5 * 86400) * 1000)
        store.sandbox_buy("NVDA", 10, 400, "b1", old_ts)
        msgs = generate_proactive_messages(store)
        types = [m["type"] for m in msgs]
        assert "practice_reminder" in types

    def test_max_2_messages(self, store):
        """最多返回 2 条"""
        import time as _time
        store.review_save({"trade_id": "t1", "symbol": "NVDA", "side": "SELL",
                           "quantity": 10, "price": 400, "pnl": -200, "pnl_pct": -5,
                           "holding_days": 1, "score": 30, "mistakes": [], "summary": ""})
        old_ts = int((_time.time() - 5 * 86400) * 1000)
        store.sandbox_buy("AAPL", 10, 180, "b2", old_ts)
        msgs = generate_proactive_messages(store)
        assert len(msgs) <= 2
