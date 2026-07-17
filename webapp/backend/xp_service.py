# -*- coding: utf-8 -*-
"""
xp_service.py — 统一 XP 体系 (v2.4 Phase 1)

功能:
  - 全站唯一 XP 发放入口：写 xp_log + 更新 learning_stats + 更新 daily_checkins
  - 幂等：同一 (source, source_id) 不重复发放
  - 等级重算：单一 LEVELS 表，替代各处内联等级逻辑
"""

import logging
from datetime import date

logger = logging.getLogger(__name__)

# 等级表：(所需 XP, 等级名)
LEVELS = [
    (0, "学徒"),
    (100, "见习"),
    (300, "初级"),
    (800, "中级"),
    (2000, "高级"),
    (5000, "专家"),
    (10000, "大师"),
]


def get_level_info(total_xp: int) -> dict:
    """
    根据总 XP 计算等级信息

    返回:
        dict: {level, level_name, current_level_xp, next_level_xp, progress_pct}
    """
    level = 1
    level_name = LEVELS[0][1]
    current_xp = 0
    next_xp = LEVELS[1][0] if len(LEVELS) > 1 else 100

    for i, (xp_req, name) in enumerate(LEVELS):
        if total_xp >= xp_req:
            level = i + 1
            level_name = name
            current_xp = xp_req
            next_xp = LEVELS[i + 1][0] if i + 1 < len(LEVELS) else xp_req
        else:
            break

    # 已满级
    if level == len(LEVELS):
        progress_pct = 100
        next_xp = current_xp
    else:
        span = next_xp - current_xp
        progress_pct = round((total_xp - current_xp) / span * 100) if span > 0 else 0

    return {
        "level": level,
        "level_name": level_name,
        "total_xp": total_xp,
        "current_level_xp": current_xp,
        "next_level_xp": next_xp,
        "progress_pct": min(100, max(0, progress_pct)),
    }


def award_xp(store, source: str, source_id: str, amount: int) -> dict:
    """
    发放 XP（幂等）

    参数:
        store: UserStore 实例
        source: 来源类型 (lesson/quest/challenge/scenario/quiz/review/checkin/exam)
        source_id: 来源唯一标识（如 chapter_id、quest_id、order_id）
        amount: XP 数量

    返回:
        dict: {awarded, amount, total, level_name, level, level_up}
    """
    # 幂等检查
    if store.xp_log_exists(source, source_id):
        stats = store.get_learning_stats()
        info = get_level_info(stats.get("total_xp", 0))
        return {"awarded": False, "amount": 0, "total": info["total_xp"],
                "level": info["level"], "level_name": info["level_name"], "level_up": False}

    # 更新总 XP
    old_stats = store.get_learning_stats()
    old_total = old_stats.get("total_xp", 0)
    old_level = get_level_info(old_total)["level"]

    new_total = old_total + amount
    store.add_xp(amount)

    # 写流水
    store.xp_log_add(source, source_id, amount, new_total)

    # 更新当日打卡
    today = date.today().isoformat()
    store.checkin_touch(today, "xp_earned", amount)

    new_info = get_level_info(new_total)
    level_up = new_info["level"] > old_level

    logger.info(f"XP 发放: {source}/{source_id} +{amount} → 总计 {new_total} ({new_info['level_name']})")

    return {
        "awarded": True,
        "amount": amount,
        "total": new_total,
        "level": new_info["level"],
        "level_name": new_info["level_name"],
        "level_up": level_up,
    }


__all__ = ["LEVELS", "get_level_info", "award_xp"]
