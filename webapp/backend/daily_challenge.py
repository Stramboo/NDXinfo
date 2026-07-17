# -*- coding: utf-8 -*-
"""
daily_challenge.py — 每日挑战系统 (v2.3 Phase 5)

功能:
  - 每日从挑战池随机选取挑战
  - 挑战类型：学习/练习/探索/复盘
  - 完成挑战获得 XP 奖励
"""

import random
from datetime import datetime, date
from typing import Optional

# ============================================================
# 挑战模板池
# ============================================================

CHALLENGE_POOL = [
    # 学习类
    {"id": "learn_1", "type": "learning", "title": "完成 1 课学习", "description": "打开学习页面，完成任意一课", "xp": 30, "target": 1},
    {"id": "learn_2", "type": "learning", "title": "查看 3 个术语", "description": "在术语表中查看 3 个不同的术语解释", "xp": 20, "target": 3},
    {"id": "learn_3", "type": "learning", "title": "完成阶段测验", "description": "完成当前阶段的测验并获得 80 分以上", "xp": 50, "target": 1},
    
    # 练习类
    {"id": "practice_1", "type": "practice", "title": "完成 1 笔模拟交易", "description": "在自由模拟中完成一笔买入或卖出", "xp": 40, "target": 1},
    {"id": "practice_2", "type": "practice", "title": "使用风险计算器", "description": "使用仓位计算器计算一次合理的买入数量", "xp": 25, "target": 1},
    {"id": "practice_3", "type": "practice", "title": "完成情景训练", "description": "完成任意一个情景训练并获得 60 分以上", "xp": 60, "target": 1},
    
    # 探索类
    {"id": "explore_1", "type": "explore", "title": "查看 2 个不同市场", "description": "在世界市场页面查看 2 个不同国家的市场", "xp": 20, "target": 2},
    {"id": "explore_2", "type": "explore", "title": "了解 1 家新公司", "description": "查看一家你之前不了解的公司的详细信息", "xp": 25, "target": 1},
    {"id": "explore_3", "type": "explore", "title": "对比 2 只股票", "description": "查看两只不同行业的股票并对比它们的走势", "xp": 30, "target": 2},
    
    # 复盘类
    {"id": "review_1", "type": "review", "title": "写 1 篇交易日志", "description": "为你最近的一笔交易写一篇复盘日志", "xp": 35, "target": 1},
    {"id": "review_2", "type": "review", "title": "查看复盘报告", "description": "在复盘中心查看一笔交易的详细分析", "xp": 20, "target": 1},
    {"id": "review_3", "type": "review", "title": "识别错误模式", "description": "在复盘中心找到你犯过的一个错误模式并阅读改进建议", "xp": 30, "target": 1},
]

# 按类型分组
CHALLENGES_BY_TYPE = {}
for c in CHALLENGE_POOL:
    CHALLENGES_BY_TYPE.setdefault(c["type"], []).append(c)


def get_daily_challenge(user_level: int = 1, seed: Optional[str] = None) -> dict:
    """
    获取今日挑战（基于日期和用户等级确定性选择）

    参数:
        user_level: 用户等级（影响挑战难度）
        seed: 可选随机种子（默认使用日期）

    返回:
        dict: 挑战信息
    """
    today = date.today().isoformat()
    rng = random.Random(seed or today)

    # 根据等级选择挑战池
    if user_level <= 2:
        # 新手：更多学习类挑战
        pool = CHALLENGES_BY_TYPE.get("learning", []) + CHALLENGES_BY_TYPE.get("explore", [])
    elif user_level <= 4:
        # 中级：平衡各类挑战
        pool = CHALLENGE_POOL
    else:
        # 高级：更多练习和复盘类
        pool = CHALLENGES_BY_TYPE.get("practice", []) + CHALLENGES_BY_TYPE.get("review", [])

    if not pool:
        pool = CHALLENGE_POOL

    challenge = rng.choice(pool)
    return {
        **challenge,
        "date": today,
        "completed": False,
        "progress": 0,
    }


def get_weekly_challenges(user_level: int = 1) -> list[dict]:
    """获取本周挑战列表（每天一个）"""
    challenges = []
    today = date.today()
    for i in range(7):
        day = today.fromordinal(today.toordinal() - today.weekday() + i)
        if day > today:
            break
        c = get_daily_challenge(user_level, seed=day.isoformat())
        challenges.append(c)
    return challenges


def check_challenge_completion(challenge_id: str, user_data: dict) -> bool:
    """
    检查挑战是否完成

    参数:
        challenge_id: 挑战 ID
        user_data: 用户数据 {lessons_completed, trades_today, markets_viewed, ...}

    返回:
        bool: 是否完成
    """
    challenge = next((c for c in CHALLENGE_POOL if c["id"] == challenge_id), None)
    if not challenge:
        return False

    ctype = challenge["type"]
    target = challenge["target"]

    if ctype == "learning":
        return user_data.get("lessons_completed_today", 0) >= target
    elif ctype == "practice":
        return user_data.get("trades_today", 0) >= target
    elif ctype == "explore":
        return user_data.get("markets_viewed_today", 0) >= target
    elif ctype == "review":
        return user_data.get("reviews_written_today", 0) >= target

    return False


__all__ = [
    "CHALLENGE_POOL",
    "get_daily_challenge",
    "get_weekly_challenges",
    "check_challenge_completion",
]
