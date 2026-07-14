# -*- coding: utf-8 -*-
"""
订单执行引擎

负责:
- 将策略信号转化为实际订单
- 执行前风险检查
- 订单状态追踪
- 止损止盈自动执行
"""

import logging
import threading
import time
from typing import Optional, Callable

from trading.broker import BrokerBase, OrderSide, OrderType, OrderStatus, Order
from trading.strategy import Signal, SignalAction
from trading.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class OrderExecutor:
    """
    订单执行器

    作为策略信号和券商之间的中介层：
    1. 接收策略信号
    2. 执行风险检查
    3. 通过券商下单
    4. 追踪订单状态
    """

    def __init__(self, broker: BrokerBase, risk_manager: RiskManager):
        self.broker = broker
        self.risk = risk_manager
        self._signal_callback: Optional[Callable] = None
        self._order_history: list[Order] = []
        self._lock = threading.Lock()

        logger.info("订单执行器已初始化")

    # ----------------------------------------------------------
    # 核心接口
    # ----------------------------------------------------------

    def execute_signal(self, signal: Signal) -> Optional[Order]:
        """
        执行交易信号

        参数:
            signal: 策略生成的交易信号

        返回:
            Order 对象，若被风控拦截则返回 None
        """
        if not signal.is_trade_signal:
            logger.debug(f"{signal.symbol}: 无交易信号，跳过")
            return None

        symbol = signal.symbol.upper()
        price = signal.price
        account = self.broker.get_account()
        positions = self.broker.get_positions()

        if signal.action == SignalAction.BUY:
            return self._execute_buy(signal, account, positions)
        elif signal.action == SignalAction.SELL:
            return self._execute_sell(signal, account, positions)

        return None

    def _execute_buy(self, signal: Signal, account, positions) -> Optional[Order]:
        """执行买入"""
        symbol = signal.symbol.upper()
        price = signal.price

        if price <= 0:
            logger.warning(f"{symbol}: 价格无效 ${price}，跳过买入")
            return None

        # 计算仓位
        quantity = self.risk.calculate_position_size(
            price=price,
            account_equity=account.equity,
            risk_per_trade=0.02,
        )

        if quantity <= 0:
            logger.warning(f"{symbol}: 计算仓位为0，跳过买入")
            return None

        # 风险检查
        check = self.risk.check_buy(
            symbol=symbol,
            quantity=quantity,
            price=price,
            positions=positions,
            account_equity=account.equity,
            account_cash=account.cash,
        )

        if not check.allowed:
            logger.warning(f"{symbol}: 买入风控拦截 - {check.reason}")
            if check.suggested_quantity > 0 and check.suggested_quantity != quantity:
                # 尝试降级数量重试
                check2 = self.risk.check_buy(
                    symbol=symbol, quantity=check.suggested_quantity,
                    price=price, positions=positions,
                    account_equity=account.equity, account_cash=account.cash,
                )
                if check2.allowed:
                    quantity = check.suggested_quantity
                    logger.info(f"{symbol}: 调整买入数量至 {quantity}")
                else:
                    return None
            else:
                return None

        # 下单
        order = self.broker.place_order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
        )

        if order.status == OrderStatus.FILLED:
            self.risk.record_trade(symbol)
            logger.info(f"[成交] BUY {symbol} x{quantity} @ ${order.avg_fill_price:.2f}"
                        f" 原因: {signal.reason}")
        else:
            logger.warning(f"[失败] BUY {symbol} - {order.note}")

        self._add_to_history(order)
        return order

    def _execute_sell(self, signal: Signal, account, positions) -> Optional[Order]:
        """执行卖出"""
        symbol = signal.symbol.upper()
        price = signal.price

        position = self.broker.get_position(symbol)
        if position is None or position.quantity <= 0:
            logger.debug(f"{symbol}: 无持仓，跳过卖出信号")
            return None

        quantity = position.quantity  # 全仓卖出

        # 风险检查
        check = self.risk.check_sell(
            symbol=symbol,
            quantity=quantity,
            price=price,
            positions=positions,
        )

        if not check.allowed:
            logger.warning(f"{symbol}: 卖出风控拦截 - {check.reason}")
            return None

        # 下单
        order = self.broker.place_order(
            symbol=symbol,
            quantity=quantity,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
        )

        if order.status == OrderStatus.FILLED:
            pnl = (order.avg_fill_price - position.avg_cost) * quantity
            pnl_pct = (order.avg_fill_price / position.avg_cost - 1) * 100
            self.risk.record_trade(symbol, pnl)
            logger.info(f"[成交] SELL {symbol} x{quantity} @ ${order.avg_fill_price:.2f}"
                        f" PnL=${pnl:,.2f}({pnl_pct:+.2f}%) 原因: {signal.reason}")
        else:
            logger.warning(f"[失败] SELL {symbol} - {order.note}")

        self._add_to_history(order)
        return order

    # ----------------------------------------------------------
    # 止损止盈检查（与策略信号独立）
    # ----------------------------------------------------------

    def check_stop_conditions(self) -> list[Order]:
        """
        检查所有持仓的止损止盈条件

        返回:
            触发的止损止盈订单列表
        """
        triggered_orders = []
        positions = self.broker.get_positions()

        for pos in positions:
            price = None
            # 获取当前价格
            quote = self.broker.get_quote(pos.symbol)
            if quote and quote.get("price"):
                price = quote["price"]
            else:
                price = pos.current_price

            if not price or price <= 0:
                continue

            reason = self.risk.check_stop_conditions(
                symbol=pos.symbol,
                current_price=price,
                position=pos,
            )

            if reason:
                logger.info(f"[止损止盈] {pos.symbol}: {reason}")
                order = self.broker.place_order(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                )
                if order.status == OrderStatus.FILLED:
                    pnl = (order.avg_fill_price - pos.avg_cost) * pos.quantity
                    self.risk.record_trade(pos.symbol, pnl)
                triggered_orders.append(order)
                self._add_to_history(order)

        return triggered_orders

    # ----------------------------------------------------------
    # 工具方法
    # ----------------------------------------------------------

    def _add_to_history(self, order: Order):
        """记录订单到历史"""
        with self._lock:
            self._order_history.append(order)
            # 最多保留最近500条
            if len(self._order_history) > 500:
                self._order_history = self._order_history[-500:]

    def get_order_history(self, limit: int = 50) -> list[Order]:
        """获取最近的订单历史"""
        with self._lock:
            return list(reversed(self._order_history[-limit:]))

    def set_signal_callback(self, callback: Callable):
        """设置信号执行回调（通知GUI更新）"""
        self._signal_callback = callback
