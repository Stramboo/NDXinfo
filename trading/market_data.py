# -*- coding: utf-8 -*-
"""
实时行情数据获取模块

功能:
- 批量获取股票历史数据（用于指标计算）
- 实时价格更新（定时轮询或 WebSocket 推送）
- 对模拟券商的自动价格同步

数据源优先级: yfinance（免费，延迟15分钟） > Alpaca WebSocket（需API Key，实时）
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable

import pandas as pd

from config import STOCK_UNIVERSE, HISTORY_PERIOD, HISTORY_INTERVAL
from trading.data_cache import HistoryCache
from trading.rate_limiter import TokenBucket

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """
    行情数据提供器

    负责:
    - 从 yfinance 获取历史 OHLCV 数据
    - 获取当前实时价格
    - 可选的后台轮询价格更新
    """

    def __init__(self):
        self._prices: dict[str, float] = {}
        self._price_callbacks: list[Callable] = []
        self._polling_thread: Optional[threading.Thread] = None
        self._polling_running = False
        self._poll_interval = 30  # 轮询间隔（秒）
        self._symbols: list[str] = []
        self._lock = threading.RLock()

        # 缓存与限流（可被热替换）
        self.history_cache = HistoryCache(max_entries=64)
        self.rate_limiter = TokenBucket(rate=2.0, burst=5)

        # 性能指标
        self.metrics = {
            "fetch_total": 0,
            "fetch_errors": 0,
            "last_refresh_at": None,
        }

        # 收集所有标的
        for tickers in STOCK_UNIVERSE.values():
            self._symbols.extend(tickers)

        logger.info(f"行情数据模块已初始化，监控 {len(self._symbols)} 只股票")

    # ----------------------------------------------------------
    # 历史数据
    # ----------------------------------------------------------

    def fetch_history(self, symbol: str, period: str = HISTORY_PERIOD) -> pd.DataFrame:
        """获取单只股票历史数据"""
        # 先查缓存
        cached = self.history_cache.get(symbol, period, HISTORY_INTERVAL)
        if cached is not None:
            return cached

        self.rate_limiter.acquire()
        try:
            import yfinance as yf
            df = yf.download(
                symbol, period=period, interval=HISTORY_INTERVAL,
                auto_adjust=True, progress=False, repair=True
            )
            if df is None or df.empty:
                return pd.DataFrame()
            # 标准化列名
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(c).capitalize() for c in df.columns]
            self.history_cache.put(symbol, period, HISTORY_INTERVAL, df)
            return df
        except Exception as e:
            self.metrics["fetch_errors"] += 1
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            return pd.DataFrame()

    def fetch_batch_history(self, symbols: list[str] = None,
                            period: str = HISTORY_PERIOD) -> dict[str, pd.DataFrame]:
        """批量获取历史数据"""
        if symbols is None:
            symbols = self._symbols

        result = {}
        try:
            import yfinance as yf
            df = yf.download(
                symbols, period=period, interval=HISTORY_INTERVAL,
                auto_adjust=True, progress=False, threads=True,
                group_by='ticker', repair=True
            )
            if df is None or df.empty:
                return {s: pd.DataFrame() for s in symbols}

            for symbol in symbols:
                try:
                    if isinstance(df.columns, pd.MultiIndex):
                        if symbol in df.columns.get_level_values(0):
                            stock_df = df[symbol].copy()
                            stock_df.columns = [str(c).capitalize() for c in stock_df.columns]
                            result[symbol] = stock_df
                        else:
                            result[symbol] = pd.DataFrame()
                    else:
                        stock_df = df.copy()
                        stock_df.columns = [str(c).capitalize() for c in stock_df.columns]
                        result[symbol] = stock_df
                except Exception:
                    result[symbol] = pd.DataFrame()

            logger.info(f"批量下载 {len(symbols)} 只股票历史数据完成")
        except Exception as e:
            logger.error(f"批量下载失败: {e}")
            result = {s: pd.DataFrame() for s in symbols}

        return result

    # ----------------------------------------------------------
    # 实时价格
    # ----------------------------------------------------------

    def get_price(self, symbol: str) -> Optional[float]:
        """获取单只股票当前价格（缓存优先）"""
        with self._lock:
            cached = self._prices.get(symbol.upper())
        if cached is not None:
            return cached

        return self._fetch_live_price(symbol)

    def get_all_prices(self) -> dict[str, float]:
        """获取所有股票当前价格"""
        with self._lock:
            return dict(self._prices)

    def _fetch_live_price(self, symbol: str) -> Optional[float]:
        """从数据源获取实时价格"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            if price:
                price = float(price)
                with self._lock:
                    self._prices[symbol.upper()] = price
                return price

            # 降级：用最近历史数据
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                with self._lock:
                    self._prices[symbol.upper()] = price
                return price
        except Exception as e:
            logger.debug(f"获取 {symbol} 实时价格失败: {e}")
        return None

    def refresh_prices(self) -> dict[str, float]:
        """刷新所有标的的实时价格（阻塞调用）。

        性能优化：使用 yf.download 单次取多只股票价格，避免 N 次网络往返。
        """
        if not self._symbols:
            return self.get_all_prices()

        self.rate_limiter.acquire()
        started = time.monotonic()
        try:
            import yfinance as yf
            tickers = " ".join(self._symbols)
            try:
                data = yf.download(
                    tickers,
                    period="1d",
                    interval="1m",
                    auto_adjust=True,
                    progress=False,
                    threads=True,
                    group_by="ticker",
                )
                for symbol in self._symbols:
                    try:
                        if isinstance(data.columns, pd.MultiIndex):
                            if symbol not in data.columns.get_level_values(0):
                                continue
                            close = data[symbol]["Close"].dropna()
                        else:
                            close = data["Close"].dropna()
                        if close is None or close.empty:
                            continue
                        price = float(close.iloc[-1])
                        with self._lock:
                            self._prices[symbol.upper()] = price
                    except Exception:
                        # 单只标的失败不阻塞整体
                        continue
            except Exception as e:
                # 整体失败：降级为逐只 fallback
                logger.debug(f"批量价格刷新失败，降到逐只: {e}")
                for symbol in self._symbols:
                    self._fetch_live_price(symbol)

            self.metrics["fetch_total"] += 1
            self.metrics["last_refresh_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated = sum(1 for _ in self._symbols if self._prices.get(_))
            elapsed = round(time.monotonic() - started, 2)
            logger.info(f"价格刷新完成: {updated}/{len(self._symbols)} 成功 in {elapsed}s")
        except Exception as e:
            self.metrics["fetch_errors"] += 1
            logger.error(f"刷新价格异常: {e}")
        return self.get_all_prices()

    # ----------------------------------------------------------
    # 后台轮询
    # ----------------------------------------------------------

    def start_polling(self, interval_seconds: int = 30):
        """启动后台价格轮询"""
        if self._polling_running:
            logger.warning("轮询已在运行中")
            return

        self._poll_interval = max(interval_seconds, 10)  # 最小10秒
        self._polling_running = True
        self._polling_thread = threading.Thread(
            target=self._polling_loop, daemon=True, name="MarketPoller"
        )
        self._polling_thread.start()
        logger.info(f"行情轮询已启动，间隔 {self._poll_interval} 秒")

    def stop_polling(self):
        """停止后台价格轮询"""
        self._polling_running = False
        if self._polling_thread:
            self._polling_thread.join(timeout=5)
        logger.info("行情轮询已停止")

    def _polling_loop(self):
        """轮询主循环

        失败连续 N 次后指数退避，恢复成功后回到默认间隔。
        """
        consecutive_fail = 0
        max_consecutive_fail = 3
        while self._polling_running:
            ok = True
            try:
                prices = self.refresh_prices()
                # 若新数据为空则记为失败
                if not prices:
                    ok = False
                self._notify_price_update()
            except Exception as e:
                ok = False
                logger.error(f"轮询异常: {e}")

            if ok:
                consecutive_fail = 0
                wait = self._poll_interval
            else:
                consecutive_fail += 1
                # 失败 3 次后开始退避
                if consecutive_fail >= max_consecutive_fail:
                    wait = self._poll_interval * (2 ** (consecutive_fail - max_consecutive_fail + 1))
                    wait = min(wait, 600)  # 上限 10 分钟
                    logger.warning(
                        f"行情连续失败 {consecutive_fail} 次，退避至 {wait}s"
                    )
                else:
                    wait = self._poll_interval

            # 分段睡眠以支持快速停止
            for _ in range(int(wait)):
                if not self._polling_running:
                    return
                time.sleep(1)

    def on_price_update(self, callback: Callable):
        """注册价格更新回调"""
        self._price_callbacks.append(callback)

    def _notify_price_update(self):
        """通知所有价格回调"""
        prices = self.get_all_prices()
        for cb in self._price_callbacks:
            try:
                cb(prices)
            except Exception:
                pass

    # ----------------------------------------------------------
    # 工具方法
    # ----------------------------------------------------------

    def get_symbols(self) -> list[str]:
        """获取监控的标的列表"""
        return list(self._symbols)

    def add_symbol(self, symbol: str):
        """动态添加标的"""
        symbol = symbol.upper()
        if symbol not in self._symbols:
            self._symbols.append(symbol)
            logger.info(f"已添加标的: {symbol}")

    def remove_symbol(self, symbol: str):
        """动态移除标的"""
        symbol = symbol.upper()
        if symbol in self._symbols:
            self._symbols.remove(symbol)
            with self._lock:
                self._prices.pop(symbol, None)
            logger.info(f"已移除标的: {symbol}")
