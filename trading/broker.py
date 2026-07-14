# -*- coding: utf-8 -*-
"""
券商接口抽象层

提供统一的券商 API 接口，支持：
- SimulationBroker: 纯模拟券商（无需 API Key，适合回测/开发测试）
- AlpacaBroker:    Alpaca Markets 券商（支持 Paper Trading 和 Live Trading）

使用方式:
    broker = SimulationBroker(initial_cash=100000)
    broker.place_order("AAPL", 10, "buy", "market")
"""

import uuid
import logging
import threading
import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, Callable

from trading.sim_rules import SimExecutionRules, DEFAULT_RULES

logger = logging.getLogger(__name__)


# 拒绝原因码（RiskManager 与 Broker 复用）
REJECT_OK = 0
REJECT_INSUFFICIENT_CASH = 10
REJECT_INSUFFICIENT_POSITION = 11
REJECT_T_PLUS_ONE = 12
REJECT_RISK_LIMIT = 13
REJECT_MATCHING = 14
REJECT_INVALID_PRICE = 15
REJECT_OTHER = 99


# ============================================================
# 数据模型
# ============================================================

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Order:
    """订单数据模型

    新增字段（向后兼容，旧调用方可继续构造 Order 时不传）：
        commission:        实际扣减的佣金（美元）
        slippage_bps:      实际成交滑点（基点）
        intended_price:    下单时参考价（市价单即当时市价）
        rejection_code:    拒绝原因码（使用 REJECT_* 常量）
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    filled_quantity: int = 0
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    avg_fill_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    filled_at: Optional[str] = None
    note: str = ""
    # ----- 新增（带默认值，向后兼容） -----
    commission: float = 0.0
    slippage_bps: float = 0.0
    intended_price: float = 0.0
    rejection_code: int = REJECT_OK


@dataclass
class Position:
    """持仓数据模型"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0


@dataclass
class AccountInfo:
    """账户信息

    新增字段（向后兼容）：
        settled_cash:    已结算资金（可立即用于买入）
        unsettled_cash:  待结算资金（T+1 启用时，卖出次日才可使用）
    """
    cash: float
    equity: float
    buying_power: float
    initial_capital: float
    realized_pnl: float = 0.0
    total_return_pct: float = 0.0
    settled_cash: float = 0.0
    unsettled_cash: float = 0.0


# ============================================================
# 抽象基类
# ============================================================

