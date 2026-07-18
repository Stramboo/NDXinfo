# -*- coding: utf-8 -*-
"""test_v25_phase1.py — v2.5 Phase 1 教学深化测试"""

import os
import tempfile
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.scenario_questions import (
    SCENARIO_QUESTIONS, KNOWLEDGE_POINTS,
    get_chapter_scenario_question, grade_scenario_question, get_knowledge_map,
)
from webapp.backend.emotion_scenarios import (
    EMOTION_SCENARIOS, get_emotion_scenario, list_emotion_scenarios,
    get_emotion_scenario_with_answers,
)
from webapp.backend.historical_events import (
    HISTORICAL_EVENTS, get_historical_event, list_historical_events,
    evaluate_historical_replay,
)


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


# ===== Phase 1a: 情景判断题 + 错题本 =====

class TestScenarioQuestions:
    def test_all_24_chapters_have_scenario(self):
        """24 课全部有情景题"""
        chapters = {q["chapter"] for q in SCENARIO_QUESTIONS}
        for i in range(1, 25):
            assert f"ch{i:02d}" in chapters, f"ch{i:02d} 缺情景题"

    def test_knowledge_points_count(self):
        """知识点图谱覆盖"""
        assert len(KNOWLEDGE_POINTS) >= 40  # 60 个知识点

    def test_get_question_hides_answer(self):
        q = get_chapter_scenario_question("ch01")
        assert q is not None
        assert "correct" not in q
        assert "explanation" not in q

    def test_grade_multi_correct(self):
        """多选题全对"""
        q = next(qq for qq in SCENARIO_QUESTIONS if qq["id"] == "sq_ch01")
        result = grade_scenario_question("sq_ch01", {"indices": q["correct"]})
        assert result["score"] == 100
        assert result["passed"] is True

    def test_grade_multi_partial(self):
        """多选题部分对"""
        result = grade_scenario_question("sq_ch01", {"indices": [0]})  # 只选 1 个
        assert 0 < result["score"] < 100

    def test_grade_sort_correct(self):
        """排序题全对"""
        q = next(qq for qq in SCENARIO_QUESTIONS if qq["id"] == "sq_ch02")
        result = grade_scenario_question("sq_ch02", {"order": q["correct"]})
        assert result["passed"] is True

    def test_grade_branching(self):
        """分支题"""
        result = grade_scenario_question("sq_ch04", {"results": ["good", "good"]})
        assert result["score"] == 100
        assert result["passed"] is True

    def test_grade_branching_mixed(self):
        """分支题混合结果"""
        result = grade_scenario_question("sq_ch04", {"results": ["bad", "good"]})
        assert result["score"] == 50  # (0+100)/2
        assert not result["passed"]

    def test_grade_wrong_adds_to_mistake_book(self, store):
        """答错入错题本"""
        result = grade_scenario_question("sq_ch01", {"indices": [99]})  # 全错
        assert not result["passed"]
        store.mistake_add("scenario", "sq_ch01", result["knowledge_point"], result["chapter"])
        mistakes = store.mistake_list()
        assert len(mistakes) == 1
        assert mistakes[0]["question_id"] == "sq_ch01"

    def test_mistake_stats_by_kp(self, store):
        """错题按知识点统计"""
        store.mistake_add("scenario", "q1", "stop_loss", "ch18")
        store.mistake_add("scenario", "q1", "stop_loss", "ch18")  # +1
        store.mistake_add("quiz", "q2", "fomo", "ch20")
        stats = store.mistake_stats()
        assert "stop_loss" in stats
        assert stats["stop_loss"]["total_wrong"] == 2

    def test_knowledge_map_with_mastery(self, store):
        """知识点图谱附掌握度"""
        store.mistake_add("scenario", "q1", "stop_loss", "ch18")
        km = get_knowledge_map()
        # 模拟 server 的附加逻辑
        mistakes = store.mistake_stats()
        for node in km["nodes"]:
            if node["id"] in mistakes:
                node["mastery"] = max(0, 100 - mistakes[node["id"]]["total_wrong"] * 20)
            else:
                node["mastery"] = 100
        sl_node = next(n for n in km["nodes"] if n["id"] == "stop_loss")
        assert sl_node["mastery"] == 80  # 100 - 1*20


# ===== Phase 1b: 情绪训练 =====

class TestEmotionScenarios:
    def test_at_least_4_scenarios(self):
        assert len(EMOTION_SCENARIOS) >= 4

    def test_emotion_types_covered(self):
        types = {s["emotion_type"] for s in EMOTION_SCENARIOS}
        assert "fomo" in types
        assert "panic" in types
        assert "greed" in types

    def test_get_scenario_hides_result(self):
        s = get_emotion_scenario("em01")
        assert s is not None
        assert "result" not in str(s["steps"][0]["options"][0])

    def test_list_scenarios(self):
        lst = list_emotion_scenarios()
        assert len(lst) >= 4
        assert all("emotion_type" in s for s in lst)

    def test_emotion_journal_save(self, store):
        store.emotion_journal_save("em01", 7, "a", 5, 80, "测试反思")
        journals = store.emotion_journal_list()
        assert len(journals) == 1
        assert journals[0]["scenario_id"] == "em01"
        assert journals[0]["rationality_score"] == 80


# ===== Phase 1c: 历史事件回放 =====

class TestHistoricalEvents:
    def test_at_least_4_events(self):
        assert len(HISTORICAL_EVENTS) >= 4

    def test_get_event_hides_answers(self):
        e = get_historical_event("he01")
        assert e is not None
        assert "result" not in str(e["decision_points"][0]["options"][0])
        assert "historical_outcome" not in str(e["decision_points"][0]["options"][0])

    def test_list_events(self):
        lst = list_historical_events()
        assert len(lst) >= 4

    def test_evaluate_all_good(self):
        """全部选 good 选项"""
        from webapp.backend.historical_events import get_historical_event_full
        e = get_historical_event_full("he01")
        decisions = []
        for dp in e["decision_points"]:
            good_opt = next(o for o in dp["options"] if o["result"] == "good")
            decisions.append({"choice": good_opt["id"]})
        result = evaluate_historical_replay("he01", decisions)
        assert result["score"] == 100
        assert result["passed"] is True
        assert result["xp_earned"] > 0

    def test_evaluate_all_bad(self):
        """全部选 bad 选项（he01 有 bad 选项）"""
        from webapp.backend.historical_events import get_historical_event_full
        e = get_historical_event_full("he01")
        decisions = []
        for dp in e["decision_points"]:
            bad_opt = next(o for o in dp["options"] if o["result"] == "bad")
            decisions.append({"choice": bad_opt["id"]})
        result = evaluate_historical_replay("he01", decisions)
        assert result["score"] == 0
        assert not result["passed"]

    def test_history_replay_progress(self, store):
        store.history_replay_save("he01", [{"choice": "b"}], 80, True)
        progress = store.history_replay_list()
        assert len(progress) == 1
        assert progress[0]["event_id"] == "he01"
        assert progress[0]["completed"] is True
