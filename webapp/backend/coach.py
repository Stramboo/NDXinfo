# -*- coding: utf-8 -*-
"""
coach.py — 个性化 AI 交易教练

不是数据展示，是替你思考。每天一句话级别的洞察 + 段位系统。
规则驱动（离线可用），可选接入 LLM。

洞察类型：
  1. 持仓体检 — 你的每只股票现状
  2. 操作建议 — 基于技术指标的建议
  3. 风险预警 — 集中度 / 回撤 / 异常
  4. 机会扫描 — 错过了什么
  5. 段位评估 — 你的交易水平
"""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))


def _import_root():
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)


# ============================================================
# 段位系统
# ============================================================

TIERS = [
    {"name": "青铜", "emoji": "🥉", "min_score": 0,
     "color": "#CD7F32", "desc": "初出茅庐，还在交学费"},
    {"name": "白银", "emoji": "🥈", "min_score": 100,
     "color": "#C0C0C0", "desc": "能找到盈利机会了"},
    {"name": "黄金", "emoji": "🥇", "min_score": 250,
     "color": "#FFD700", "desc": "稳定盈利，心态成熟"},
    {"name": "铂金", "emoji": "💎", "min_score": 500,
     "color": "#E5E4E2", "desc": "真正的专业选手"},
    {"name": "钻石", "emoji": "👑", "min_score": 1000,
     "color": "#B9F2FF", "desc": "市场里最顶端的那 5%"},
    {"name": "王者", "emoji": "🏆", "min_score": 2000,
     "color": "#FF4500", "desc": "你已经不是在交易，是在收割"},
]


def _calc_score(stats: dict) -> float:
    """根据交易数据计算段位分"""
    score = 0.0
    wr = stats.get("win_rate", 0) or 0
    total_trades = stats.get("total_trades", 0) or 0
    total_pnl = stats.get("total_pnl", 0) or 0
    avg_pnl = stats.get("avg_pnl", 0) or 0

    # 胜率贡献（最高 200 分）
    if total_trades >= 5:
        score += min(wr * 2.5, 200)

    # 交易量贡献（最高 100 分）
    score += min(total_trades * 2, 100)

    # 盈亏贡献（最高 800 分）
    score += min(total_pnl * 0.05, 500)
    score += min(max(avg_pnl, 0) * 0.1, 300)

    # 活跃度加成（最近有交易 +20%）
    if stats.get("recent_trades", 0) > 0:
        score *= 1.15

    return round(score, 1)


def get_ranking(orders: list[dict], journal: list[dict]) -> dict:
    """计算段位 — 从订单和交易日记中提取指标"""
    filled = [o for o in orders if o.get("status") == "filled"]
    wins = [o for o in filled if o.get("avg_fill_price", 0) > 0]
    losses = [o for o in filled if o.get("avg_fill_price", 0) <= 0]

    total_trades = len(filled) + len(journal)

    # 从 journal 算更精确的盈亏
    journal_pnl = sum(j.get("pnl", 0) or 0 for j in journal)
    journal_wins = sum(1 for j in journal if (j.get("pnl", 0) or 0) > 0)
    journal_losses = sum(1 for j in journal if (j.get("pnl", 0) or 0) <= 0)

    win_count = len(wins) + journal_wins
    total_with_pnl = total_trades

    win_rate = round(win_count / total_with_pnl * 100, 1) if total_with_pnl > 0 else 0
    total_pnl = journal_pnl

    avg_pnl_per_trade = round(total_pnl / total_with_pnl, 2) if total_with_pnl > 0 else 0

    # 最近活跃度
    now = time.time()
    recent_cutoff = now - 7 * 86400
    recent_trades = sum(
        1 for j in journal
        if _parse_ts(j.get("entry_date", "")) > recent_cutoff
    )

    stats = {
        "total_trades": total_with_pnl,
        "wins": win_count,
        "losses": total_with_pnl - win_count,
        "win_rate": win_rate,
        "total_pnl": round(total_pnl, 2),
        "avg_pnl": avg_pnl_per_trade,
        "recent_trades": recent_trades,
        "best_trade": _best_trade(journal),
        "worst_trade": _worst_trade(journal),
    }

    score = _calc_score(stats)

    # 找当前段位和下一段位
    current_tier = TIERS[0]
    next_tier = None
    for i, t in enumerate(TIERS):
        if score >= t["min_score"]:
            current_tier = t
            next_tier = TIERS[i + 1] if i + 1 < len(TIERS) else None

    gap = None
    if next_tier:
        gap = {"name": next_tier["name"], "emoji": next_tier["emoji"],
               "need": round(next_tier["min_score"] - score, 1),
               "pct": round(score / next_tier["min_score"] * 100, 1) if next_tier["min_score"] > 0 else 100}

    return {
        "tier": {"name": current_tier["name"], "emoji": current_tier["emoji"],
                 "color": current_tier["color"], "desc": current_tier["desc"]},
        "score": score,
        "next_tier": gap,
        "stats": stats,
    }


