# -*- coding: utf-8 -*-
"""
ai_coach.py — AI 教练结构化反馈引擎

基于规则的交易四维评估：决策质量 / 执行质量 / 风险管理 / 结果归因。
可选通过 DeepSeek LLM 增强自然语言点评。

使用方式:
    coach = TradeCoach()
    report = coach.evaluate(trade_record, journal_entry=None, trade_plan=None)
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class CategoryScore:
    """单维度评分"""
    score: float       # 0-100
    max_score: float   # 满分
    label: str         # 维度名称
    breakdown: list[dict] = field(default_factory=list)  # [{item, score, note}]
    summary: str = ""  # 简短总结


@dataclass
class CoachReport:
    """完整的教练反馈报告"""
    trade_id: str = ""
    symbol: str = ""
    direction: str = ""
    evaluated_at: str = ""
    overall: float = 0.0          # 0-100 综合得分
    grade: str = ""               # S/A/B/C/D
    decision: CategoryScore = field(default_factory=lambda: CategoryScore(0, 100, "决策质量"))
    execution: CategoryScore = field(default_factory=lambda: CategoryScore(0, 100, "执行质量"))
    risk: CategoryScore = field(default_factory=lambda: CategoryScore(0, 100, "风险管理"))
    attribution: CategoryScore = field(default_factory=lambda: CategoryScore(0, 100, "结果归因"))
    highlights: list[str] = field(default_factory=list)   # 做得好的
    improvements: list[str] = field(default_factory=list)  # 需要改进的
    llm_comment: str = ""         # LLM 增强点评（可选）


# ---------------------------------------------------------------------------
# TradeCoach 规则引擎
# ---------------------------------------------------------------------------

# 各维度权重
WEIGHTS = {
    "decision": 0.30,
    "execution": 0.25,
    "risk": 0.25,
    "attribution": 0.20,
}

GRADE_THRESHOLDS = [
    (90, "S"),
    (80, "A"),
    (65, "B"),
    (50, "C"),
    (0, "D"),
]


class TradeCoach:
    """基于规则的交易教练评估器"""

    # ---- 1. 决策质量 (Decision Quality) ----

    @staticmethod
    def _score_decision(plan: Optional[dict], entry_price: Optional[float],
                        current_price: Optional[float]) -> CategoryScore:
        breakdown = []
        total = 0.0
        max_score = 100.0

        # 是否有交易计划
        if plan and plan.get("reason", "").strip():
            total += 30
            breakdown.append({"item": "交易计划", "score": 30, "note": "有明确的交易计划"})
        elif plan:
            total += 10
            breakdown.append({"item": "交易计划", "score": 10, "note": "有计划但缺少理由"})
        else:
            breakdown.append({"item": "交易计划", "score": 0, "note": "无交易计划，冲动交易风险高"})

        # 理由质量
        reason = (plan or {}).get("reason", "")
        if len(reason) >= 20:
            total += 20
            breakdown.append({"item": "理由深度", "score": 20, "note": "理由详细，经过思考"})
        elif len(reason) >= 5:
            total += 10
            breakdown.append({"item": "理由深度", "score": 10, "note": "有理由但过于简单"})
        else:
            total += 0
            breakdown.append({"item": "理由深度", "score": 0, "note": "没有明确的买入理由"})

        # 目标/止损计划
        has_target = plan and plan.get("target_price") is not None
        has_stop = plan and plan.get("stop_loss_price") is not None
        if has_target and has_stop:
            total += 20
            breakdown.append({"item": "目标管理", "score": 20, "note": "设定了目标和止损"})
        elif has_target or has_stop:
            total += 10
            breakdown.append({"item": "目标管理", "score": 10, "note": "部分设定了目标或止损"})
        else:
            breakdown.append({"item": "目标管理", "score": 0, "note": "未设定出场条件"})

        # 技术面合理性（如果有当前价格和入场价）
        if entry_price and current_price:
            pct_from_entry = abs(current_price - entry_price) / entry_price * 100
            if pct_from_entry <= 2:
                total += 15
                breakdown.append({"item": "入场时机", "score": 15, "note": "入场价接近当前市价，时机合理"})
            elif pct_from_entry <= 5:
                total += 8
                breakdown.append({"item": "入场时机", "score": 8, "note": "入场价与市价有偏差"})
            else:
                breakdown.append({"item": "入场时机", "score": 0, "note": "入场价偏离市价较多"})

        # 持仓周期规划
        holding = (plan or {}).get("planned_holding", "")
        if holding:
            total += 15
            breakdown.append({"item": "持仓规划", "score": 15, "note": f"有持仓周期规划: {holding}"})
        else:
            breakdown.append({"item": "持仓规划", "score": 0, "note": "未规划持仓周期"})

        summary = _category_summary(total, "决策")
        return CategoryScore(score=total, max_score=max_score, label="决策质量",
                             breakdown=breakdown, summary=summary)

    # ---- 2. 执行质量 (Execution Quality) ----

    @staticmethod
    def _score_execution(trade: dict) -> CategoryScore:
        breakdown = []
        total = 0.0
        max_score = 100.0

        order_type = trade.get("order_type", trade.get("type", "market"))

        # 订单类型
        if order_type == "limit":
            total += 20
            breakdown.append({"item": "订单类型", "score": 20, "note": "使用限价单，控制成本"})
        else:
            total += 10
            breakdown.append({"item": "订单类型", "score": 10, "note": "市价单，执行快但可能有滑点"})

        # 成交效率（价格是否优于计划）
        planned = trade.get("planned_price")
        executed = trade.get("price") or trade.get("avg_cost")
        if planned and executed:
            if trade.get("side") == "BUY" or trade.get("direction") == "long":
                improvement = (planned - executed) / planned * 100
            else:
                improvement = (executed - planned) / planned * 100
            if improvement >= 0.5:
                total += 30
                breakdown.append({"item": "成交效率", "score": 30, "note": f"成交价优于计划 {improvement:.1f}%"})
            elif improvement >= -1.0:
                total += 20
                breakdown.append({"item": "成交效率", "score": 20, "note": "成交价接近计划"})
            else:
                total += 5
                breakdown.append({"item": "成交效率", "score": 5, "note": f"成交价劣于计划 {abs(improvement):.1f}%，注意滑点"})
        else:
            total += 15
            breakdown.append({"item": "成交效率", "score": 15, "note": "无法对比计划价"})

        # 仓位管理执行
        pos_pct_planned = (trade.get("plan") or {}).get("position_pct")
        actual_qty = trade.get("quantity", 0)
        if pos_pct_planned and actual_qty > 0:
            total += 25
            breakdown.append({"item": "仓位执行", "score": 25, "note": "按计划执行仓位"})
        else:
            total += 15
            breakdown.append({"item": "仓位执行", "score": 15, "note": "未设定仓位计划"})

        # 多笔成交无过度交易
        trades_today = trade.get("daily_trade_count", 1)
        if trades_today <= 3:
            total += 25
            breakdown.append({"item": "交易频率", "score": 25, "note": "交易频率合理，无过度交易"})
        elif trades_today <= 6:
            total += 15
            breakdown.append({"item": "交易频率", "score": 15, "note": "交易频率偏高"})
        else:
            total += 0
            breakdown.append({"item": "交易频率", "score": 0, "note": "过度交易，容易增加成本"})

        summary = _category_summary(total, "执行")
        return CategoryScore(score=total, max_score=max_score, label="执行质量",
                             breakdown=breakdown, summary=summary)

    # ---- 3. 风险管理 (Risk Management) ----

    @staticmethod
    def _score_risk(trade: dict, plan: Optional[dict], cash: float = 100_000) -> CategoryScore:
        breakdown = []
        total = 0.0
        max_score = 100.0

        qty = trade.get("quantity", 0)
        price = trade.get("price") or trade.get("avg_cost") or 0
        position_value = qty * price
        position_pct = (position_value / cash * 100) if cash > 0 else 100

        # 仓位占比
        if position_pct <= 10:
            total += 30
            breakdown.append({"item": "仓位控制", "score": 30, "note": f"仓位 {position_pct:.1f}%，风险可控"})
        elif position_pct <= 20:
            total += 15
            breakdown.append({"item": "仓位控制", "score": 15, "note": f"仓位 {position_pct:.1f}%，偏高"})
        else:
            total += 0
            breakdown.append({"item": "仓位控制", "score": 0, "note": f"仓位 {position_pct:.1f}%，过度集中"})

        # 止损设置
        stop_loss = (plan or {}).get("stop_loss_price")
        max_loss = (plan or {}).get("max_loss_pct")
        if stop_loss and max_loss:
            total += 25
            breakdown.append({"item": "止损计划", "score": 25, "note": f"设定了止损 {max_loss}%"})
        elif max_loss:
            total += 15
            breakdown.append({"item": "止损计划", "score": 15, "note": f"设定了最大亏损 {max_loss}%"})
        else:
            total += 0
            breakdown.append({"item": "止损计划", "score": 0, "note": "未设定止损，风险敞口大"})

        # 最大损失控制
        if max_loss and max_loss <= 5:
            total += 25
            breakdown.append({"item": "亏损上限", "score": 25, "note": "最大亏损控制在5%以内，纪律性强"})
        elif max_loss and max_loss <= 10:
            total += 15
            breakdown.append({"item": "亏损上限", "score": 15, "note": f"最大亏损 {max_loss}%，可接受"})
        else:
            total += 8
            breakdown.append({"item": "亏损上限", "score": 8, "note": "未明确亏损上限"})

        # 收益风险比
        target_price = (plan or {}).get("target_price")
        if target_price and stop_loss and price:
            reward = abs(target_price - price)
            risk = abs(price - stop_loss)
            if risk > 0 and reward / risk >= 2:
                total += 20
                breakdown.append({"item": "风报比", "score": 20, "note": f"收益风险比 {reward/risk:.1f}:1，优秀"})
            elif risk > 0 and reward / risk >= 1:
                total += 10
                breakdown.append({"item": "风报比", "score": 10, "note": f"收益风险比 {reward/risk:.1f}:1，合理"})
            else:
                breakdown.append({"item": "风报比", "score": 0, "note": "未设定目标或无法计算风报比"})

        summary = _category_summary(total, "风险")
        return CategoryScore(score=total, max_score=max_score, label="风险管理",
                             breakdown=breakdown, summary=summary)

    # ---- 4. 结果归因 (Result Attribution) ----

    @staticmethod
    def _score_attribution(trade: dict, current_price: Optional[float],
                           journal: Optional[dict]) -> CategoryScore:
        breakdown = []
        total = 0.0
        max_score = 100.0

        pnl = trade.get("realized_pnl") or trade.get("unrealized_pnl") or 0
        side = trade.get("side", trade.get("direction", "long"))

        # 盈亏分析
        if pnl > 0:
            total += 30
            breakdown.append({"item": "交易结果", "score": 30, "note": f"盈利 +${pnl:.2f}"})
        elif pnl < 0:
            total += 10
            breakdown.append({"item": "交易结果", "score": 10, "note": f"亏损 ${abs(pnl):.2f}"})
        else:
            total += 15
            breakdown.append({"item": "交易结果", "score": 15, "note": "盈亏平衡"})

        # 是否有复盘日志
        if journal and journal.get("content", "").strip():
            content_len = len(journal["content"].strip())
            if content_len >= 30:
                total += 25
                breakdown.append({"item": "复盘质量", "score": 25, "note": "有详细复盘，学习态度好"})
            else:
                total += 15
                breakdown.append({"item": "复盘质量", "score": 15, "note": "有简单复盘"})
        else:
            breakdown.append({"item": "复盘质量", "score": 0, "note": "未做复盘，缺少反思"})

        # 情绪管理
        emotion = (journal or {}).get("emotion", "")
        if emotion:
            total += 15
            breakdown.append({"item": "情绪记录", "score": 15, "note": f"记录了交易情绪: {emotion}"})
        else:
            breakdown.append({"item": "情绪记录", "score": 0, "note": "未记录交易情绪"})

        # 教训总结
        lesson = (journal or {}).get("lesson", "")
        if lesson and len(lesson) >= 10:
            total += 20
            breakdown.append({"item": "教训总结", "score": 20, "note": "有具体教训总结"})
        elif lesson:
            total += 10
            breakdown.append({"item": "教训总结", "score": 10, "note": "有简单总结"})
        else:
            breakdown.append({"item": "教训总结", "score": 0, "note": "未总结教训"})

        # 是否客观归因
        if pnl != 0 and (journal and journal.get("content", "")):
            total += 10
            breakdown.append({"item": "归因客观性", "score": 10, "note": "有反思，归因较客观"})
        else:
            total += 5
            breakdown.append({"item": "归因客观性", "score": 5, "note": "缺少归因分析"})

        summary = _category_summary(total, "归因")
        return CategoryScore(score=total, max_score=max_score, label="结果归因",
                             breakdown=breakdown, summary=summary)

    # ---- 主评估入口 ----

    def evaluate(self, trade: dict, journal: Optional[dict] = None,
                 plan: Optional[dict] = None, cash: float = 100_000) -> CoachReport:
        """
        综合评估一笔交易。

        Parameters
        ----------
        trade : dict
            交易记录，至少包含 symbol, side/direction, quantity, price
        journal : dict, optional
            复盘日志 {content, emotion, lesson}
        plan : dict, optional
            交易计划 {reason, target_price, stop_loss_price, max_loss_pct, position_pct, planned_holding}
        cash : float
            账户总资金

        Returns
        -------
        CoachReport
        """
        now = datetime.now(timezone.utc).isoformat()
        symbol = trade.get("symbol", "???")
        direction = trade.get("side", trade.get("direction", "long"))
        trade_id = trade.get("id", trade.get("trade_id", symbol))

        entry_price = trade.get("price") or trade.get("avg_cost")
        current_price = trade.get("current_price") or entry_price

        decision = self._score_decision(plan, entry_price, current_price)
        execution = self._score_execution(trade)
        risk = self._score_risk(trade, plan, cash)
        attribution = self._score_attribution(trade, current_price, journal)

        w = WEIGHTS
        overall = (
            decision.score * w["decision"]
            + execution.score * w["execution"]
            + risk.score * w["risk"]
            + attribution.score * w["attribution"]
        )

        grade = next((g for t, g in GRADE_THRESHOLDS if overall >= t), "D")

        # 收集亮点和改进点
        highlights, improvements = _collect_feedback(decision, execution, risk, attribution)

        return CoachReport(
            trade_id=str(trade_id),
            symbol=symbol,
            direction=direction,
            evaluated_at=now,
            overall=round(overall, 1),
            grade=grade,
            decision=decision,
            execution=execution,
            risk=risk,
            attribution=attribution,
            highlights=highlights,
            improvements=improvements,
        )


# ---------------------------------------------------------------------------
# LLM 增强（可选，通过 DeepSeek API）
# ---------------------------------------------------------------------------

def enhance_with_llm(report: CoachReport, trade: dict) -> str:
    """
    使用 DeepSeek LLM 为教练报告添加自然语言点评。

    返回点评文本，失败时返回空字符串。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        )
    except ImportError:
        logger.warning("openai not installed, skip LLM enhancement")
        return ""

    # 构建精简上下文
    context = {
        "symbol": report.symbol,
        "direction": report.direction,
        "entry_price": trade.get("price") or trade.get("avg_cost"),
        "grade": report.grade,
        "overall": report.overall,
        "decision_score": report.decision.score,
        "execution_score": report.execution.score,
        "risk_score": report.risk.score,
        "attribution_score": report.attribution.score,
        "highlights": report.highlights[:3],
        "improvements": report.improvements[:3],
    }

    prompt = (
        '你是一位专业的股票交易教练。根据以下交易数据给出简短的点评（2-3句话中文），'
        '语气鼓励但有建设性，用「你」称呼交易者。\n\n'
        f'交易数据: {json.dumps(context, ensure_ascii=False)}\n\n'
        '请直接回复点评内容，不要加前缀或标题。'
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM enhancement failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _category_summary(score: float, prefix: str) -> str:
    if score >= 80:
        return f"{prefix}优秀 👍"
    elif score >= 60:
        return f"{prefix}良好 ✅"
    elif score >= 40:
        return f"{prefix}一般 ⚠️"
    else:
        return f"{prefix}需改进 ❌"


def _collect_feedback(decision: CategoryScore, execution: CategoryScore,
                       risk: CategoryScore, attribution: CategoryScore):
    """收集亮点和改进点"""
    highlights = []
    improvements = []

    all_items = (
        decision.breakdown + execution.breakdown
        + risk.breakdown + attribution.breakdown
    )

    for item in all_items:
        s = item["score"]
        max_s = _max_score_for_item(item["item"])
        pct = s / max_s if max_s > 0 else 0
        if pct >= 0.8 and s > 0:
            highlights.append(item["note"])
        elif pct <= 0.3:
            improvements.append(item["note"])

    # 保留最多各 3 条
    return highlights[:3], improvements[:3]


def _max_score_for_item(item_name: str) -> float:
    mapping = {
        "交易计划": 30, "理由深度": 20, "目标管理": 20,
        "入场时机": 15, "持仓规划": 15,
        "订单类型": 20, "成交效率": 30, "仓位执行": 25, "交易频率": 25,
        "仓位控制": 30, "止损计划": 25, "亏损上限": 25, "风报比": 20,
        "交易结果": 30, "复盘质量": 25, "情绪记录": 15, "教训总结": 20, "归因客观性": 10,
    }
    return mapping.get(item_name, 25)
