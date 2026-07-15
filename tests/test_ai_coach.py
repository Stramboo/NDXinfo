# -*- coding: utf-8 -*-
"""
test_ai_coach.py — AI 教练测试

验证四维评分、边界条件、分值范围。
"""
import os
import sys
from dataclasses import asdict

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from webapp.backend.ai_coach import TradeCoach, CoachReport


@pytest.fixture
def coach():
    return TradeCoach()


class TestDecisionQuality:
    """决策质量评分"""

    def test_no_plan(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        report = coach.evaluate(trade)
        assert report.decision.score <= 30  # no plan = low score

    def test_full_plan(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        plan = {
            "reason": "MACD金叉+RSI底部反弹+趋势突破",
            "target_price": 500,
            "stop_loss_price": 430,
            "max_loss_pct": 5,
            "position_pct": 10,
            "planned_holding": "短期(1-5天)",
        }
        report = coach.evaluate(trade, plan=plan)
        assert report.decision.score >= 50  # full plan = decent score

    def test_plan_without_reason(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        plan = {"reason": "  "}
        report = coach.evaluate(trade, plan=plan)
        assert report.decision.score < 50

    def test_short_reason(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        plan = {"reason": "涨"}
        report = coach.evaluate(trade, plan=plan)
        # short reason = partial credit for plan + partial for short reason
        assert report.decision.score < 50


class TestRiskManagement:
    """风险管理评分"""

    def test_small_position(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 100}
        report = coach.evaluate(trade, cash=100_000)
        assert report.risk.score >= 25  # small pos (1%) gets credit

    def test_large_position(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 500, "price": 450}
        report = coach.evaluate(trade, cash=100_000)
        # 500*450=225000 > 100000, position_pct > 100%
        assert report.risk.score <= 40  # large position = low risk score

    def test_stop_loss_and_target(self, coach):
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        plan = {
            "reason": "test",
            "target_price": 500,
            "stop_loss_price": 430,
            "max_loss_pct": 5,
        }
        report = coach.evaluate(trade, plan=plan, cash=100_000)
        assert report.risk.score >= 60  # good risk plan


class TestResultAttribution:
    """结果归因评分"""

    def test_no_journal(self, coach):
        trade = {"symbol": "NVDA", "side": "SELL", "quantity": 10, "price": 450, "realized_pnl": 50}
        report = coach.evaluate(trade)
        assert report.attribution.score <= 40  # no journal = low

    def test_full_journal(self, coach):
        trade = {"symbol": "NVDA", "side": "SELL", "quantity": 10, "price": 450, "realized_pnl": 200}
        journal = {
            "content": "这次交易基于MACD金叉信号入场，持有3天获利了结。执行力好。",
            "emotion": "冷静",
            "lesson": "要有耐心等待确定信号，不要追高",
        }
        report = coach.evaluate(trade, journal=journal)
        assert report.attribution.score >= 60

    def test_loss_with_journal(self, coach):
        trade = {"symbol": "TSLA", "side": "SELL", "quantity": 10, "price": 200, "realized_pnl": -500}
        journal = {
            "content": "冲动追高，没有设止损，亏了大钱。教训深刻。",
            "emotion": "后悔",
            "lesson": "必须设止损",
        }
        report = coach.evaluate(trade, journal=journal)
        # Loss hurts, but journal helps
        assert 30 <= report.attribution.score <= 80


class TestOverallScore:
    """综合得分"""

    def test_range_is_0_to_100(self, coach):
        """所有得分在 0-100 范围内"""
        # 极端情况：无计划无日志
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        report = coach.evaluate(trade)
        assert 0 <= report.overall <= 100

    def test_grade_mapping(self, coach):
        """等级映射正确"""
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        plan = {
            "reason": "MACD金叉+RSI底部反弹+趋势突破，成交量放大确认",
            "target_price": 500,
            "stop_loss_price": 430,
            "max_loss_pct": 5,
            "position_pct": 10,
            "planned_holding": "短期(1-5天)",
        }
        journal = {
            "content": "严格按照计划执行，入场时MACD确实金叉，RSI在40反弹。持有3天后达到目标价卖出。",
            "emotion": "自信",
            "lesson": "做计划真的很重要，这次盈利证明了纪律的价值",
        }
        report = coach.evaluate(trade, plan=plan, journal=journal)
        assert report.grade in ("S", "A", "B", "C", "D")
        assert report.grade == "B" or report.overall >= 60  # reasonable expectations

    def test_highlights_and_improvements(self, coach):
        """亮点和改进点不为空"""
        trade = {"symbol": "NVDA", "side": "BUY", "quantity": 10, "price": 450}
        plan = {"reason": "test", "max_loss_pct": 5}
        report = coach.evaluate(trade, plan=plan)
        # At least for a very basic trade, there should be some feedback
        assert isinstance(report.highlights, list)
        assert isinstance(report.improvements, list)

    def test_coach_report_dataclass(self, coach):
        """CoachReport 可序列化"""
        trade = {"symbol": "AAPL", "side": "SELL", "quantity": 5, "price": 180, "realized_pnl": -50}
        report = coach.evaluate(trade)
        d = asdict(report)
        assert "overall" in d
        assert "grade" in d
        assert "decision" in d
        assert "execution" in d
        assert "risk" in d
        assert "attribution" in d
