# -*- coding: utf-8 -*-
"""
achievements.py — 学习成就/徽章定义

10 枚成就徽章。解锁检测在后端每次任务完成或交易后触发。
"""

ACHIEVEMENTS = [
    {"key": "first_trade", "name": "初次交易", "desc": "完成第 1 笔沙盒交易", "icon": "🎯"},
    {"key": "first_profit", "name": "首胜", "desc": "单笔交易盈利", "icon": "💰"},
    {"key": "trade_10", "name": "交易新手", "desc": "累计完成 10 笔交易", "icon": "📈"},
    {"key": "trade_50", "name": "交易熟手", "desc": "累计完成 50 笔交易", "icon": "🔥"},
    {"key": "journal_10", "name": "复盘达人", "desc": "写满 10 篇交易日志", "icon": "📝"},
    {"key": "all_chapters", "name": "全章通关", "desc": "完成全部 8 章课程", "icon": "🎓"},
    {"key": "diversify_5", "name": "分散高手", "desc": "同时持有 5 只不同股票", "icon": "🧺"},
    {"key": "win_streak_3", "name": "三连胜", "desc": "连续 3 笔交易盈利", "icon": "🏅"},
    {"key": "profit_1000", "name": "千元户", "desc": "累计盈利超过 $1,000", "icon": "💎"},
    {"key": "streak_7d", "name": "每周打卡", "desc": "连续 7 天登录学习", "icon": "📅"},
]
