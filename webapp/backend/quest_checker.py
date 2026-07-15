# -*- coding: utf-8 -*-
"""
quest_checker.py — 学习任务完成条件检测引擎

集中管理所有任务类型的完成条件判断逻辑。
支持前端通过 /api/learning/quests/check 传上下文数据来检测。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_quest(quest: dict, context: dict) -> bool:
    """根据任务类型和上下文数据判断是否完成

    Args:
        quest: 任务定义（含 type, params）
        context: 前端传的当前状态数据，格式因 type 而异

    Returns:
        True 表示任务已完成
    """
    qtype = quest.get("type", "")
    params = quest.get("params", {})

    try:
        if qtype == "trade_buy":
            return context.get("buy_count", 0) >= params.get("min_quantity", 1)
        elif qtype == "trade_sell":
            return context.get("sell_count", 0) >= params.get("min_quantity", 1)
        elif qtype == "trade_profit":
            return context.get("realized_pnl", 0) >= params.get("min_pnl", 0.01)
        elif qtype == "trade_count":
            return context.get("trade_count", 0) >= params.get("min_count", 1)
        elif qtype == "total_profit":
            return context.get("total_pnl", 0) >= params.get("min_total_pnl", 0)
        elif qtype == "journal_create":
            return context.get("journal_count", 0) >= 1
        elif qtype == "portfolio_diversify":
            return context.get("unique_positions", 0) >= params.get("min_symbols", 1)
        elif qtype == "position_limit":
            max_pct = params.get("max_pct", 30)
            positions = context.get("positions", [])
            total_equity = context.get("total_equity", 100000)
            if total_equity <= 0:
                return False
            for pos in positions:
                market_val = pos.get("market_value", 0)
                pct = (market_val / total_equity) * 100
                if pct > max_pct:
                    return False
            return len(positions) > 0  # 至少有一只持仓才算有效
        elif qtype in ("chart_view", "indicator_view", "analysis_view", "explore_view"):
            # 这些类型通过前端传 completed=true 来标记
            return context.get("completed", False)
        elif qtype in ("quiz_complete", "risk_calc_done", "trade_plan_create", "trade_plan_with_stop"):
            # 也通过前端传 completed=true 来标记
            return context.get("completed", False)
        else:
            logger.warning(f"未知任务类型: {qtype}")
            return False
    except Exception as e:
        logger.warning(f"任务检测异常 ({qtype}): {e}")
        return False
