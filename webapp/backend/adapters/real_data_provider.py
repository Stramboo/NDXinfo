# -*- coding: utf-8 -*-
"""
real_data_provider.py — 真实市场数据 Provider (v2.3 Phase 1)

通过 Yahoo Finance API 获取真实股票数据，带 60 秒内存缓存。
失败时自动降级到 Mock 数据（Graceful Degradation）。

Feature Flag: ENABLE_REAL_DATA (默认 false)
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# 缓存：{symbol: (timestamp, data)}
_quote_cache: dict[str, tuple[float, dict]] = {}
_ohlc_cache: dict[str, tuple[float, list]] = {}
CACHE_TTL = 60  # 60 秒缓存


def _is_cache_valid(ts: float) -> bool:
    """检查缓存是否过期"""
    return (time.time() - ts) < CACHE_TTL


def get_quote(symbol: str) -> Optional[dict]:
    """
    获取单只股票实时报价

    返回:
        dict: {symbol, price, change, change_pct, volume, market_cap, updated_at}
        None: 获取失败
    """
    symbol = symbol.upper()

    # 检查缓存
    if symbol in _quote_cache:
        ts, data = _quote_cache[symbol]
        if _is_cache_valid(ts):
            return data

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("regularMarketPrice") or info.get("currentPrice")
        if price is None:
            # 尝试从 fast_info 获取
            price = getattr(ticker.fast_info, "last_price", None)

        if price is None:
            logger.warning(f"无法获取 {symbol} 的价格")
            return None

        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
        change = round(price - prev_close, 2) if prev_close else 0
        change_pct = round((price / prev_close - 1) * 100, 2) if prev_close else 0

        result = {
            "symbol": symbol,
            "price": round(price, 2),
            "change": change,
            "change_pct": change_pct,
            "volume": info.get("regularMarketVolume") or info.get("volume"),
            "market_cap": info.get("marketCap"),
            "name": info.get("shortName") or info.get("longName") or symbol,
            "updated_at": int(time.time()),
            "source": "real",
        }

        _quote_cache[symbol] = (time.time(), result)
        return result

    except ImportError:
        logger.warning("yfinance 未安装，无法获取真实数据")
        return None
    except Exception as e:
        logger.warning(f"获取 {symbol} 报价失败: {e}")
        return None


def get_ohlc(symbol: str, period: str = "6mo", interval: str = "1d") -> Optional[list]:
    """
    获取 K 线历史数据

    参数:
        symbol: 股票代码
        period: 时间范围 (1mo, 3mo, 6mo, 1y)
        interval: K线间隔 (1d, 1wk, 1mo)

    返回:
        list[dict]: [{t, o, h, l, c, v}, ...]
        None: 获取失败
    """
    symbol = symbol.upper()
    cache_key = f"{symbol}:{period}:{interval}"

    # 检查缓存
    if cache_key in _ohlc_cache:
        ts, data = _ohlc_cache[cache_key]
        if _is_cache_valid(ts):
            return data

    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            logger.warning(f"{symbol} 无历史数据")
            return None

        result = []
        for idx, row in df.iterrows():
            result.append({
                "t": int(idx.timestamp()),
                "o": round(row["Open"], 2),
                "h": round(row["High"], 2),
                "l": round(row["Low"], 2),
                "c": round(row["Close"], 2),
                "v": int(row["Volume"]),
            })

        _ohlc_cache[cache_key] = (time.time(), result)
        return result

    except ImportError:
        logger.warning("yfinance 未安装，无法获取真实数据")
        return None
    except Exception as e:
        logger.warning(f"获取 {symbol} K线失败: {e}")
        return None


def get_batch_quotes(symbols: list[str]) -> dict[str, dict]:
    """
    批量获取多只股票报价

    返回:
        dict: {symbol: quote_data, ...}
    """
    result = {}
    for sym in symbols:
        quote = get_quote(sym)
        if quote:
            result[sym] = quote
    return result


def clear_cache():
    """清空缓存（测试用）"""
    global _quote_cache, _ohlc_cache
    _quote_cache = {}
    _ohlc_cache = {}


__all__ = ["get_quote", "get_ohlc", "get_batch_quotes", "clear_cache"]
