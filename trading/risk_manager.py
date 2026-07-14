# -*- coding: utf-8 -*-
"""
风险管理系统

核心功能:
- 仓位管理: 单只股票最大仓位、总仓位限制
- 止损止盈: 固定比例止损、追踪止损、目标止盈
- 资金限制: 单日最大亏损限制、最大回撤限制
- 交易频率: 冷却时间、单日最大交易次数
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """风险参数配置"""
    # 仓位限制
    max_position_pct: float = 0.25       # 单只股票最大仓位占比（25%）
    max_total_position_pct: float = 0.80 # 总仓位上限（80%）
    max_positions_count: int = 8         # 最大持仓数量

    # 止损止盈（相对成本价）
    stop_loss_pct: float = -8.0          # 固定止损 -8%
    take_profit_pct: float = 20.0        # 固定止盈 +20%
    trailing_stop_pct: float = -5.0      # 追踪止损 从最高点回落-5%

    # 资金限制
    max_daily_loss: float = 5000.0       # 单日最大亏损额
    max_drawdown_pct: float = -15.0      # 最大回撤限制

    # 交易频率
    cooldown_seconds: int = 60           # 同标的交易冷却时间（秒）
    max_daily_trades: int = 20           # 单日最大交易次数

    # 单笔交易
    max_order_value: float = 50000.0     # 单笔最大订单金额
    min_order_value: float = 500.0       # 单笔最小订单金额

    # H 任务：ATR 动态止损（带默认值以保持向后兼容）
    atr_multiple: float = 2.0
    atr_period: int = 14
    use_atr_stop: bool = False


@dataclass
class RiskCheckResult:
    """风险检查结果"""
    allowed: bool = True
    reason: str = ""
    suggested_quantity: int = 0


class RiskManager:
    """
    风险管理器

    在下单前执行多层风险检查，确保交易符合风控规则。
    """

    def __init__(self, limits: RiskLimits = None):
        self.limits = limits or RiskLimits()

        # 运行时状态
        self._daily_pnl: float = 0.0
        self._daily_trades: int = 0
        self._last_trade_time: dict[str, float] = {}  # symbol -> timestamp
        self._peak_equity: float = 0.0
        self._current_equity: float = 0.0
        self._peak_prices: dict[str, float] = {}  # symbol -> 持仓期间最高价

        logger.info("风险管理器已初始化")

    # ----------------------------------------------------------
    # 核心接口：下单前检查
    # ----------------------------------------------------------

    def check_buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        positions: list,
        account_equity: float,
        account_cash: float,
    ) -> RiskCheckResult:
        """
        检查买入是否合规

        参数:
            symbol:        股票代码
            quantity:      拟买入数量
            price:         当前价格
            positions:     当前持仓列表 (Position 对象)
            account_equity: 账户总资产
            account_cash:   账户现金
        """
        symbol = symbol.upper()
        order_value = quantity * price

        self._current_equity = account_equity
        if account_equity > self._peak_equity:
            self._peak_equity = account_equity

        # 1. 单笔金额检查
        if order_value > self.limits.max_order_value:
            suggested = int(self.limits.max_order_value / price)
            return RiskCheckResult(
                False,
                f"单笔订单金额 ${order_value:,.0f} 超过上限 ${self.limits.max_order_value:,.0f}",
                suggested,
            )
        if order_value < self.limits.min_order_value:
            return RiskCheckResult(
                False,
                f"单笔订单金额 ${order_value:,.0f} 低于下限 ${self.limits.min_order_value:,.0f}",
            )

        # 2. 资金检查
        if order_value > account_cash:
            return RiskCheckResult(
                False,
                f"资金不足: 需要 ${order_value:,.0f}, 可用 ${account_cash:,.0f}",
            )

        # 3. 单只股票仓位检查
        position_value = 0.0
        for pos in positions:
            if pos.symbol == symbol:
                position_value = pos.market_value
                break
        total_after_buy = position_value + order_value
        position_pct_after = total_after_buy / account_equity if account_equity > 0 else 1
        if position_pct_after > self.limits.max_position_pct:
            max_value = account_equity * self.limits.max_position_pct - position_value
            suggested = int(max_value / price) if price > 0 else 0
            return RiskCheckResult(
                False,
                f"单只股票仓位 {position_pct_after:.0%} 超过上限 {self.limits.max_position_pct:.0%}",
                max(0, suggested),
            )

        # 4. 总仓位检查
        total_position_value = sum(p.market_value for p in positions)
        total_pct_after = (total_position_value + order_value) / account_equity if account_equity > 0 else 1
        if total_pct_after > self.limits.max_total_position_pct:
            return RiskCheckResult(
                False,
                f"总仓位 {total_pct_after:.0%} 超过上限 {self.limits.max_total_position_pct:.0%}",
            )

        # 5. 持仓数量检查（仅新开仓时检查）
        has_existing = any(p.symbol == symbol for p in positions)
        if not has_existing and len(positions) >= self.limits.max_positions_count:
            return RiskCheckResult(
                False,
                f"持仓数量 {len(positions)} 已达上限 {self.limits.max_positions_count}",
            )

        # 6. 日交易次数检查
        if self._daily_trades >= self.limits.max_daily_trades:
            return RiskCheckResult(
                False,
                f"今日交易次数 {self._daily_trades} 已达上限 {self.limits.max_daily_trades}",
            )

        # 7. 冷却时间检查
        last_time = self._last_trade_time.get(symbol, 0)
        elapsed = time.time() - last_time
        if elapsed < self.limits.cooldown_seconds:
            remaining = self.limits.cooldown_seconds - int(elapsed)
            return RiskCheckResult(
                False,
                f"请等待 {remaining} 秒后再交易 {symbol}",
            )

        # 8. 日亏损限制
        if self._daily_pnl < -self.limits.max_daily_loss:
            return RiskCheckResult(
                False,
                f"今日亏损 ${abs(self._daily_pnl):,.0f} 超过限制 ${self.limits.max_daily_loss:,.0f}",
            )

        # 全部通过
        return RiskCheckResult(True, "风险检查通过", quantity)

    def check_sell(
        self,
        symbol: str,
        quantity: int,
        price: float,
        positions: list,
    ) -> RiskCheckResult:
        """
        检查卖出是否合规

        参数:
            symbol:    股票代码
            quantity:  拟卖出数量
            price:     当前价格
            positions: 当前持仓列表
        """
        symbol = symbol.upper()

        # 1. 持仓检查
        position = None
        for pos in positions:
            if pos.symbol == symbol:
                position = pos
                break

        if position is None:
            return RiskCheckResult(False, f"没有 {symbol} 的持仓")

        if position.quantity < quantity:
            return RiskCheckResult(
                False,
                f"持仓不足: 需要 {quantity} 股, 持有 {position.quantity} 股",
                position.quantity,
            )

        # 2. 日交易次数检查
        if self._daily_trades >= self.limits.max_daily_trades:
            return RiskCheckResult(
                False,
                f"今日交易次数已达上限 {self.limits.max_daily_trades}",
            )

        return RiskCheckResult(True, "卖出检查通过", quantity)

    # ----------------------------------------------------------
    # 止损止盈检查
    # ----------------------------------------------------------

    def check_stop_conditions(
        self,
        symbol: str,
        current_price: float,
        position: object,
        atr: Optional[float] = None,
    ) -> Optional[str]:
        """
        检查持仓是否触发止损/止盈

        参数:
            symbol:        股票代码
            current_price: 当前价格
            position:      持仓对象 (含 avg_cost, current_price 等)
            atr:           可选 ATR；若启用 use_atr_stop 且 atr 提供，则按 ATR 止损

        返回:
            None 表示无需操作；字符串表示触发的原因
        """
        if position is None or position.quantity <= 0:
            return None

        symbol = symbol.upper()
        avg_cost = position.avg_cost
        if avg_cost <= 0:
            return None

        # 0. ATR 动态止损（H 任务：可选）
        if getattr(self.limits, "use_atr_stop", False) and atr:
            dynamic_stop = avg_cost - float(self.limits.atr_multiple) * atr
            if current_price <= dynamic_stop:
                return (
                    f"触发 ATR 动态止损: ATR={atr:.2f} × {self.limits.atr_multiple} "
                    f"≈ {dynamic_stop:.2f}"
                )

        pnl_pct = (current_price / avg_cost - 1) * 100

        # 1. 固定止损
        if pnl_pct <= self.limits.stop_loss_pct:
            return f"触发固定止损: {pnl_pct:.1f}% <= {self.limits.stop_loss_pct}%"

        # 2. 固定止盈
        if pnl_pct >= self.limits.take_profit_pct:
            return f"触发目标止盈: {pnl_pct:.1f}% >= {self.limits.take_profit_pct}%"

        # 3. 追踪止损
        peak = self._peak_prices.get(symbol, avg_cost)
        if current_price > peak:
            self._peak_prices[symbol] = current_price
        else:
            drawdown_from_peak = (current_price / peak - 1) * 100
            if drawdown_from_peak <= self.limits.trailing_stop_pct:
                return f"触发追踪止损: 从最高 ${peak:.2f} 回落 {drawdown_from_peak:.1f}%"

        return None

    # ----------------------------------------------------------
    # 仓位计算
    # ----------------------------------------------------------

    def calculate_position_size(
        self,
        price: float,
        account_equity: float,
        risk_per_trade: float = 0.02,
        stop_loss_pct: Optional[float] = None,
    ) -> int:
        """
        计算建议仓位大小

        基于凯利公式变体：仓位 = (风险资金) / (止损幅度 * 价格)

        参数:
            price:          当前价格
            account_equity: 账户总资产
            risk_per_trade: 单笔风险占比（默认2%）
            stop_loss_pct:  止损百分比（默认使用配置值）

        返回:
            建议买入股数
        """
        sl_pct = stop_loss_pct or abs(self.limits.stop_loss_pct / 100)
        risk_amount = account_equity * risk_per_trade
        risk_per_share = price * sl_pct

        if risk_per_share <= 0:
            return 0

        shares = int(risk_amount / risk_per_share)

        # 确保不超过单只股票仓位上限
        max_shares = int(account_equity * self.limits.max_position_pct / price)
        shares = min(shares, max_shares)

        return max(1, shares)  # 至少1股

    # ----------------------------------------------------------
    # 状态管理
    # ----------------------------------------------------------

    def record_trade(self, symbol: str, pnl: float = 0):
        """记录一次交易"""
        self._daily_trades += 1
        self._daily_pnl += pnl
        self._last_trade_time[symbol.upper()] = time.time()

    def reset_daily(self):
        """重置日计数器（每日零点调用）"""
        self._daily_pnl = 0.0
        self._daily_trades = 0
        self._last_trade_time.clear()
        logger.info("日风险计数器已重置")

    def update_equity(self, equity: float):
        """更新当前资产（用于最大回撤追踪）"""
        self._current_equity = equity
        if equity > self._peak_equity:
            self._peak_equity = equity

    def get_status(self) -> dict:
        """获取风险管理状态"""
        drawdown = 0.0
        if self._peak_equity > 0:
            drawdown = (self._current_equity / self._peak_equity - 1) * 100

        return {
            "daily_trades": self._daily_trades,
            "max_daily_trades": self.limits.max_daily_trades,
            "daily_pnl": round(self._daily_pnl, 2),
            "max_daily_loss": self.limits.max_daily_loss,
            "current_equity": round(self._current_equity, 2),
            "peak_equity": round(self._peak_equity, 2),
            "drawdown_pct": round(drawdown, 2),
            "max_drawdown_pct": self.limits.max_drawdown_pct,
        }
