# -*- coding: utf-8 -*-
"""
交易引擎

将券商、行情、策略、风险管理、订单执行等模块整合在一起，
提供统一的交易核心。支持：
- 手动/自动模式切换
- 后台自动运行循环
- 实时状态报告
- GUI 事件回调

使用方式:
    engine = TradingEngine(broker_type="simulation", strategy_name="multi")
    engine.start_auto()   # 启动自动交易
    engine.manual_buy("AAPL", 10)  # 手动买入
    engine.stop()         # 停止
"""

import logging
import threading
import time
import traceback
from datetime import datetime
from enum import Enum
from typing import Optional, Callable

import pandas as pd

from trading.broker import (
    BrokerBase, OrderSide, OrderType, OrderStatus, Order,
    AccountInfo, Position, SimulationBroker, create_broker,
)
from trading.market_data import MarketDataProvider
from trading.strategy import Signal, SignalAction, StrategyBase, create_strategy
from trading.risk_manager import RiskManager, RiskLimits
from trading.executor import OrderExecutor
from indicators import calc_all_indicators


class ErrorKind(Enum):
    """异常分类（用于自动循环可观测性）"""
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    DATA_EMPTY = "data_empty"
    EXECUTION = "execution"
    UNKNOWN = "unknown"

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    交易引擎

    所有模块的协调中心，提供统一的外部接口。
    """

    def __init__(
        self,
        broker_type: str = "simulation",
        strategy_name: str = "multi",
        initial_cash: float = 100000.0,
        risk_limits: RiskLimits = None,
    ):
        """
        初始化交易引擎

        参数:
            broker_type:   "simulation" | "alpaca"
            strategy_name: "macd" | "rsi" | "ma_trend" | "bollinger" | "multi"
            initial_cash:  模拟券商的初始资金
            risk_limits:   风险参数（None=使用默认值）
        """
        # 核心模块
        self.broker: BrokerBase = create_broker(
            broker_type=broker_type, initial_cash=initial_cash
        )
        self.market_data = MarketDataProvider()
        self.strategy: StrategyBase = create_strategy(strategy_name)
        self.risk_manager = RiskManager(limits=risk_limits)
        self.executor = OrderExecutor(
            broker=self.broker,
            risk_manager=self.risk_manager,
        )

        # 历史数据缓存（用于指标计算）
        self._hist_data: dict[str, pd.DataFrame] = {}

        # 自动交易状态
        self._auto_running = False
        self._auto_thread: Optional[threading.Thread] = None
        self._auto_interval = 60  # 自动交易间隔（秒）

        # 回调
        self._status_callbacks: list[Callable] = []
        self._signal_callbacks: list[Callable] = []
        self._log_callbacks: list[Callable] = []

        # 上次信号时间
        self._last_signal_time: dict[str, float] = {}

        # 心跳指标
        self._tick_count = 0
        self._success_count = 0
        self._error_count = 0
        self._started_at = datetime.now()

        logger.info(f"交易引擎已初始化 | 券商={self.broker.name} | 策略={self.strategy.name}")

        # 注入日志回调到各模块
        self._setup_logging()

    def switch_strategy(self, strategy_name: str):
        """运行时切换策略"""
        new_strategy = create_strategy(strategy_name)
        self.strategy = new_strategy
        logger.info(f"策略已切换为: {strategy_name}")

    def _setup_logging(self):
        """设置日志回调"""
        class CallbackHandler(logging.Handler):
            def __init__(self, engine):
                super().__init__()
                self.engine = engine

            def emit(self, record):
                msg = self.format(record)
                self.engine._notify_log(msg)

        handler = CallbackHandler(self)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                                datefmt="%H:%M:%S"))
        logging.getLogger("trading").addHandler(handler)

    # ----------------------------------------------------------
    # 手动交易接口
    # ----------------------------------------------------------

    def manual_buy(self, symbol: str, quantity: int) -> Order:
        """手动买入"""
        logger.info(f"手动买入: {symbol} x{quantity}")
        # 价格来源：market_data → 历史数据 → broker 行情（向后兼容）
        price = (
            self.market_data.get_price(symbol)
            or self._get_hist_price(symbol)
            or self._broker_price(symbol)
        )
        account = self.broker.get_account()
        positions = self.broker.get_positions()

        check = self.risk_manager.check_buy(
            symbol=symbol, quantity=quantity, price=price,
            positions=positions, account_equity=account.equity,
            account_cash=account.cash,
        )

        if not check.allowed:
            logger.warning(f"风险检查拦截: {check.reason}")
            return Order(
                order_id="", symbol=symbol, side=OrderSide.BUY,
                order_type=OrderType.MARKET, quantity=quantity,
                status=OrderStatus.REJECTED, note=check.reason,
            )

        order = self.broker.place_order(
            symbol=symbol, quantity=quantity,
            side=OrderSide.BUY, order_type=OrderType.MARKET,
        )
        if order.status == OrderStatus.FILLED:
            self.risk_manager.record_trade(symbol)
        self._notify_status_changed()
        return order

    def manual_sell(self, symbol: str, quantity: int = 0) -> Order:
        """手动卖出（quantity=0 表示全部卖出）"""
        pos = self.broker.get_position(symbol)
        if pos is None:
            logger.warning(f"无 {symbol} 持仓")
            return Order(
                order_id="", symbol=symbol, side=OrderSide.SELL,
                order_type=OrderType.MARKET, quantity=0,
                status=OrderStatus.REJECTED, note="无持仓",
            )

        qty = quantity if quantity > 0 else pos.quantity
        logger.info(f"手动卖出: {symbol} x{qty}")

        order = self.broker.place_order(
            symbol=symbol, quantity=qty,
            side=OrderSide.SELL, order_type=OrderType.MARKET,
        )
        if order.status == OrderStatus.FILLED:
            pnl = (order.avg_fill_price - pos.avg_cost) * qty
            self.risk_manager.record_trade(symbol, pnl)
        self._notify_status_changed()
        return order

    # ----------------------------------------------------------
    # 自动交易
    # ----------------------------------------------------------

    def start_auto(self, interval_seconds: int = 60):
        """启动自动交易循环"""
        if self._auto_running:
            logger.warning("自动交易已在运行中")
            return

        self._auto_interval = max(interval_seconds, 30)
        self._auto_running = True
        self._started_at = datetime.now()
        self._tick_count = 0
        self._error_count = 0
        self._success_count = 0
        self._auto_thread = threading.Thread(
            target=self._auto_loop, daemon=True, name="AutoTrader"
        )
        self._auto_thread.start()
        # startup banner
        logger.info(
            f"[startup] broker={self.broker.name} strategy={self.strategy.name} "
            f"cash={self._initial_cash_for_log()} symbols={len(self.market_data.get_symbols())} "
            f"interval={self._auto_interval}s"
        )
        logger.info(f"自动交易已启动，扫描间隔 {self._auto_interval} 秒")

    def _initial_cash_for_log(self) -> str:
        try:
            return f"{self.broker.get_account().equity:,.0f}"
        except Exception:
            return "?"

    def stop_auto(self):
        """停止自动交易"""
        self._auto_running = False
        if self._auto_thread:
            self._auto_thread.join(timeout=10)
        logger.info("自动交易已停止")

    @property
    def is_auto_running(self) -> bool:
        return self._auto_running

    def _auto_loop(self):
        """自动交易主循环

        - 单次失败不退出循环
        - 异常按类型区分（网络、限流、数据空、执行），不计入风控冷却
        """
        logger.info("自动交易循环开始")

        # 首次加载全部历史数据
        self._load_all_history()

        while self._auto_running:
            self._tick_count += 1
            try:
                self._auto_tick()
                self._success_count += 1
            except Exception as e:
                self._error_count += 1
                kind = self._classify_error(e)
                logger.error(
                    f"[tick #{self._tick_count}] 异常: kind={kind.value} "
                    f"err={type(e).__name__}: {e}"
                )
                logger.debug(traceback.format_exc())

            logger.debug(
                f"[heartbeat] tick={self._tick_count} "
                f"ok={self._success_count} err={self._error_count}"
            )

            # 分段睡眠，便于快速停止
            for _ in range(self._auto_interval):
                if not self._auto_running:
                    break
                time.sleep(1)

        logger.info("自动交易循环结束")

    def _classify_error(self, exc: BaseException) -> ErrorKind:
        name = type(exc).__name__.lower()
        msg = str(exc).lower()
        if "ratelimit" in name or "rate limit" in msg or "too many requests" in msg:
            return ErrorKind.RATE_LIMIT
        if "timeout" in msg or "connection" in msg or "network" in msg:
            return ErrorKind.NETWORK
        if "empty" in msg or "no data" in msg:
            return ErrorKind.DATA_EMPTY
        if "order" in msg or "reject" in msg or "risk" in msg:
            return ErrorKind.EXECUTION
        return ErrorKind.UNKNOWN

    def _auto_tick(self):
        """单次自动交易扫描"""
        # 1. 刷新价格
        prices = self.market_data.refresh_prices()

        # 2. 同步价格到模拟券商
        if isinstance(self.broker, SimulationBroker):
            self.broker.set_price_batch(prices)

        # 3. 检查止损止盈
        stop_orders = self.executor.check_stop_conditions()

        # 4. 更新账户信息，通知风控
        account = self.broker.get_account()
        self.risk_manager.update_equity(account.equity)

        # 5. 为每个标的生成信号
        symbols = self.market_data.get_symbols()
        signals = []

        for symbol in symbols:
            # 检查冷却时间（避免同标的频繁交易）
            last_time = self._last_signal_time.get(symbol, 0)
            if time.time() - last_time < 300:  # 5分钟冷却
                continue

            df = self._hist_data.get(symbol)
            if df is None or df.empty:
                # 尝试获取
                df = self.market_data.fetch_history(symbol)
                if df is not None and not df.empty:
                    df = calc_all_indicators(df)
                    self._hist_data[symbol] = df
                else:
                    continue
            else:
                # 增量更新最后一行
                if price := prices.get(symbol):
                    self._hist_data[symbol] = self._update_last_row(df, price)

            signal = self.strategy.generate_signal(symbol, self._hist_data[symbol])
            if signal.is_trade_signal:
                signals.append(signal)
                self._last_signal_time[symbol] = time.time()

        # 6. 执行信号
        for sig in signals:
            self._notify_signal(sig)
            self.executor.execute_signal(sig)

        # 7. 通知状态更新
        self._notify_status_changed()

    def _load_all_history(self):
        """加载所有标的历史数据并计算指标"""
        logger.info("加载历史数据...")
        symbols = self.market_data.get_symbols()
        hist = self.market_data.fetch_batch_history(symbols, period="6mo")

        for symbol, df in hist.items():
            if not df.empty and len(df) >= 30:
                df = calc_all_indicators(df)
                self._hist_data[symbol] = df

        loaded = len(self._hist_data)
        logger.info(f"历史数据加载完成: {loaded}/{len(symbols)}")

    def _update_last_row(self, df: pd.DataFrame, price: float) -> pd.DataFrame:
        """用最新价格更新DataFrame最后一行（近似刷新）"""
        if df is None or df.empty:
            return df
        df = df.copy()
        df.iloc[-1, df.columns.get_loc("Close")] = price
        df.iloc[-1, df.columns.get_loc("High")] = max(df.iloc[-1]["High"], price)
        df.iloc[-1, df.columns.get_loc("Low")] = min(df.iloc[-1]["Low"], price)
        return df

    def _broker_price(self, symbol: str) -> float:
        """从 broker 取最后报价（broker 自身或 SimulationBroker._prices）"""
        try:
            quote = self.broker.get_quote(symbol)
            if quote and quote.get("price"):
                return float(quote["price"])
        except Exception:
            return 0.0
        return 0.0

    def _get_hist_price(self, symbol: str) -> float:
        """从历史数据获取最近价格"""
        df = self._hist_data.get(symbol)
        if df is not None and not df.empty and "Close" in df.columns:
            return float(df["Close"].iloc[-1])
        return 0.0

    # ----------------------------------------------------------
    # 状态查询
    # ----------------------------------------------------------

    def get_status(self) -> dict:
        """获取引擎完整状态"""
        account = self.broker.get_account()
        positions = self.broker.get_positions()

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "broker_name": self.broker.name,
            "strategy_name": self.strategy.name,
            "strategy_enabled": self.strategy.enabled,
            "auto_running": self._auto_running,
            "heartbeat": {
                "tick_count": self._tick_count,
                "success_count": self._success_count,
                "error_count": self._error_count,
                "uptime_seconds": int((datetime.now() - self._started_at).total_seconds()),
            },
            "market_health": {
                "fetch_total": self.market_data.metrics["fetch_total"],
                "fetch_errors": self.market_data.metrics["fetch_errors"],
                "last_refresh_at": self.market_data.metrics["last_refresh_at"],
                "cache_hit_ratio": self.market_data.history_cache.stats()["hit_ratio"],
            },
            "account": {
                "cash": account.cash,
                "equity": account.equity,
                "buying_power": account.buying_power,
                "total_return_pct": account.total_return_pct,
            },
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "unrealized_pnl": p.unrealized_pnl,
                    "unrealized_pnl_pct": p.unrealized_pnl_pct,
                }
                for p in positions
            ],
            "risk": self.risk_manager.get_status(),
            "recent_orders": [
                {
                    "order_id": o.order_id,
                    "symbol": o.symbol,
                    "side": o.side.value,
                    "quantity": o.quantity,
                    "avg_fill_price": o.avg_fill_price,
                    "status": o.status.value,
                    "note": o.note,
                    "created_at": o.created_at,
                }
                for o in self.executor.get_order_history(limit=20)
            ],
        }

    def get_dashboard_data(self) -> dict:
        """获取仪表盘汇总数据"""
        status = self.get_status()
        account = status["account"]
        positions = status["positions"]
        risk = status["risk"]

        # 计算当日盈亏
        daily_pnl = sum(p["unrealized_pnl"] for p in positions)

        return {
            "equity": account["equity"],
            "cash": account["cash"],
            "market_value": account["equity"] - account["cash"],
            "total_return_pct": account["total_return_pct"],
            "daily_pnl": daily_pnl,
            "daily_trades": risk["daily_trades"],
            "position_count": len(positions),
            "auto_running": self._auto_running,
        }

    # ----------------------------------------------------------
    # 回调管理
    # ----------------------------------------------------------

    def on_status_changed(self, callback: Callable):
        """注册状态变更回调"""
        self._status_callbacks.append(callback)

    def on_signal(self, callback: Callable):
        """注册信号回调"""
        self._signal_callbacks.append(callback)

    def on_log(self, callback: Callable):
        """注册日志回调"""
        self._log_callbacks.append(callback)

    def _notify_status_changed(self):
        """通知状态变更"""
        status = self.get_status()
        for cb in self._status_callbacks:
            try:
                cb(status)
            except Exception:
                pass

    def _notify_signal(self, signal: Signal):
        """通知交易信号"""
        for cb in self._signal_callbacks:
            try:
                cb(signal)
            except Exception:
                pass

    def _notify_log(self, msg: str):
        """通知日志消息"""
        for cb in self._log_callbacks:
            try:
                cb(msg)
            except Exception:
                pass

    # ----------------------------------------------------------
    # 生命周期
    # ----------------------------------------------------------

    def stop(self):
        """停止引擎"""
        self.stop_auto()
        self.market_data.stop_polling()
        logger.info("交易引擎已停止")
