# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 趋势分析模块
基于技术指标生成趋势判断、支撑/阻力位、交易信号、市场宽度、VIX情绪解读
"""

import numpy as np


def analyze_trend(df):
    """
    趋势方向判断：基于 MA 均线排列
    返回: {"direction": str, "level": str, "score": float}
    score: 1=强势下跌, 2=下跌/震荡, 2.5=震荡, 3=上涨, 4=强势上涨
    """
    if df is None or df.empty or len(df) < 2:
        return {"direction": "数据不足", "level": "unknown", "score": 2.5}

    last = df.iloc[-1]
    ma5 = last.get("MA5")
    ma10 = last.get("MA10")
    ma20 = last.get("MA20")
    ma60 = last.get("MA60")

    # 检查 NaN
    if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in [ma5, ma10, ma20]):
        return {"direction": "数据不足", "level": "unknown", "score": 2.5}

    # MA60 可能为 NaN（数据不足60天）
    has_ma60 = ma60 is not None and not (isinstance(ma60, float) and np.isnan(ma60))

    if has_ma60 and ma5 > ma10 > ma20 > ma60:
        return {"direction": "强势上涨", "level": "strong_bull", "score": 4}
    elif ma5 > ma10 > ma20:
        return {"direction": "上涨", "level": "bull", "score": 3}
    elif has_ma60 and ma5 < ma10 < ma20 < ma60:
        return {"direction": "强势下跌", "level": "strong_bear", "score": 1}
    elif ma5 < ma10 < ma20:
        return {"direction": "下跌", "level": "bear", "score": 2}
    else:
        return {"direction": "震荡", "level": "sideways", "score": 2.5}


def find_support_resistance(df, lookback=20):
    """
    识别支撑/阻力位：基于近 N 日 swing high/low
    返回: {"support1", "support2", "resistance1", "resistance2"}
    """
    if df is None or df.empty:
        return {"support1": 0, "support2": 0, "resistance1": 0, "resistance2": 0}

    recent = df.tail(lookback)
    resistance1 = round(float(recent["High"].max()), 2)
    support1 = round(float(recent["Low"].min()), 2)

    # 二级支撑阻力（第3高/第3低）
    highs = recent["High"].nlargest(min(3, len(recent)))
    lows = recent["Low"].nsmallest(min(3, len(recent)))
    resistance2 = round(float(highs.iloc[-1]), 2) if len(highs) >= 3 else resistance1
    support2 = round(float(lows.iloc[-1]), 2) if len(lows) >= 3 else support1

    return {
        "support1": support1,
        "support2": support2,
        "resistance1": resistance1,
        "resistance2": resistance2,
    }


def generate_signals(df):
    """
    生成关键价格信号
    检测: MACD金叉/死叉, RSI超买/超卖, KDJ金叉/死叉, 布林带突破, MA20穿越
    """
    if df is None or df.empty or len(df) < 2:
        return []

    last = df.iloc[-1]
    prev = df.iloc[-2]
    signals = []

    # --- MACD 金叉/死叉 ---
    if "DIF" in df.columns and "DEA" in df.columns:
        prev_dif = prev.get("DIF")
        prev_dea = prev.get("DEA")
        last_dif = last.get("DIF")
        last_dea = last.get("DEA")
        if all(v is not None and not (isinstance(v, float) and np.isnan(v))
               for v in [prev_dif, prev_dea, last_dif, last_dea]):
            if prev_dif < prev_dea and last_dif > last_dea:
                signals.append({"type": "MACD金叉", "level": "看多", "severity": "high"})
            elif prev_dif > prev_dea and last_dif < last_dea:
                signals.append({"type": "MACD死叉", "level": "看空", "severity": "high"})

    # --- RSI 超买/超卖 ---
    if "RSI" in df.columns:
        rsi_val = last.get("RSI")
        if rsi_val is not None and not (isinstance(rsi_val, float) and np.isnan(rsi_val)):
            if rsi_val > 70:
                signals.append({"type": f"RSI超买({rsi_val:.1f})", "level": "看空", "severity": "medium"})
            elif rsi_val < 30:
                signals.append({"type": f"RSI超卖({rsi_val:.1f})", "level": "看多", "severity": "medium"})

    # --- KDJ 金叉/死叉 ---
    if "K" in df.columns and "D" in df.columns:
        prev_k = prev.get("K")
        prev_d = prev.get("D")
        last_k = last.get("K")
        last_d = last.get("D")
        if all(v is not None and not (isinstance(v, float) and np.isnan(v))
               for v in [prev_k, prev_d, last_k, last_d]):
            if prev_k < prev_d and last_k > last_d:
                signals.append({"type": "KDJ金叉", "level": "看多", "severity": "medium"})
            elif prev_k > prev_d and last_k < last_d:
                signals.append({"type": "KDJ死叉", "level": "看空", "severity": "medium"})

    # --- 布林带突破 ---
    if "BOLL_UPPER" in df.columns and "BOLL_LOWER" in df.columns:
        boll_up = last.get("BOLL_UPPER")
        boll_low = last.get("BOLL_LOWER")
        close = last.get("Close")
        if all(v is not None and not (isinstance(v, float) and np.isnan(v))
               for v in [boll_up, boll_low, close]):
            if close > boll_up:
                signals.append({"type": "突破布林上轨", "level": "超买", "severity": "medium"})
            elif close < boll_low:
                signals.append({"type": "跌破布林下轨", "level": "超卖", "severity": "medium"})

    # --- 价格穿越 MA20 ---
    if "MA20" in df.columns:
        prev_close = prev.get("Close")
        prev_ma20 = prev.get("MA20")
        last_close = last.get("Close")
        last_ma20 = last.get("MA20")
        if all(v is not None and not (isinstance(v, float) and np.isnan(v))
               for v in [prev_close, prev_ma20, last_close, last_ma20]):
            if prev_close < prev_ma20 and last_close > last_ma20:
                signals.append({"type": "上穿MA20", "level": "看多", "severity": "medium"})
            elif prev_close > prev_ma20 and last_close < last_ma20:
                signals.append({"type": "下穿MA20", "level": "看空", "severity": "medium"})

    return signals


def analyze_market_breadth(stocks_data):
    """
    市场宽度分析：统计上涨/下跌股票比例
    """
    if not stocks_data:
        return {"up": 0, "down": 0, "flat": 0, "breadth_ratio": 0}

    up = sum(1 for s in stocks_data if s.get("change_pct", 0) > 0)
    down = sum(1 for s in stocks_data if s.get("change_pct", 0) < 0)
    flat = len(stocks_data) - up - down
    return {
        "up": up,
        "down": down,
        "flat": flat,
        "breadth_ratio": round(up / max(len(stocks_data), 1), 2),
    }


def vix_sentiment(vix_value):
    """
    VIX 恐慌指数情绪解读
    <15: 极度乐观, <20: 乐观, <25: 中性, <30: 恐慌, >=30: 极度恐慌
    """
    if vix_value is None or (isinstance(vix_value, float) and np.isnan(vix_value)):
        vix_value = 20

    if vix_value < 15:
        return {"level": "极度乐观", "color": "#3fb950", "desc": "市场情绪极度放松，可能存在过度乐观风险"}
    elif vix_value < 20:
        return {"level": "乐观", "color": "#3fb950", "desc": "市场情绪稳定，波动率较低"}
    elif vix_value < 25:
        return {"level": "中性", "color": "#d29922", "desc": "市场情绪偏谨慎，波动率适中"}
    elif vix_value < 30:
        return {"level": "恐慌", "color": "#f85149", "desc": "市场情绪紧张，波动率较高"}
    else:
        return {"level": "极度恐慌", "color": "#f85149", "desc": "市场情绪极度恐慌，可能出现恐慌性抛售"}


def generate_recommendation(trend, signals, rsi):
    """
    基于趋势+信号+RSI 综合生成投资建议
    """
    if not trend or "score" not in trend:
        return "数据不足"

    score = trend["score"]
    bull_signals = sum(1 for s in signals if "看多" in s.get("level", ""))
    bear_signals = sum(1 for s in signals if "看空" in s.get("level", ""))

    if score >= 3.5 and bull_signals > bear_signals:
        return "买入/加仓"
    elif score <= 2 and bear_signals > bull_signals:
        return "减持/观望"
    elif rsi is not None and not (isinstance(rsi, float) and np.isnan(rsi)):
        if rsi > 70:
            return "短期超买，谨慎"
        elif rsi < 30:
            return "短期超卖，关注"
    return "持有/观望"
