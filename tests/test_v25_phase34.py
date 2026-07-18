# -*- coding: utf-8 -*-
"""test_v25_phase34.py — v2.5 Phase 3+4 测试"""

import os
import tempfile
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.live_readiness import evaluate_readiness, READINESS_DIMENSIONS


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


class TestLiveReadiness:
    def test_evaluate_new_user(self, store):
        """新用户 readiness"""
        result = evaluate_readiness(store)
        assert "dimensions" in result
        assert "all_passed" in result
        assert "overall_score" in result
        assert "recommendation" in result
        assert not result["all_passed"]  # 新用户不该通过

    def test_4_dimensions_covered(self, store):
        result = evaluate_readiness(store)
        assert len(result["dimensions"]) == 4
        assert "knowledge" in result["dimensions"]
        assert "discipline" in result["dimensions"]
        assert "emotion" in result["dimensions"]
        assert "risk_control" in result["dimensions"]

    def test_readiness_saved(self, store):
        """评估结果保存"""
        evaluate_readiness(store)
        history = store.live_readiness_list()
        assert len(history) == 4  # 4 个维度各一条

    def test_recommendation_new_user(self, store):
        """新用户建议"""
        result = evaluate_readiness(store)
        assert "❌" in result["recommendation"] or "⚠️" in result["recommendation"]


class TestChartAnnotations:
    def test_save_and_list(self, store):
        store.chart_annotation_save("NVDA", "support", {"price": 400, "note": "支撑位"})
        annotations = store.chart_annotations_list("NVDA")
        assert len(annotations) == 1
        assert annotations[0]["symbol"] == "NVDA"
        assert annotations[0]["annotation"]["price"] == 400

    def test_list_all(self, store):
        store.chart_annotation_save("NVDA", "support", {"price": 400})
        store.chart_annotation_save("AAPL", "resistance", {"price": 180})
        all_annotations = store.chart_annotations_list()
        assert len(all_annotations) == 2


class TestProCodes:
    def test_create_and_redeem(self, store):
        store.pro_code_create("TESTCODE123", "pro")
        success = store.pro_code_redeem("TESTCODE123", "pro")
        assert success is True

    def test_redeem_invalid_code(self, store):
        success = store.pro_code_redeem("INVALID", "pro")
        assert success is False

    def test_redeem_twice_fails(self, store):
        store.pro_code_create("CODE2", "pro")
        assert store.pro_code_redeem("CODE2", "pro") is True
        assert store.pro_code_redeem("CODE2", "pro") is False  # 已激活

    def test_active_features(self, store):
        store.pro_code_create("CODE3", "advanced_analysis")
        store.pro_code_redeem("CODE3", "advanced_analysis")
        features = store.pro_features_active()
        assert "advanced_analysis" in features
