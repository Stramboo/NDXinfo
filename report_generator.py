# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 报告生成模块
使用 Jinja2 渲染 HTML 模板，将 DataFrame 转换为 ECharts JSON 数据格式
"""

import json
import os
import shutil
import math
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from config import OUTPUT_DIR, TEMPLATE_DIR, CHART_DISPLAY_DAYS, MA_PERIODS, BASE_DIR

logger = logging.getLogger(__name__)


class ReportGenerator:
    """HTML 报告生成器"""

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=False  # HTML 模板不转义，允许注入 JSON
        )

    def _safe_float(self, value):
        """安全转换浮点数，NaN/Inf 返回 None"""
        if value is None:
            return None
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return None
            return round(f, 2)
        except (ValueError, TypeError):
            return None

    def _prepare_chart_data(self, df, display_days=CHART_DISPLAY_DAYS):
        """将 DataFrame 转换为 ECharts 所需的数据格式"""
        if df is None or df.empty:
            return {
                "dates": [], "candlestick": [], "ma_lines": {f"MA{p}": [] for p in MA_PERIODS},
                "volume": [], "boll_upper": [], "boll_lower": [],
                "macd_dif": [], "macd_dea": [], "macd_hist": [],
                "rsi": [], "k": [], "d": [], "j": []
            }

        # 取最近 display_days 天数据
        recent = df.tail(display_days)

        # 日期
        dates = recent.index.strftime("%Y-%m-%d").tolist()

        # K线数据: [open, close, low, high]
        candlestick = []
        for _, row in recent.iterrows():
            candlestick.append([
                self._safe_float(row.get("Open")),
                self._safe_float(row.get("Close")),
                self._safe_float(row.get("Low")),
                self._safe_float(row.get("High")),
            ])

        # MA 线数据
        ma_lines = {}
        for p in MA_PERIODS:
            col = f"MA{p}"
            ma_lines[col] = [self._safe_float(v) for v in recent[col].tolist()] if col in recent.columns else []

        # 成交量数据（带涨跌标记）
        volume = []
        if "Volume" in recent.columns:
            closes = recent["Close"].tolist()
            opens = recent["Open"].tolist()
            volumes = recent["Volume"].tolist()
            for i in range(len(volumes)):
                vol = volumes[i]
                if hasattr(vol, 'item'):
                    vol = vol.item()
                volume.append({
                    "value": int(vol) if not math.isnan(float(vol)) else 0,
                    "isup": float(closes[i]) >= float(opens[i]) if not math.isnan(float(closes[i])) and not math.isnan(float(opens[i])) else True
                })

        # 布林带数据
        boll_upper = [self._safe_float(v) for v in recent["BOLL_UPPER"].tolist()] if "BOLL_UPPER" in recent.columns else []
        boll_lower = [self._safe_float(v) for v in recent["BOLL_LOWER"].tolist()] if "BOLL_LOWER" in recent.columns else []

        # MACD 数据
        macd_dif = [self._safe_float(v) for v in recent["DIF"].tolist()] if "DIF" in recent.columns else []
        macd_dea = [self._safe_float(v) for v in recent["DEA"].tolist()] if "DEA" in recent.columns else []
        macd_hist = [self._safe_float(v) for v in recent["MACD_HIST"].tolist()] if "MACD_HIST" in recent.columns else []

        # RSI 数据
        rsi = [self._safe_float(v) for v in recent["RSI"].tolist()] if "RSI" in recent.columns else []

        # KDJ 数据
        k = [self._safe_float(v) for v in recent["K"].tolist()] if "K" in recent.columns else []
        d = [self._safe_float(v) for v in recent["D"].tolist()] if "D" in recent.columns else []
        j = [self._safe_float(v) for v in recent["J"].tolist()] if "J" in recent.columns else []

        return {
            "dates": dates,
            "candlestick": candlestick,
            "ma_lines": ma_lines,
            "volume": volume,
            "boll_upper": boll_upper,
            "boll_lower": boll_lower,
            "macd_dif": macd_dif,
            "macd_dea": macd_dea,
            "macd_hist": macd_hist,
            "rsi": rsi,
            "k": k,
            "d": d,
            "j": j,
        }

    def generate(self, report_data):
        """
        生成完整 HTML 报告
        report_data: dict 包含所有报告数据
        返回: 输出文件路径
        """
        logger.info("开始生成 HTML 报告...")

        # 准备图表数据
        ixic_df = report_data.get("ixic_df")
        ndx_df = report_data.get("ndx_df")

        chart_json = {
            "ixic": self._prepare_chart_data(ixic_df),
            "ndx": self._prepare_chart_data(ndx_df),
            "dynamic_gainers": report_data.get("dynamic_gainers", []),
        }

        # 渲染模板
        template = self.env.get_template("report_template.html")
        html = template.render(
            report_date=datetime.now().strftime("%Y-%m-%d"),
            report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            market_summary=report_data.get("market_summary", {}),
            ixic_latest=report_data.get("ixic_latest"),
            ndx_latest=report_data.get("ndx_latest"),
            vix_data=report_data.get("vix_data", {"value": 20, "level": "中性", "color": "#d29922", "desc": "数据不可用"}),
            trend=report_data.get("trend", {"direction": "数据不足", "level": "sideways", "score": 2.5}),
            support_resistance=report_data.get("support_resistance", {"support1": 0, "support2": 0, "resistance1": 0, "resistance2": 0}),
            signals=report_data.get("signals", []),
            market_breadth=report_data.get("market_breadth", {"up": 0, "down": 0, "flat": 0, "breadth_ratio": 0}),
            stock_recommendations=report_data.get("stock_recommendations", {}),
            dynamic_gainers=report_data.get("dynamic_gainers", []),
            chart_data=json.dumps(chart_json, ensure_ascii=False, default=str),
        )

        # 保存到输出目录
        filename = f"nasdaq_report_{datetime.now().strftime('%Y-%m-%d')}.html"
        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 确保 echarts.min.js 存在于输出目录
        echarts_src = os.path.join(BASE_DIR, "echarts.min.js")
        echarts_dst = os.path.join(OUTPUT_DIR, "echarts.min.js")
        if os.path.exists(echarts_src) and echarts_src != echarts_dst:
            shutil.copy2(echarts_src, echarts_dst)
            logger.info(f"已复制 echarts.min.js 到输出目录")

        logger.info(f"HTML 报告已生成: {output_path}")
        return output_path