def _best_trade(journal: list[dict]) -> Optional[dict]:
    best = None
    for j in journal:
        pnl = j.get("pnl", 0) or 0
        if best is None or pnl > (best.get("pnl", 0) or 0):
            best = j
    return {"symbol": best.get("symbol", ""), "pnl": best.get("pnl", 0),
            "date": best.get("entry_date", "")} if best else None


def _worst_trade(journal: list[dict]) -> Optional[dict]:
    worst = None
    for j in journal:
        pnl = j.get("pnl", 0) or 0
        if worst is None or pnl < (worst.get("pnl", 0) or 0):
            worst = j
    return {"symbol": worst.get("symbol", ""), "pnl": worst.get("pnl", 0),
            "date": worst.get("entry_date", "")} if worst else None


def _parse_ts(val: Any) -> float:
    if not val:
        return 0
    try:
        if isinstance(val, (int, float)):
            return float(val)
        return datetime.fromisoformat(str(val)).timestamp()
    except Exception:
        return 0


# ============================================================
# AI 教练简报生成
# ============================================================

@dataclass
class CoachBriefing:
    headline: str          # 一句话总结
    positions: list[dict]  # 持仓分析
    warnings: list[str]    # 风险提醒
    opportunities: list[str]  # 机会提示
    ranking: dict          # 段位（嵌入）
    tone: str              # "bull" | "bear" | "neutral"
    generated_at: str


