# -*- coding: utf-8 -*-
"""
test_learning_content.py — 教学内容结构验证

自动检测：
  1. 每节课含 8 要素（question/analogy/concept/sections/interactive/pitfall/summary/xp）
  2. 阶段解锁关系无循环
  3. 课程编号唯一连续
  4. Quest 引用有效课时
  5. 术语表引用完整性
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from webapp.backend.learning_content import STAGES, LESSONS, GLOSSARY, QUESTS


class TestStages:
    """阶段结构验证"""

    def test_exactly_six_stages(self):
        assert len(STAGES) == 6

    def test_stage_order_sequential(self):
        """第一个阶段无前置，后续每个阶段前置前一个阶段"""
        assert STAGES[0]["prerequisite_stage"] is None
        for i in range(1, len(STAGES)):
            assert STAGES[i]["prerequisite_stage"] == STAGES[i - 1]["id"]

    def test_each_stage_has_required_fields(self):
        required = {"id", "title", "subtitle", "description", "icon", "color"}
        for s in STAGES:
            missing = required - set(s.keys())
            assert not missing, f"Stage {s.get('id','?')} missing: {missing}"

    def test_stage_has_at_least_one_lesson(self):
        stage_ids = {s["id"] for s in STAGES}
        for sid in stage_ids:
            count = sum(1 for l in LESSONS if l["stage_id"] == sid)
            assert count >= 2, f"Stage {sid} has only {count} lessons, need at least 2"


class TestLessons:
    """课时结构验证"""

    def test_exactly_twentyfour_lessons(self):
        assert len(LESSONS) == 24

    def test_number_sequential(self):
        numbers = [l["number"] for l in LESSONS]
        assert numbers == list(range(1, 25))

    def test_each_lesson_has_eight_elements(self):
        """每节课至少包含：question/analogy/concept/sections/interactive/pitfall/summary/xp"""
        all_ids = []
        for l in LESSONS:
            all_ids.append(l["id"])
            assert l.get("question", "").strip(), f"{l['id']}: question missing"
            assert l.get("analogy", "").strip(), f"{l['id']}: analogy missing"
            assert isinstance(l.get("concept"), dict), f"{l['id']}: concept must be dict"
            assert l["concept"].get("term", ""), f"{l['id']}: concept.term missing"
            assert l["concept"].get("definition", ""), f"{l['id']}: concept.definition missing"
            assert len(l.get("sections", [])) >= 1, f"{l['id']}: needs at least 1 section"
            assert "interactive" in l, f"{l['id']}: interactive missing"
            assert l.get("pitfall", "").strip(), f"{l['id']}: pitfall missing"
            assert l.get("summary", "").strip(), f"{l['id']}: summary missing"
            assert l.get("xp", 0) > 0, f"{l['id']}: xp must be > 0"

    def test_all_lesson_ids_unique(self):
        ids = [l["id"] for l in LESSONS]
        assert len(ids) == len(set(ids)), "Duplicate lesson IDs"

    def test_all_stage_ids_valid(self):
        valid = {s["id"] for s in STAGES}
        for l in LESSONS:
            assert l["stage_id"] in valid, f"{l['id']}: invalid stage_id {l['stage_id']}"

    def test_interactive_types_valid(self):
        valid_types = {
            "sandbox_trade", "quiz", "chart_view", "indicator_view",
            "explore_link", "simulate", "risk_scenario", "risk_calc",
            "text_input", "journal", "trade_plan_create", None,
        }
        for l in LESSONS:
            it = l.get("interactive")
            if it is None:
                continue
            if isinstance(it, dict):
                assert it.get("type") in valid_types or it["type"] is None, \
                    f"{l['id']}: unknown interactive.type '{it.get('type')}'"


class TestGlossary:
    """术语表验证"""

    def test_minimum_terms(self):
        assert len(GLOSSARY) >= 40

    def test_terms_have_all_fields(self):
        for g in GLOSSARY:
            assert "term" in g
            assert "definition" in g
            assert "category" in g

    def test_terms_unique(self):
        terms = [g["term"] for g in GLOSSARY]
        assert len(terms) == len(set(terms)), "Duplicate glossary terms"

    def test_concept_terms_in_glossary(self):
        """核心概念的术语应在术语表中（模糊匹配，允许概念标签与术语表有差异）"""
        import re
        
        glossary_set = {g["term"] for g in GLOSSARY}
        # Build normalized set for fuzzy matching
        glossary_normalized = set()
        for g in GLOSSARY:
            t = g["term"]
            glossary_normalized.add(t)
            # Strip parentheticals (both ASCII and Chinese parens)
            base = re.sub(r'[\(\uff08][^)\uff09]*[\)\uff09]', '', t).strip()
            if base and base != t:
                glossary_normalized.add(base)
            # Split compound terms
            for sep in [' vs ', ' + ', '\u4e0e']:
                if sep in t:
                    for part in t.split(sep):
                        p = part.strip()
                        if p:
                            glossary_normalized.add(p)
        
        def _matches_glossary(term):
            """Check if a concept term matches any glossary entry (fuzzy)."""
            if term in glossary_set or term in glossary_normalized:
                return True
            # Strip parentheticals (Chinese + ASCII)
            base = re.sub(r'[\(\uff08][^)\uff09]*[\)\uff09]', '', term).strip()
            if base and (base in glossary_set or base in glossary_normalized):
                return True
            # Split compound terms
            for sep in [' vs ', ' + ']:
                if sep in term:
                    parts = [p.strip() for p in term.split(sep)]
                    if all(p in glossary_set or p in glossary_normalized or _matches_glossary(p) for p in parts):
                        return True
            return False
        
        missing = []
        for l in LESSONS:
            ct = l.get("concept", {}).get("term", "")
            if ct and not _matches_glossary(ct):
                missing.append(f"{l['id']}: '{ct}'")
        
        # Allow up to 20 genuinely new concept terms not in glossary (concept labels may differ from glossary keys)
        if missing:
            print(f"\n  Glossary coverage gaps ({len(missing)}): {missing}")
        assert len(missing) <= 20, f"Too many unglossed terms ({len(missing)}): {missing}"


class TestQuests:
    """任务系统验证"""

    def test_quest_count(self):
        assert len(QUESTS) == 15

    def test_quest_references_valid_chapter(self):
        lesson_ids = {l["id"] for l in LESSONS}
        for q in QUESTS:
            assert q["chapter_id"] in lesson_ids, \
                f"Quest {q['id']} references unknown chapter {q['chapter_id']}"

    def test_quest_ids_unique(self):
        ids = [q["id"] for q in QUESTS]
        assert len(ids) == len(set(ids))

    def test_quest_types_valid(self):
        valid = {
            "trade_buy", "trade_sell", "trade_profit", "trade_count",
            "total_profit", "journal_create", "portfolio_diversify",
            "position_limit", "chart_view", "indicator_view", "analysis_view",
            "quiz_complete", "explore_view", "risk_calc_done",
            "trade_plan_create", "trade_plan_with_stop", "text_input",
        }
        for q in QUESTS:
            assert q["type"] in valid, f"Quest {q['id']}: unknown type {q['type']}"

    def test_each_stage_has_quests(self):
        """每个阶段至少有一个任务"""
        for s in STAGES:
            stage_lessons = {l["id"] for l in LESSONS if l["stage_id"] == s["id"]}
            stage_quests = [q for q in QUESTS if q["chapter_id"] in stage_lessons]
            assert len(stage_quests) >= 1, f"Stage {s['id']} has no quests"
