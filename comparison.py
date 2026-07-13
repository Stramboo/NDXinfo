# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 历史报告对比模块
对比本期与上期报告的关键变化
"""

import logging
import numpy as np
from db import DbManager

logger = logging.getLogger(__name__)


def compare_with_previous(current_data, db_manager=None):
    """
    对比本期与上期报告的关键变化

    参数:
        current_data: 当期报告数据 dict
        db_manager: DbManager 实例

    返回: {
        "has_previous": bool,
        "previous_date": str,
        "changes": [{category, before, after, note, direction}]
    }
    """
    if db_manager is None:
        return {"has_previous": False, "changes": []}

    current_date = current_data.get("date", "")
    prev_report = db_manager.get_previous_report(current_date)

    if not prev_report:
        logger.info("无历史报告可对比")
        return {"has_previous": False, "changes": []}

    changes = []

    # 1. 趋势方向变化
    curr_trend = current_data.get("trend", {}).get("direction", "")
    prev_trend = prev_report.get("trend", "")
    if curr_trend and prev_trend and curr_trend != prev_trend:
        direction = _trend_direction(prev_trend, curr_trend)
        changes.append({
            "category": "趋势方向",
            "before": prev_trend,
            "after": curr_trend,
            "direction": direction,
            "note": f"趋势从「{prev_trend}」转为「{curr_trend}」",
        })

    # 2. VIX 等级变化
    curr_vix = current_data.get("vix", {}).get("value")
    prev_vix = prev_report.get("vix")
    if curr_vix is not None and prev_vix is not None:
        vix_diff = curr_vix - prev_vix
        if abs(vix_diff) >= 1:
            direction = "down" if vix_diff < 0 else "up"
            label = "恐慌下降" if vix_diff < 0 else "恐慌上升"
            changes.append({
                "category": "VIX恐慌指数",
                "before": f"{prev_vix:.2f}",
                "after": f"{curr_vix:.2f}",
                "direction": direction,
                "note": f"VIX {'下降' if vix_diff < 0 else '上升'} {abs(vix_diff):.2f} 点",
            })

    # 3. 市场宽度变化
    curr_breadth = current_data.get("market_breadth", {}).get("breadth_ratio")
    prev_breadth = prev_report.get("breadth_ratio")
    if curr_breadth is not None and prev_breadth is not None:
        breadth_diff = curr_breadth - prev_breadth
        if abs(breadth_diff) >= 0.1:
            direction = "up" if breadth_diff > 0 else "down"
            changes.append({
                "category": "市场宽度",
                "before": f"{prev_breadth:.0%}",
                "after": f"{curr_breadth:.0%}",
                "direction": direction,
                "note": f"多头比例{'上升' if breadth_diff > 0 else '下降'} {abs(breadth_diff):.0%}",
            })

    # 4. IXIC 收盘价变化
    curr_ixic = current_data.get("ixic_close")
    prev_ixic = prev_report.get("ixic_close")
    if curr_ixic is not None and prev_ixic is not None and prev_ixic > 0:
        price_diff = (curr_ixic / prev_ixic - 1) * 100
        if abs(price_diff) >= 0.5:
            direction = "up" if price_diff > 0 else "down"
            changes.append({
                "category": "IXIC收盘价",
                "before": f"{prev_ixic:.2f}",
                "after": f"{curr_ixic:.2f}",
                "direction": direction,
                "note": f"纳斯达克指数{'上涨' if price_diff > 0 else '下跌'} {abs(price_diff):.2f}%",
            })

    # 5. 个股推荐变化
    curr_stocks = current_data.get("stocks", [])
    for stock in curr_stocks:
        ticker = stock.get("ticker", "")
        curr_rec = stock.get("recommendation", "")
        prev_indicators = db_manager.get_previous_indicators(ticker, current_date)
        if prev_indicators:
            prev_rec = prev_indicators.get("recommendation", "")
            if curr_rec and prev_rec and curr_rec != prev_rec:
                direction = _rec_direction(prev_rec, curr_rec)
                changes.append({
                    "category": f"{ticker} 推荐",
                    "before": prev_rec,
                    "after": curr_rec,
                    "direction": direction,
                    "note": f"{ticker} 建议从「{prev_rec}」变为「{curr_rec}」",
                })

    logger.info(f"对比完成: 发现 {len(changes)} 项变化")

    return {
        "has_previous": True,
        "previous_date": prev_report.get("date", ""),
        "changes": changes,
    }


def _trend_direction(prev, curr):
    """判断趋势变化方向"""
    score_map = {
        "强势下跌": 1, "下跌": 2, "震荡": 2.5, "上涨": 3, "强势上涨": 4,
    }
    prev_score = score_map.get(prev, 2.5)
    curr_score = score_map.get(curr, 2.5)
    if curr_score > prev_score:
        return "up"
    elif curr_score < prev_score:
        return "down"
    return "flat"


def _rec_direction(prev, curr):
    """判断推荐变化方向"""
    if "买入" in curr and "买入" not in prev:
        return "up"
    if "减持" in curr and "减持" not in prev:
        return "down"
    if "持有" in curr and ("减持" in prev or "卖出" in prev):
        return "up"
    if "持有" in curr and "买入" in prev:
        return "down"
    return "flat"