def generate_briefing(
    account: dict,
    positions: list[dict],
    ndx_status: dict,
    watchlist: list[dict] = None,
    orders: list[dict] = None,
    journal: list[dict] = None,
    signals: list[dict] = None,
    alerts: list[dict] = None,
) -> CoachBriefing:
    """生成个性化盘前简报 — 核心逻辑"""

    now_ts = datetime.now(timezone.utc)
    positions = positions or []
    orders = orders or []
    journal = journal or []
    signals = signals or []
    alerts = alerts or []

    equity = account.get("equity", 0)
    cash = account.get("cash", 0)
    daily_pnl = account.get("daily_pnl", 0)

    # ---- 1. 持仓分析 ----
    position_insights = []
    warnings = []
    opportunities = []

    if positions:
        for p in positions:
            sym = p.get("symbol", "")
            pnl_pct = p.get("unrealized_pnl_pct", 0) or 0
            pnl = p.get("unrealized_pnl", 0) or 0
            mv = p.get("market_value", 0) or 0

            # 集中度
            concentration = round(mv / equity * 100, 1) if equity > 0 else 0

            insight = {
                "symbol": sym,
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "concentration_pct": concentration,
                "status": "",
                "advice": "",
            }

            if pnl_pct >= 10:
                insight["status"] = "profit_big"
                insight["advice"] = (
                    f"{sym} 浮盈 {pnl_pct:.1f}%，来之不易。"
                    f"建议设移动止盈，保护利润。"
                )
            elif pnl_pct >= 3:
                insight["status"] = "profit_good"
                insight["advice"] = (
                    f"{sym} 走势良好，+{pnl_pct:.1f}%。"
                    f"可以继续持有，但注意不要全仓一只票。"
                )
            elif pnl_pct >= 0:
                insight["status"] = "flat"
                insight["advice"] = f"{sym} 几乎不赚不赔。考虑是否有更好的资金去处。"
            elif pnl_pct >= -5:
                insight["status"] = "loss_small"
                insight["advice"] = (
                    f"{sym} 小幅亏损 {abs(pnl_pct):.1f}%。"
                    f"可以等反弹，但设好止损线。"
                )
            else:
                insight["status"] = "loss_big"
                insight["advice"] = (
                    f"{sym} 亏损 {abs(pnl_pct):.1f}%，正处在煎熬区。"
                    f"冷静问自己：如果现在空仓，还会买它吗？"
                )

            position_insights.append(insight)

            # 风险预警
            if concentration > 30:
                warnings.append(f"⚠ 你在 {sym} 上的仓位占 {concentration:.0f}%，单票集中度过高。")
            if pnl_pct < -10:
                warnings.append(f"⚠ {sym} 浮亏超过 10%，建议重新评估是否值得继续持有。")

    # ---- 2. 大盘情绪 ----
    ndx_change = ndx_status.get("change_pct", 0) or 0
    ndx_sentiment = ndx_status.get("sentiment", "neutral")

    if ndx_change > 1:
        tone = "bull"
    elif ndx_change < -1:
        tone = "bear"
    else:
        tone = "neutral"

    # ---- 3. 机会扫描 ----
    if alerts:
        triggered_alerts = [a for a in alerts if a.get("triggered")]
        if triggered_alerts:
            opportunities.append(
                f"🔔 {len(triggered_alerts)} 个价格告警已触发，检查设置页。"
            )

    if signals:
        buy_signals = [s for s in signals if s.get("action") == "BUY"]
        if buy_signals:
            syms = ", ".join(s["symbol"] for s in buy_signals[:3])
            opportunities.append(f"💡 策略刚发了买入信号：{syms}。去操盘页看看？")

    # ---- 4. 生成标题 ----
    headline = _gen_headline(
        len(positions), daily_pnl, ndx_change, tone,
        position_insights, len(orders), len(journal),
    )

    # ---- 5. 段位 ----
    ranking = get_ranking(orders, journal)

    return CoachBriefing(
        headline=headline,
        positions=position_insights,
        warnings=warnings,
        opportunities=opportunities,
        ranking=ranking,
        tone=tone,
        generated_at=now_ts.strftime("%Y-%m-%d %H:%M UTC"),
    )


def _gen_headline(n_positions: int, daily_pnl: float, ndx_change: float,
                  tone: str, pos_insights: list, n_orders: int, n_journal: int) -> str:
    """生成今日标题——一句话灵魂总结"""

    has_positions = n_positions > 0
    has_history = n_orders + n_journal > 0

    profit_insights = [p for p in pos_insights if p["status"] in ("profit_big", "profit_good")]
    loss_insights = [p for p in pos_insights if p["status"] in ("loss_big", "loss_small")]

    if not has_history and not has_positions:
        return "👋 新手交易者，欢迎来到市场。先建仓，或者去交易页试试模拟下单。"

    if has_positions:
        if len(profit_insights) > len(loss_insights):
            best = profit_insights[0]
            return (
                f"🟢 今天你的组合在赚钱。{best['symbol']} 是最亮的星，"
                f"浮盈 {best['pnl_pct']:.1f}%。大盘 {'上涨' if ndx_change >= 0 else '震荡'}，"
                f"节奏对了。"
            )
        if len(loss_insights) > len(profit_insights):
            worst = loss_insights[0]
            return (
                f"🔴 组合承压中。{worst['symbol']} 浮亏 {abs(worst['pnl_pct']):.1f}%，"
                f"大盘 {('涨' if ndx_change >= 0 else '跌') + str(abs(ndx_change))}%。"
                f"别慌，先看哪个是逻辑错了，哪个只是波动。"
            )
        return (
            f"🟡 组合涨跌互现。{n_positions} 只持仓中，{len(profit_insights)} 只盈利"
            f"{len(loss_insights)} 只亏损。这时候比的是定力。"
        )

    if has_history:
        return (
            f"📊 空仓中。过去你有 {n_orders + n_journal} 笔交易记录。"
            f"如果今天市场 {('走强' if ndx_change >= 0 else '偏弱')}，"
            f"要不要看看自选列表？"
        )

    return f"💤 今天还没开始交易。大盘 {ndx_change:+.2f}%。"


__all__ = ["get_ranking", "generate_briefing", "CoachBriefing", "TIERS"]
