# -*- coding: utf-8 -*-
"""
growth_service.py — 成长体系编排 (v2.4 Phase 3)

功能:
  - 聚合当日行为计数（学习/交易/探索/复盘），供挑战完成检测
  - 每日签到：写 daily_checkins + 更新 streak + 发放签到 XP
  - 成就解锁检测：10 枚徽章规则评估，解锁记录到 user_prefs
"""

import logging
from datetime import date, datetime, timedelta

from webapp.backend.achievements import ACHIEVEMENTS
from webapp.backend.xp_service import award_xp

logger = logging.getLogger(__name__)

UNLOCKED_KEY = "achievements_unlocked"


def collect_today_activity(store) -> dict:
    """
    聚合当日行为计数

    返回:
        dict: {lessons_completed_today, trades_today, markets_viewed_today,
               reviews_written_today, glossary_viewed_today}
    """
    today = date.today().isoformat()
    checkin = store.checkin_get(today) or {}
    return {
        "lessons_completed_today": checkin.get("lessons_done", 0),
        "trades_today": checkin.get("trades_done", 0),
        "markets_viewed_today": checkin.get("explores_done", 0),
        "reviews_written_today": checkin.get("reviews_done", 0),
        "glossary_viewed_today": 0,
    }


def daily_checkin(store) -> dict:
    """
    每日签到（幂等）

    返回:
        dict: {date, streak, xp_awarded, is_new}
    """
    today = date.today().isoformat()
    existing = store.checkin_get(today)
    is_new = existing is None

    # 更新 streak（复用已有逻辑，幂等）
    streak = store.update_streak()

    # 创建今日打卡记录
    store.checkin_touch(today, "xp_earned", 0)

    # 签到 XP（每日一次，用日期做幂等键）
    xp_result = award_xp(store, "checkin", today, 10)

    return {
        "date": today,
        "streak": streak,
        "xp_awarded": xp_result["amount"],
        "is_new": is_new,
    }


def _get_unlocked(store) -> set:
    """获取已解锁成就集合"""
    val = store.pref_get(UNLOCKED_KEY)
    if isinstance(val, list):
        return set(val)
    return set()


def _save_unlocked(store, unlocked: set):
    """保存已解锁成就集合"""
    store.pref_set(UNLOCKED_KEY, sorted(unlocked))


def _compute_stats(store) -> dict:
    """计算成就评估所需的统计数据"""
    orders = store.sandbox_orders_list(500)
    reviews = store.review_list(500)
    journals = store.journal_list(limit=500)
    account = store.sandbox_get()
    progress = store.learning_progress_list()
    stats = store.get_learning_stats()

    # 盈利交易数（从复盘记录）
    profitable_trades = sum(1 for r in reviews if r.get("pnl", 0) > 0)
    # 累计盈利
    total_profit = sum(r.get("pnl", 0) for r in reviews if r.get("pnl", 0) > 0)
    # 连续盈利（最近 N 笔复盘）
    win_streak = 0
    for r in reviews:  # review_list 按时间倒序
        if r.get("pnl", 0) > 0:
            win_streak += 1
        else:
            break

    return {
        "total_trades": len(orders),
        "profitable_trades": profitable_trades,
        "total_profit": total_profit,
        "win_streak": win_streak,
        "journal_count": len(journals),
        "chapters_completed": sum(1 for p in progress if p.get("completed")),
        "positions_count": len(account.get("positions", [])),
        "streak_days": stats.get("streak_days", 0),
    }


# 成就规则：key → (判断函数, 奖励 XP)
_ACHIEVEMENT_RULES = {
    "first_trade":   (lambda s: s["total_trades"] >= 1, 20),
    "first_profit":  (lambda s: s["profitable_trades"] >= 1, 30),
    "trade_10":      (lambda s: s["total_trades"] >= 10, 50),
    "trade_50":      (lambda s: s["total_trades"] >= 50, 100),
    "journal_10":    (lambda s: s["journal_count"] >= 10, 50),
    "all_chapters":  (lambda s: s["chapters_completed"] >= 24, 200),
    "diversify_5":   (lambda s: s["positions_count"] >= 5, 60),
    "win_streak_3":  (lambda s: s["win_streak"] >= 3, 40),
    "profit_1000":   (lambda s: s["total_profit"] >= 1000, 80),
    "streak_7d":     (lambda s: s["streak_days"] >= 7, 70),
}


def evaluate_achievements(store) -> list[dict]:
    """
    评估全部成就，新解锁的发 XP

    返回:
        list[dict]: 新解锁的成就列表 [{key, name, desc, icon, xp}]
    """
    try:
        unlocked = _get_unlocked(store)
        stats = _compute_stats(store)
        newly = []

        for ach in ACHIEVEMENTS:
            key = ach["key"]
            if key in unlocked:
                continue
            rule = _ACHIEVEMENT_RULES.get(key)
            if not rule:
                continue
            check_fn, xp = rule
            try:
                if check_fn(stats):
                    unlocked.add(key)
                    award_xp(store, "achievement", key, xp)
                    newly.append({**ach, "xp": xp})
                    logger.info(f"成就解锁: {ach['name']} (+{xp} XP)")
            except Exception:
                continue

        if newly:
            _save_unlocked(store, unlocked)
        return newly
    except Exception as e:
        logger.warning(f"成就评估失败: {e}")
        return []


def get_achievements_with_status(store) -> list[dict]:
    """获取全部成就及解锁状态（供前端展示）"""
    unlocked = _get_unlocked(store)
    return [
        {**ach, "unlocked": ach["key"] in unlocked}
        for ach in ACHIEVEMENTS
    ]


__all__ = [
    "collect_today_activity", "daily_checkin",
    "evaluate_achievements", "get_achievements_with_status",
]
