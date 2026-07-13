# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 新闻情绪分析模块
词典法情绪分析，零重型依赖
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================
# 中英文金融情感词典
# ============================================================

POSITIVE_WORDS = {
    # 中文正面
    "利好", "上涨", "增长", "盈利", "突破", "创新高", "大涨", "暴涨", "反弹",
    "强势", "买入", "增持", "升级", "超预期", "回暖", "复苏", "牛市", "看涨",
    "机会", "分红", "回购", "合作", "签约", "获批", "批准", "成功", "领先",
    "需求旺盛", "订单", "营收增长", "利润增长", "市场看好", "提振", "刺激",
    # 英文正面
    "surge", "rally", "gain", "bullish", "upgrade", "beat", "strong", "growth",
    "profit", "record", "high", "positive", "optimistic", "buy", "overweight",
    "breakthrough", "innovation", "partnership", "approval", "launch",
}

NEGATIVE_WORDS = {
    # 中文负面
    "利空", "下跌", "亏损", "下滑", "暴跌", "大跌", "破位", "新低", "看跌",
    "卖出", "减持", "降级", "不及预期", "衰退", "熊市", "风险", "警告",
    "调查", "诉讼", "罚款", "违规", "退市", "停牌", "裁员", "关停", "召回",
    "债务", "违约", "破产", "制裁", "贸易战", "关税", "通胀", "加息",
    # 英文负面
    "plunge", "crash", "drop", "bearish", "downgrade", "miss", "weak", "loss",
    "decline", "fall", "sell", "underweight", "lawsuit", "investigation",
    "recall", "bankruptcy", "debt", "default", "sanction", "tariff",
}


def _score_text(text):
    """对单条文本进行情感打分"""
    if not text:
        return 0
    text_lower = text.lower()
    score = 0
    for word in POSITIVE_WORDS:
        if word in text_lower:
            score += 1
    for word in NEGATIVE_WORDS:
        if word in text_lower:
            score -= 1
    # 归一化到 -1 ~ +1
    if score == 0:
        return 0
    return max(-1, min(1, score / 5.0))


def _label_from_score(score):
    """根据分数生成标签"""
    if score > 0.2:
        return "看多"
    elif score < -0.2:
        return "看空"
    else:
        return "中性"


def _fetch_news_yfinance(tickers, top_n=10):
    """通过 yfinance 获取新闻（英文，备选方案）"""
    try:
        import yfinance as yf
        all_news = []
        for ticker in tickers[:3]:  # 限制请求数量
            try:
                stock = yf.Ticker(ticker)
                news = stock.news
                if news:
                    for item in news[:top_n // 3 + 1]:
                        title = item.get("title", "")
                        publisher = item.get("publisher", "")
                        pub_time = item.get("providerPublishTime", "")
                        if pub_time:
                            try:
                                pub_time = datetime.fromtimestamp(
                                    pub_time if isinstance(pub_time, (int, float)) else 0
                                ).strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                pub_time = ""
                        all_news.append({
                            "title": title,
                            "source": publisher,
                            "time": pub_time,
                            "ticker": ticker,
                        })
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"获取 {ticker} 新闻失败: {e}")
                continue
        return all_news
    except ImportError:
        logger.warning("yfinance 未安装，无法获取新闻")
        return []


def _fetch_news_akshare(top_n=10):
    """通过 AKShare 获取财经新闻（中文，优先方案）"""
    try:
        import akshare as ak
        news_list = []
        # 尝试获取东方财富新闻
        try:
            df = ak.stock_news_em(symbol="000001")
            if df is not None and not df.empty:
                for _, row in df.head(top_n).iterrows():
                    news_list.append({
                        "title": str(row.get("新闻标题", "")),
                        "source": str(row.get("文章来源", "")),
                        "time": str(row.get("发布时间", "")),
                        "ticker": "",
                    })
        except Exception as e:
            logger.debug(f"AKShare stock_news_em 失败: {e}")

        # 尝试央视新闻
        if not news_list:
            try:
                df = ak.news_cctv(date=datetime.now().strftime("%Y%m%d"))
                if df is not None and not df.empty:
                    for _, row in df.head(top_n).iterrows():
                        news_list.append({
                            "title": str(row.get("title", "")),
                            "source": "央视财经",
                            "time": str(row.get("date", "")),
                            "ticker": "",
                        })
            except Exception as e:
                logger.debug(f"AKShare news_cctv 失败: {e}")

        return news_list
    except ImportError:
        logger.info("AKShare 未安装，使用 yfinance 新闻源")
        return []


def analyze_market_sentiment(tickers, top_n=10):
    """
    分析市场新闻情绪

    返回: {
        "overall_score": float,        # -1 ~ +1
        "overall_label": "看多"|"中性"|"看空",
        "news_items": [{"title", "source", "time", "sentiment", "score"}],
        "per_ticker": {"NVDA": score, ...}
    }
    """
    logger.info("开始获取新闻并分析情绪...")

    # 优先使用 AKShare，降级到 yfinance
    news_items = _fetch_news_akshare(top_n)

    if not news_items:
        # 降级到 yfinance
        news_items = _fetch_news_yfinance(tickers, top_n)

    if not news_items:
        logger.warning("无法获取新闻数据，跳过情绪分析")
        return {
            "overall_score": 0,
            "overall_label": "无数据",
            "news_items": [],
            "per_ticker": {},
        }

    # 对每条新闻打分
    scored_news = []
    total_score = 0
    per_ticker_scores = {}

    for item in news_items:
        title = item.get("title", "")
        score = _score_text(title)
        label = _label_from_score(score)

        scored_news.append({
            "title": title,
            "source": item.get("source", ""),
            "time": item.get("time", ""),
            "sentiment": label,
            "score": round(score, 2),
        })

        total_score += score

        ticker = item.get("ticker", "")
        if ticker:
            if ticker not in per_ticker_scores:
                per_ticker_scores[ticker] = []
            per_ticker_scores[ticker].append(score)

    # 计算整体情绪
    overall_score = total_score / len(scored_news) if scored_news else 0
    overall_score = max(-1, min(1, overall_score))
    overall_label = _label_from_score(overall_score)

    # 计算每只股票的平均情绪
    per_ticker_avg = {}
    for ticker, scores in per_ticker_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        per_ticker_avg[ticker] = round(max(-1, min(1, avg)), 2)

    result = {
        "overall_score": round(overall_score, 2),
        "overall_label": overall_label,
        "news_items": scored_news[:top_n],
        "per_ticker": per_ticker_avg,
    }

    logger.info(f"情绪分析完成: 整体情绪={overall_label}({overall_score:+.2f}), "
                 f"新闻数={len(scored_news)}")

    return result
