# -*- coding: utf-8 -*-
"""
coach_proactive.py — 教练主动关怀消息 (v2.4 Phase 6)

纯规则引擎，根据用户状态生成 1-2 条关怀消息：
  - streak 将断（昨日活跃今日未签到）
  - 复盘评分过低（安慰 + 建议）
  - 多日未交易（提醒练习）
  - 新成就解锁（祝贺）
"""

import logging
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


def generate_proactive_messages(store) -> list[dict]:
    """
    生成主动关怀消息

    返回:
        list[dict]: [{type, icon, title, message, action}]
    """
    messages = []

    try:
        stats = store.get_learning_stats()
        streak = stats.get("streak_days", 0)
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        today_checkin = store.checkin_get(today)
        yesterday_checkin = store.checkin_get(yesterday)

        # 1. streak 将断：昨天活跃但今天还没活动
        if streak >= 2 and yesterday_checkin and not today_checkin:
            messages.append({
                "type": "streak_warning",
                "icon": "🔥",
                "title": f"连续学习 {streak} 天，今天还没打卡",
                "message": "完成一课或一笔模拟交易，就能保住你的连续记录！",
                "action": {"label": "去学习", "link": "/learning"},
            })

        # 2. 复盘评分过低
        reviews = store.review_list(3)
        if reviews and reviews[0].get("score", 100) < 50:
            r = reviews[0]
            messages.append({
                "type": "review_comfort",
                "icon": "💪",
                "title": "别灰心，每笔亏损都是学费",
                "message": f"你在 {r.get('symbol')} 的交易评分 {r.get('score', 0):.0f} 分。"
                           "去复盘中心看看改进建议，下次会更好。",
                "action": {"label": "查看复盘", "link": "/me/reviews"},
            })

        # 3. 多日未交易（有学习但 3 天没练习）
        orders = store.sandbox_orders_list(1)
        if orders:
            last_ts = orders[-1].get("ts", 0)
            days_since = (int(datetime.now().timestamp() * 1000) - last_ts) / (1000 * 60 * 60 * 24)
            if days_since >= 3:
                messages.append({
                    "type": "practice_reminder",
                    "icon": "🎯",
                    "title": f"已经 {int(days_since)} 天没练习了",
                    "message": "交易技能需要持续练习。来一笔模拟交易保持手感吧！",
                    "action": {"label": "去练习", "link": "/practice/free"},
                })

        # 4. 新成就祝贺（最近解锁的成就）
        unlocked = store.pref_get("achievements_unlocked") or []
        celebrated = store.pref_get("achievements_celebrated") or []
        new_ones = [k for k in unlocked if k not in celebrated]
        if new_ones:
            from webapp.backend.achievements import ACHIEVEMENTS
            ach = next((a for a in ACHIEVEMENTS if a["key"] == new_ones[-1]), None)
            if ach:
                messages.append({
                    "type": "achievement_congrats",
                    "icon": ach["icon"],
                    "title": f"恭喜解锁「{ach['name']}」！",
                    "message": ach["desc"] + "。继续保持！",
                    "action": {"label": "查看成就", "link": "/me"},
                })
            # 标记已祝贺
            store.pref_set("achievements_celebrated", unlocked)

    except Exception as e:
        logger.warning(f"主动关怀消息生成失败: {e}")

    return messages[:2]  # 最多 2 条


__all__ = ["generate_proactive_messages"]
