#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告生成器
独立可运行脚本，供 SOLO Schedule 调用

用法: python nasdaq_analyzer.py
输出: nasdaq_report_YYYY-MM-DD.html
"""

import sys
import os
import math
import logging
from datetime import datetime

# 将脚本所在目录加入 path（确保模块导入）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    INDEX_TICKERS, STOCK_UNIVERSE, OUTPUT_DIR
)
from data_fetcher import DataFetcher
from indicators import calc_all_indicators
from analysis import (
    analyze_trend, find_support_resistance, generate_signals,
    analyze_market_breadth, vix_sentiment, generate_recommendation
)
from report_generator import ReportGenerator

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def extract_latest(df):
    """提取最新行情数据"""
    if df is None or df.empty or len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    try:
        close = float(last["Close"])
        prev_close = float(prev["Close"])
        change = close - prev_close
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0

        return {
            "close": round(close, 2),
            "open": round(float(last["Open"]), 2),
            "high": round(float(last["High"]), 2),
            "low": round(float(last["Low"]), 2),
            "volume": int(float(last["Volume"])),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except (KeyError, ValueError, TypeError) as e:
        logger.warning(f"提取最新行情数据失败: {e}")
        return None


def analyze_stock(fetcher, ticker, stock_df):
    """分析单只股票，返回推荐信息"""
    if stock_df is None or stock_df.empty or len(stock_df) < 2:
        logger.warning(f"{ticker} 数据不足，跳过")
        return None

    # 计算技术指标
    stock_df = calc_all_indicators(stock_df)

    # 获取基本信息
    info = fetcher.fetch_stock_info(ticker)

    # 提取行情数据
    last = stock_df.iloc[-1]
    prev = stock_df.iloc[-2]

    try:
        close = float(last["Close"])
        prev_close = float(prev["Close"])
        change_pct = ((close - prev_close) / prev_close * 100) if prev_close != 0 else 0
    except (KeyError, ValueError, TypeError):
        close = 0
        change_pct = 0

    # 趋势和信号分析
    trend = analyze_trend(stock_df)
    signals = generate_signals(stock_df)
    rsi_val = last.get("RSI")
    rsi_val = float(rsi_val) if rsi_val is not None and not (isinstance(rsi_val, float) and math.isnan(rsi_val)) else None

    # 生成投资建议
    recommendation = generate_recommendation(trend, signals, rsi_val)

    return {
        "ticker": ticker,
        "name": info.get("name", ticker),
        "price": round(close, 2),
        "change_pct": round(change_pct, 2),
        "rsi": rsi_val,
        "trend": trend["direction"],
        "signals": ", ".join(s["type"] for s in signals) if signals else "无",
        "recommendation": recommendation,
    }


def main():
    """主执行流程"""
    logger.info("=" * 60)
    logger.info("NASDAQ 每日分析报告生成开始")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    fetcher = DataFetcher()
    generator = ReportGenerator()

    try:
        # ============================================================
        # Step 1: 获取指数数据
        # ============================================================
        logger.info(">>> Step 1: 获取指数数据")
        ixic_df = fetcher.fetch_index_history(INDEX_TICKERS["ixic"])
        ndx_df = fetcher.fetch_index_history(INDEX_TICKERS["ndx"])
        vix_df = fetcher.fetch_index_history(INDEX_TICKERS["vix"])

        # ============================================================
        # Step 2: 计算指数技术指标
        # ============================================================
        logger.info(">>> Step 2: 计算指数技术指标")
        ixic_df = calc_all_indicators(ixic_df)
        ndx_df = calc_all_indicators(ndx_df)

        # ============================================================
        # Step 3: 获取个股数据（批量）
        # ============================================================
        logger.info(">>> Step 3: 批量获取个股数据")
        all_tickers = []
        for group in STOCK_UNIVERSE.values():
            all_tickers.extend(group)

        stocks_data = fetcher.fetch_stocks_batch(all_tickers)

        # ============================================================
        # Step 4: 计算个股指标并生成推荐
        # ============================================================
        logger.info(">>> Step 4: 分析个股并生成推荐")
        stock_recommendations = {}  # 按板块分组

        for sector_name, tickers in STOCK_UNIVERSE.items():
            stock_recommendations[sector_name] = []
            for ticker in tickers:
                stock_df = stocks_data.get(ticker)
                rec = analyze_stock(fetcher, ticker, stock_df)
                if rec:
                    stock_recommendations[sector_name].append(rec)

        # ============================================================
        # Step 5: 动态筛选 NASDAQ 涨幅榜
        # ============================================================
        logger.info(">>> Step 5: 筛选 NASDAQ 涨幅榜")
        dynamic_gainers = fetcher.screen_top_nasdaq_gainers()
        logger.info(f"筛选到 {len(dynamic_gainers)} 只涨幅榜股票")

        # ============================================================
        # Step 6: 市场宽度分析
        # ============================================================
        logger.info(">>> Step 6: 市场宽度分析")
        all_stocks_flat = []
        for stocks in stock_recommendations.values():
            all_stocks_flat.extend(stocks)
        breadth = analyze_market_breadth(all_stocks_flat)

        # ============================================================
        # Step 7: VIX 情绪分析
        # ============================================================
        logger.info(">>> Step 7: VIX 情绪分析")
        vix_latest = 20.0  # 默认值
        if vix_df is not None and not vix_df.empty:
            try:
                vix_latest = float(vix_df.iloc[-1]["Close"])
                if math.isnan(vix_latest):
                    vix_latest = 20.0
            except (KeyError, ValueError, IndexError):
                vix_latest = 20.0

        vix_data = {
            "value": round(vix_latest, 2),
            **vix_sentiment(vix_latest)
        }

        # ============================================================
        # Step 8: 趋势与信号分析
        # ============================================================
        logger.info(">>> Step 8: 趋势与信号分析")
        ixic_trend = analyze_trend(ixic_df)
        sr = find_support_resistance(ixic_df)
        signals = generate_signals(ixic_df)

        # ============================================================
        # Step 9: 组装报告数据
        # ============================================================
        logger.info(">>> Step 9: 组装报告数据")
        ixic_latest = extract_latest(ixic_df)
        ndx_latest = extract_latest(ndx_df)

        report_data = {
            "ixic_df": ixic_df,
            "ndx_df": ndx_df,
            "ixic_latest": ixic_latest,
            "ndx_latest": ndx_latest,
            "vix_data": vix_data,
            "trend": ixic_trend,
            "support_resistance": sr,
            "signals": signals,
            "market_breadth": breadth,
            "stock_recommendations": stock_recommendations,
            "dynamic_gainers": dynamic_gainers,
            "market_summary": {
                "ixic_close": ixic_latest["close"] if ixic_latest else 0,
                "ndx_close": ndx_latest["close"] if ndx_latest else 0,
                "vix": vix_latest,
                "breadth": breadth,
            },
        }

        # ============================================================
        # Step 10: 生成 HTML 报告
        # ============================================================
        logger.info(">>> Step 10: 生成 HTML 报告")
        output_path = generator.generate(report_data)

        logger.info("=" * 60)
        logger.info(f"报告生成成功!")
        logger.info(f"输出路径: {output_path}")
        logger.info("=" * 60)

        # 标准输出文件路径（供 Schedule 工具识别）
        print(f"\nREPORT_OUTPUT:{output_path}")

        return output_path

    except Exception as e:
        logger.error(f"报告生成失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
