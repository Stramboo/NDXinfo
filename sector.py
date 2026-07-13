# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 板块轮动分析模块
分析美股11大行业ETF相对强度，识别资金流向
"""

import logging
import time
import pandas as pd
import numpy as np
from config import SECTOR_ETFS, BROAD_INDEX_ETFS, HISTORY_PERIOD

logger = logging.getLogger(__name__)


def fetch_sector_data(fetcher):
    """
    获取所有行业ETF和宽基指数数据

    返回: {
        "sector_etfs": {sector_name: DataFrame},
        "broad_etfs": {ticker: DataFrame},
        "sector_analysis": [...],
        "broad_analysis": [...]
    }
    """
    logger.info("开始获取行业ETF数据...")

    sector_data = {}
    broad_data = {}

    # 获取行业ETF数据
    for sector_name, ticker in SECTOR_ETFS.items():
        try:
            df = fetcher.fetch_index_history(ticker, period="3mo")
            if df is not None and not df.empty:
                sector_data[sector_name] = {
                    "ticker": ticker,
                    "data": df,
                }
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"获取 {sector_name}({ticker}) 数据失败: {e}")
            continue

    # 获取宽基指数ETF数据
    for ticker, name in BROAD_INDEX_ETFS.items():
        try:
            df = fetcher.fetch_index_history(ticker, period="3mo")
            if df is not None and not df.empty:
                broad_data[ticker] = {
                    "name": name,
                    "data": df,
                }
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"获取 {ticker}({name}) 数据失败: {e}")
            continue

    if not sector_data:
        logger.warning("未获取到任何行业ETF数据")
        return None

    # 分析板块相对强度
    sector_analysis = _analyze_sector_strength(sector_data, broad_data.get("SPY", {}).get("data"))
    broad_analysis = _analyze_broad_indices(broad_data)

    return {
        "sector_etfs": sector_data,
        "broad_etfs": broad_data,
        "sector_analysis": sector_analysis,
        "broad_analysis": broad_analysis,
    }


def _analyze_sector_strength(sector_data, spy_df=None):
    """
    分析各行业ETF相对强度
    RS = ETF涨幅 / SPY涨幅
    按20日动量排名
    """
    results = []

    for sector_name, info in sector_data.items():
        df = info["data"]
        ticker = info["ticker"]

        if df is None or len(df) < 20:
            continue

        close = df["Close"]
        current = close.iloc[-1]

        # 各周期收益率
        ret_5d = (current / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0
        ret_20d = (current / close.iloc[-20] - 1) * 100 if len(close) >= 20 else 0
        ret_60d = (current / close.iloc[-60] - 1) * 100 if len(close) >= 60 else 0

        # 相对SPY强度
        rs_vs_spy = 0
        if spy_df is not None and len(spy_df) >= 20:
            spy_ret_20d = (spy_df["Close"].iloc[-1] / spy_df["Close"].iloc[-20] - 1) * 100
            if spy_ret_20d != 0:
                rs_vs_spy = ret_20d / spy_ret_20d

        # 动量排名分数（综合5日和20日）
        momentum_score = (ret_5d * 0.3 + ret_20d * 0.7)

        results.append({
            "sector": sector_name,
            "ticker": ticker,
            "close": round(current, 2),
            "ret_5d": round(ret_5d, 2),
            "ret_20d": round(ret_20d, 2),
            "ret_60d": round(ret_60d, 2),
            "rs_vs_spy": round(rs_vs_spy, 2),
            "momentum_score": round(momentum_score, 2),
        })

    # 按动量分数排名
    results.sort(key=lambda x: x["momentum_score"], reverse=True)

    # 添加排名和强弱标签
    for i, item in enumerate(results):
        item["rank"] = i + 1
        if i < len(results) // 3:
            item["label"] = "强势"
        elif i >= len(results) * 2 // 3:
            item["label"] = "弱势"
        else:
            item["label"] = "中性"

    return results


def _analyze_broad_indices(broad_data):
    """分析宽基指数ETF"""
    results = []

    for ticker, info in broad_data.items():
        df = info["data"]
        name = info["name"]

        if df is None or len(df) < 5:
            continue

        close = df["Close"]
        current = close.iloc[-1]
        ret_1d = (current / close.iloc[-2] - 1) * 100 if len(close) >= 2 else 0
        ret_5d = (current / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0
        ret_20d = (current / close.iloc[-20] - 1) * 100 if len(close) >= 20 else 0

        results.append({
            "ticker": ticker,
            "name": name,
            "close": round(current, 2),
            "ret_1d": round(ret_1d, 2),
            "ret_5d": round(ret_5d, 2),
            "ret_20d": round(ret_20d, 2),
        })

    return results


def get_sector_chart_data(sector_analysis):
    """生成板块强度图表数据（横向条形图）"""
    if not sector_analysis:
        return None

    chart_data = {
        "sectors": [item["sector"] for item in sector_analysis],
        "ret_20d": [item["ret_20d"] for item in sector_analysis],
        "momentum_scores": [item["momentum_score"] for item in sector_analysis],
        "labels": [item["label"] for item in sector_analysis],
    }
    return chart_data
