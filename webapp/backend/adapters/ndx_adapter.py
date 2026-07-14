# -*- coding: utf-8 -*-
"""
ndx_adapter.py — 把 nasdaq_analyzer / data_fetcher 包成"今日 NDX 状态"接口

目标：让 webapp 后端能用一次函数调用，
      直接拿到今天 NDX 的"涨跌百分比 / 是否在 MA200 上方 / 情绪"，
      而不需要跑完整 nasdaq_analyzer.main()。

策略：
- 优先用项目里的 DataFetcher + indicators.calc_all_indicators 拉 NDX 日 K
- 失败/没有依赖时，退化到 yfinance 直接拉
- 出错一律 fallback 一份 mock 数据，绝不让 webapp 504
"""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class NdxStatus:
    """今日 NDX 状态（给前端 dashboard 用）"""
    symbol: str = "NDX"
    last_close: float = 0.0
    change_pct: float = 0.0
    ma50: float = 0.0
    ma200: float = 0.0
    above_ma200: bool = False
    rsi14: float = 50.0
    sentiment: str = "neutral"      # "bull" / "bear" / "neutral"
    sentiment_label: str = "中性"
    summary: str = ""
    source: str = "live"            # "live" | "cached" | "mock"
    ts: int = 0
    ndx_analysis_report_path: str = ""  # 本地报告 HTML 文件路径（如果有）


def _import_root():
    """让 import 'data_fetcher' 'indicators' 能找到"""
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
    if _root not in sys.path:
        sys.path.insert(0, _root)


def _find_latest_report() -> str:
    """在 reports/ 下找最新的 nasdaq_report_*.html，返回 webapp 可见的相对路径"""
    _here = os.path.dirname(os.path.abspath(__file__))
    _root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
    reports_dir = os.path.join(_root, "reports")
    if not os.path.isdir(reports_dir):
        return ""
    files = [f for f in os.listdir(reports_dir)
             if f.startswith("nasdaq_report_") and f.endswith(".html")]
    if not files:
        return ""
    # 按日期排序
    files.sort(reverse=True)
    return f"reports/{files[0]}"


def _classify_sentiment(change_pct: float, above_ma200: bool, rsi: float) -> tuple[str, str]:
    """根据 3 个指标给出情绪判断"""
    if change_pct >= 0.7 and above_ma200 and rsi < 70:
        return "bull", "强势上涨"
    if change_pct >= 0.2 and above_ma200:
        return "bull", "温和偏多"
    if change_pct <= -0.7 and (not above_ma200) and rsi > 30:
        return "bear", "弱势下跌"
    if change_pct <= -0.2:
        return "bear", "偏空"
    if rsi > 70:
        return "bear", "RSI 超买"
    if rsi < 30:
        return "bull", "RSI 超卖"
    return "neutral", "中性震荡"


def _summary(sentiment_label: str, change_pct: float, above_ma200: bool) -> str:
    ma_clause = "MA200 上方" if above_ma200 else "MA200 下方"
    direction = "上涨" if change_pct >= 0 else "下跌"
    return f"NDX {direction} {abs(change_pct):.2f}%，{ma_clause}；情绪 {sentiment_label}"


def _mock_status() -> NdxStatus:
    """离线兜底数据"""
    last = 21_350.0
    chg = 1.12
    ma200 = last * 0.97
    return NdxStatus(
        last_close=last,
        change_pct=chg,
        ma50=last * 0.985,
        ma200=ma200,
        above_ma200=True,
        rsi14=58.4,
        sentiment="bull",
        sentiment_label="温和偏多",
        summary="NDX 上涨 1.12%，MA200 上方；情绪 温和偏多 (mock)",
        source="mock",
        ts=int(time.time() * 1000),
        ndx_analysis_report_path=_find_latest_report(),
    )


class NdxAdapter:
    """NDX 状态读取器——能调真依赖就调，不能就 mock"""

    def __init__(self, cache_ttl_seconds: int = 300):
        self._cache: Optional[NdxStatus] = None
        self._cached_at: float = 0.0
        self.ttl = cache_ttl_seconds

    def get_status(self, force: bool = False) -> NdxStatus:
        """返回今日 NDX 状态；force=True 跳过缓存"""
        if not force and self._cache and (time.time() - self._cached_at) < self.ttl:
            return self._cache

        st = self._fetch_live() or _mock_status()
        # 报告路径（mock 时也填）
        if not st.ndx_analysis_report_path:
            st.ndx_analysis_report_path = _find_latest_report()
        st.ts = int(time.time() * 1000)
        self._cache = st
        self._cached_at = time.time()
        return st

    # ------------------------------------------------------------------
    # 真数据获取（用项目原生的 data_fetcher + indicators）
    # ------------------------------------------------------------------
    def _fetch_live(self) -> Optional[NdxStatus]:
        try:
            _import_root()
            from data_fetcher import DataFetcher   # noqa: WPS433
            from indicators import calc_all_indicators  # noqa: WPS433
        except Exception as e:
            logger.warning("NDX live fetch skipped (deps missing): %s", e)
            return None

        try:
            fetcher = DataFetcher()
            df = fetcher.fetch_index_history({"ticker": "^NDX", "name": "NDX"})
            if df is None or len(df) == 0:
                return None

            df = calc_all_indicators(df)
            last_row = df.iloc[-1]

            last_close = float(last_row["Close"])
            prev_close = float(df.iloc[-2]["Close"]) if len(df) >= 2 else last_close
            change_pct = (last_close / prev_close - 1.0) * 100.0

            ma50  = float(last_row.get("MA50",  0.0) or 0.0)
            ma200 = float(last_row.get("MA200", 0.0) or 0.0)
            rsi14 = float(last_row.get("RSI14", 50.0) or 50.0)
            above_ma200 = ma200 > 0 and last_close > ma200

            sent, sent_label = _classify_sentiment(change_pct, above_ma200, rsi14)
            return NdxStatus(
                symbol="NDX",
                last_close=last_close,
                change_pct=change_pct,
                ma50=ma50,
                ma200=ma200,
                above_ma200=above_ma200,
                rsi14=rsi14,
                sentiment=sent,
                sentiment_label=sent_label,
                summary=_summary(sent_label, change_pct, above_ma200),
                source="live",
            )
        except Exception as e:
            logger.warning("NDX live fetch failed (%s); fallback to mock", e)
            return None


__all__ = ["NdxAdapter", "NdxStatus"]