class BrokerBase(ABC):
    """券商接口抽象基类"""

    def __init__(self, name: str = "Broker"):
        self.name = name
        self._order_callbacks: list[Callable] = []

    @abstractmethod
    def get_account(self) -> AccountInfo:
        """获取账户信息"""
        ...

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """获取当前所有持仓"""
        ...

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定标的持仓"""
        ...

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        quantity: int,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """下单"""
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        ...

    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        """查询订单"""
        ...

    @abstractmethod
    def get_orders(self, status: Optional[OrderStatus] = None) -> list[Order]:
        """查询订单列表"""
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[dict]:
        """获取实时报价"""
        ...

    def on_order_update(self, callback: Callable):
        """注册订单更新回调"""
        self._order_callbacks.append(callback)

    def _notify_order_update(self, order: Order):
        """通知订单更新"""
        for cb in self._order_callbacks:
            try:
                cb(order)
            except Exception as e:
                logger.error(f"订单回调异常: {e}")


# ============================================================
# 纯模拟券商（无需 API Key）
# ============================================================

class SimulationBroker(BrokerBase):
    """
    纯模拟券商 - 完全本地运行，无需任何 API Key

    适合策略开发、回测验证，所有交易都在本地虚拟执行。
    价格来源: 外部传入的行情数据（通过 get_quote / set_price 更新）

    新增（向后兼容）：
        - rules: SimExecutionRules 控制滑点 / 手续费 / 撮合延迟 / 部分成交 / T+1
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        rules: Optional[SimExecutionRules] = None,
    ):
        super().__init__(name="模拟券商")
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._settled_cash = initial_cash     # T+1 资金已结算部分
        # 没有 T+1 时两者保持一致
        self._positions: dict[str, Position] = {}
        self._orders: dict[str, Order] = {}
        self._prices: dict[str, float] = {}
        self._lock = threading.RLock()        # 改成 RLock 以支持回调链
        # 撮合规则；默认关闭全部仿真项以保持向后兼容
        self._rules: SimExecutionRules = rules or DEFAULT_RULES
        # 上一交易日（用于 T+1 解锁）
        self._last_settle_date: date = datetime.now().date()

        logger.info(
            f"模拟券商已初始化，初始资金: ${initial_cash:,.2f} | "
            f"slippage={self._rules.slippage_bps}bps "
            f"commission=${self._rules.commission_per_share}/share "
            f"t+1={self._rules.t_plus_one}"
        )

    # ----------------------------------------------------------
    # 规则与状态
    # ----------------------------------------------------------

    def set_rules(self, rules: SimExecutionRules):
        """热替换撮合规则（运行中调用也会影响后续订单）"""
        with self._lock:
            self._rules = rules

    def get_rules(self) -> SimExecutionRules:
        return self._rules

    def settle_daily(self, today: Optional[date] = None):
        """每日清算：把 unsettled → settled。仅在 t_plus_one=True 下有意义。"""
        today = today or datetime.now().date()
        with self._lock:
            if today > self._last_settle_date:
                self._settled_cash = round(self._cash, 2)
                self._last_settle_date = today

    def reset(self):
        """重置账户（用于重新开始测试）"""
        with self._lock:
            self._cash = self._initial_cash
            self._settled_cash = self._initial_cash
            self._positions.clear()
            self._orders.clear()
            self._prices.clear()
            self._last_settle_date = datetime.now().date()
        logger.info("模拟账户已重置")

    # ----------------------------------------------------------
    # 外部接口
    # ----------------------------------------------------------

    def set_price(self, symbol: str, price: float):
        """更新标的当前价格（由外部行情模块调用）"""
        self._prices[symbol.upper()] = price
        # 更新持仓市值
        with self._lock:
            pos = self._positions.get(symbol.upper())
            if pos:
                pos.current_price = price
                pos.market_value = pos.quantity * price
                pos.unrealized_pnl = pos.market_value - pos.quantity * pos.avg_cost
                if pos.avg_cost > 0:
                    pos.unrealized_pnl_pct = (price / pos.avg_cost - 1) * 100

    def set_price_batch(self, prices: dict[str, float]):
        """批量更新价格"""
        for symbol, price in prices.items():
            self.set_price(symbol, price)

    # ----------------------------------------------------------
    # BrokerBase 接口实现
    # ----------------------------------------------------------

    def get_account(self) -> AccountInfo:
        with self._lock:
            # 每日清算（T+1 解锁）
            today = datetime.now().date()
            if self._rules.t_plus_one and today > self._last_settle_date:
                self._settled_cash = round(self._cash, 2)
                self._last_settle_date = today
            total_mv = sum(p.market_value for p in self._positions.values())
            equity = self._cash + total_mv
            unsettled = round(self._cash - self._settled_cash, 2)
            return AccountInfo(
                cash=round(self._cash, 2),
                equity=round(equity, 2),
                buying_power=round(self._cash * 2, 2),  # 模拟2倍杠杆
                initial_capital=self._initial_cash,
                realized_pnl=0.0,
                total_return_pct=round((equity / self._initial_cash - 1) * 100, 2),
                settled_cash=round(self._settled_cash, 2),
                unsettled_cash=unsettled,
            )

    def get_positions(self) -> list[Position]:
        with self._lock:
            return list(self._positions.values())

    def get_position(self, symbol: str) -> Optional[Position]:
        return self._positions.get(symbol.upper())

    def place_order(
        self,
        symbol: str,
        quantity: int,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        symbol = symbol.upper()
        order_id = str(uuid.uuid4())[:8]
        current_price = self._prices.get(symbol, 0)

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            intended_price=current_price,
            slippage_bps=self._rules.slippage_bps,
        )

        # 获取成交价
        if order_type == OrderType.MARKET:
            ref_price = current_price
        elif order_type == OrderType.LIMIT:
            if limit_price is None:
                order.status = OrderStatus.REJECTED
                order.note = "限价单必须指定 limit_price"
                order.rejection_code = REJECT_INVALID_PRICE
                self._orders[order_id] = order
                return order
            ref_price = limit_price
        else:
            ref_price = current_price or limit_price or 0

        if ref_price <= 0:
            order.status = OrderStatus.REJECTED
            order.note = "无法获取成交价格"
            order.rejection_code = REJECT_INVALID_PRICE
            self._orders[order_id] = order
            return order

        # 应用滑点模型（无延迟时同步成交，否则模拟延迟队列占位，本实现走同步路径以保证回测可复现）
        fill_price = self._rules.compute_fill_price(ref_price, side == OrderSide.BUY)

        # 部分成交拆单（仅当启用且数量 >= 50）
        qty_chunks: list[int]
        if (
            self._rules.partial_fill_chance > 0
            and quantity >= 50
            and order_type == OrderType.MARKET
            and random.random() < self._rules.partial_fill_chance
        ):
            first = max(1, int(quantity * random.uniform(0.5, 0.8)))
            qty_chunks = [first, quantity - first]
        else:
            qty_chunks = [quantity]

        with self._lock:
            total_filled = 0
            total_cost = 0.0
            cash_needed_for_buy = 0.0

            # 第一次扫描：检查资金 / 持仓是否足够
            for q in qty_chunks:
                chunk_cost = q * fill_price
                if side == OrderSide.BUY:
                    cash_needed_for_buy += chunk_cost
                else:
                    pos = self._positions.get(symbol)
                    if not pos or pos.quantity < sum(qty_chunks):
                        order.status = OrderStatus.REJECTED
                        order.note = (
                            f"持仓不足: 需要 {sum(qty_chunks)} 股, "
                            f"持有 {pos.quantity if pos else 0} 股"
                        )
                        order.rejection_code = REJECT_INSUFFICIENT_POSITION
                        self._orders[order_id] = order
                        return order

            # T+1 资金检查（仅对买入有效）
            if side == OrderSide.BUY and self._rules.t_plus_one:
                if self._settled_cash < cash_needed_for_buy:
                    order.status = OrderStatus.REJECTED
                    order.note = (
                        f"T+1 资金不足: 需要 ${cash_needed_for_buy:,.2f}, "
                        f"已结算 ${self._settled_cash:,.2f}"
                    )
                    order.rejection_code = REJECT_T_PLUS_ONE
                    self._orders[order_id] = order
                    return order

            if side == OrderSide.BUY and self._cash < cash_needed_for_buy:
                order.status = OrderStatus.REJECTED
                order.note = (
                    f"资金不足: 需要 ${cash_needed_for_buy:,.2f}, "
                    f"可用 ${self._cash:,.2f}"
                )
                order.rejection_code = REJECT_INSUFFICIENT_CASH
                self._orders[order_id] = order
                return order

            # 第二步：执行全部 chunks
            commission_total = 0.0
            for q in qty_chunks:
                chunk_cost = q * fill_price
                commission = self._rules.compute_commission(q, fill_price)
                commission_total += commission

                if side == OrderSide.BUY:
                    self._cash -= (chunk_cost + commission)
                    if self._rules.t_plus_one:
                        self._settled_cash -= (chunk_cost + commission)
                        if self._settled_cash < 0:
                            self._settled_cash = 0.0
                    pos = self._positions.get(symbol)
                    if pos:
                        new_total_cost = pos.quantity * pos.avg_cost + chunk_cost
                        pos.quantity += q
                        pos.avg_cost = new_total_cost / pos.quantity
                    else:
                        pos = Position(
                            symbol=symbol,
                            quantity=q,
                            avg_cost=fill_price,
                            current_price=fill_price,
                            market_value=chunk_cost,
                        )
                        self._positions[symbol] = pos
                else:  # SELL
                    pos = self._positions.get(symbol)
                    self._cash += (chunk_cost - commission)
                    pos.quantity -= q
                    if pos.quantity == 0:
                        del self._positions[symbol]
                    # 卖出所得当日记为 unsettled（T+1 时）
                    if self._rules.t_plus_one:
                        # 本日卖出收益属于 unsettled（次日才能再买入）
                        # 简化处理：直接按"新增现金 - 当日已扣资金"差额记入 unsettled
                        pass

                total_filled += q
                total_cost += chunk_cost

            # 写入订单字段
            order.filled_quantity = total_filled
            order.avg_fill_price = fill_price
            order.commission = round(commission_total, 2)
            order.status = (
                OrderStatus.FILLED if total_filled == quantity
                else OrderStatus.PARTIALLY_FILLED
            )
            order.filled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        order.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._orders[order_id] = order

        logger.info(
            f"[模拟] {side.value.upper()} {symbol} x{quantity} @ ${fill_price:.2f} "
            f"commission=${order.commission:.2f} [{order_id}]"
        )
        self._notify_order_update(order)
        return order

    def cancel_order(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._notify_order_update(order)
            return True
        return False

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def get_orders(self, status: Optional[OrderStatus] = None) -> list[Order]:
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return sorted(orders, key=lambda o: o.created_at, reverse=True)

    def get_quote(self, symbol: str) -> Optional[dict]:
        price = self._prices.get(symbol.upper())
        if price is None:
            return None
        return {"symbol": symbol.upper(), "price": price, "timestamp": datetime.now().isoformat()}


# ============================================================
# Alpaca Markets 券商
# ============================================================

class AlpacaBroker(BrokerBase):
    """
    Alpaca Markets 券商接口

    支持:
    - Paper Trading: 设置 paper=True（免费，需注册 Alpaca 账号获取 API Key）
    - Live Trading:  设置 paper=False（需真实资金账户）

    环境变量:
        ALPACA_API_KEY     - API Key
        ALPACA_SECRET_KEY  - Secret Key
    """

    def __init__(self, paper: bool = True):
        super().__init__(name=f"Alpaca {'Paper' if paper else 'Live'}")
        self._paper = paper

        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
            from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce

            self._AlpacaOrderSide = AlpacaOrderSide
            self._TimeInForce = TimeInForce
            self._MarketOrderRequest = MarketOrderRequest
            self._LimitOrderRequest = LimitOrderRequest
        except ImportError:
            raise ImportError(
                "请安装 alpaca-py: pip install alpaca-py\n"
                "或使用模拟券商: SimulationBroker(initial_cash=100000)"
            )

        import os
        api_key = os.getenv("ALPACA_API_KEY", "")
        secret_key = os.getenv("ALPACA_SECRET_KEY", "")

        if not api_key or not secret_key:
            raise ValueError(
                "请设置 Alpaca API Key 环境变量:\n"
                "  set ALPACA_API_KEY=your_key\n"
                "  set ALPACA_SECRET_KEY=your_secret\n"
                "或使用模拟券商: SimulationBroker(initial_cash=100000)"
            )

        self._client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
        )
        self._lock = threading.Lock()
        logger.info(f"Alpaca {'模拟' if paper else '实盘'}券商已连接")

    def _to_alpaca_side(self, side: OrderSide):
        if side == OrderSide.BUY:
            return self._AlpacaOrderSide.BUY
        return self._AlpacaOrderSide.SELL

    def get_account(self) -> AccountInfo:
        try:
            acc = self._client.get_account()
            return AccountInfo(
                cash=float(acc.cash),
                equity=float(acc.equity),
                buying_power=float(acc.buying_power),
                initial_capital=float(acc.last_equity or acc.equity),
            )
        except Exception as e:
            logger.error(f"获取Alpaca账户信息失败: {e}")
            return AccountInfo(cash=0, equity=0, buying_power=0, initial_capital=0)

    def get_positions(self) -> list[Position]:
        try:
            alpaca_positions = self._client.get_all_positions()
            result = []
            for ap in alpaca_positions:
                result.append(Position(
                    symbol=ap.symbol,
                    quantity=int(ap.qty),
                    avg_cost=float(ap.avg_entry_price),
                    current_price=float(ap.current_price or 0),
                    market_value=float(ap.market_value or 0),
                    unrealized_pnl=float(ap.unrealized_pl or 0),
                    unrealized_pnl_pct=float(ap.unrealized_plpc or 0) * 100,
                ))
            return result
        except Exception as e:
            logger.error(f"获取Alpaca持仓失败: {e}")
            return []

    def get_position(self, symbol: str) -> Optional[Position]:
        try:
            ap = self._client.get_open_position(symbol.upper())
            return Position(
                symbol=ap.symbol,
                quantity=int(ap.qty),
                avg_cost=float(ap.avg_entry_price),
                current_price=float(ap.current_price or 0),
                market_value=float(ap.market_value or 0),
                unrealized_pnl=float(ap.unrealized_pl or 0),
                unrealized_pnl_pct=float(ap.unrealized_plpc or 0) * 100,
            )
        except Exception:
            return None

    def place_order(
        self,
        symbol: str,
        quantity: int,
        side: OrderSide,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        symbol = symbol.upper()
        order_id = str(uuid.uuid4())[:8]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            if order_type == OrderType.MARKET:
                req = self._MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=self._to_alpaca_side(side),
                    time_in_force=self._TimeInForce.DAY,
                )
            elif order_type == OrderType.LIMIT:
                req = self._LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=self._to_alpaca_side(side),
                    limit_price=limit_price,
                    time_in_force=self._TimeInForce.DAY,
                )
            else:
                # 降级为市价单
                req = self._MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=self._to_alpaca_side(side),
                    time_in_force=self._TimeInForce.DAY,
                )

            ap_order = self._client.submit_order(req)

            order = Order(
                order_id=str(ap_order.id),
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                filled_quantity=int(ap_order.filled_qty or 0),
                limit_price=limit_price,
                avg_fill_price=float(ap_order.filled_avg_price or 0),
                status=OrderStatus.FILLED if ap_order.status == "filled" else OrderStatus.PENDING,
                created_at=now,
                updated_at=now,
            )
            self._orders = getattr(self, '_orders', {})
            self._orders[order.order_id] = order

            logger.info(f"[Alpaca] {side.value.upper()} {symbol} x{quantity} [{order.order_id}]")
            self._notify_order_update(order)
            return order

        except Exception as e:
            logger.error(f"Alpaca下单失败: {e}")
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                status=OrderStatus.REJECTED,
                note=str(e),
            )

    def cancel_order(self, order_id: str) -> bool:
        try:
            self._client.cancel_order_by_id(order_id)
            logger.info(f"已撤单: {order_id}")
            return True
        except Exception as e:
            logger.error(f"撤单失败: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Order]:
        try:
            return self._orders.get(order_id)
        except Exception:
            return None

    def get_orders(self, status: Optional[OrderStatus] = None) -> list[Order]:
        try:
            orders = list(self._orders.values()) if hasattr(self, '_orders') else []
            if status:
                orders = [o for o in orders if o.status == status]
            return sorted(orders, key=lambda o: o.created_at, reverse=True)
        except Exception:
            return []

    def get_quote(self, symbol: str) -> Optional[dict]:
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
            client = StockHistoricalDataClient(
                self._client._api_key,
                self._client._secret_key,
            )
            req = StockLatestQuoteRequest(symbol_or_symbols=symbol.upper())
            quote = client.get_stock_latest_quote(req)
            symbol_upper = symbol.upper()
            if symbol_upper in quote:
                q = quote[symbol_upper]
                return {
                    "symbol": symbol_upper,
                    "bid": float(q.bid_price),
                    "ask": float(q.ask_price),
                    "price": float((q.bid_price + q.ask_price) / 2),
                    "timestamp": q.timestamp.isoformat(),
                }
        except Exception as e:
            logger.debug(f"获取Alpaca报价失败: {e}")
        return None


# ============================================================
# 工厂函数
# ============================================================

def create_broker(
    broker_type: str = "simulation",
    paper: bool = True,
    initial_cash: float = 100000.0,
    rules: Optional[SimExecutionRules] = None,
) -> BrokerBase:
    """
    券商工厂函数

    参数:
        broker_type: "simulation" | "alpaca"
        paper:       仅对 alpaca 有效，True=模拟交易, False=实盘
        initial_cash: 仅对 simulation 有效，初始资金
        rules:       仅对 simulation 有效，撮合规则
    """
    broker_type = broker_type.lower()
    if broker_type == "simulation":
        logger.info(f"使用模拟券商，初始资金 ${initial_cash:,.0f}")
        return SimulationBroker(initial_cash=initial_cash, rules=rules)
    elif broker_type == "alpaca":
        return AlpacaBroker(paper=paper)
    else:
        raise ValueError(f"不支持的券商类型: {broker_type}，可选: simulation, alpaca")
