# -*- coding: utf-8 -*-
"""
模拟撮合规则（SimExecutionRules）

定义 SimulationBroker 在回测 / 模拟盘中如何"模拟真实市场"：
- 手续费：每股 / 最低
- 滑点：基点（1 bps = 0.01%）
- 撮合延迟：毫秒
- 部分成交概率
- T+1 资金规则
- 仅交易时段约束

默认 `DEFAULT_RULES` 等价于旧版本（无手续费、无滑点、无延迟、无 T+1），
以保证现有调用方完全向后兼容。
"""

from dataclasses import dataclass


@dataclass
class SimExecutionRules:
    """
    模拟撮合规则

    字段:
        commission_per_share:  每股佣金（美元），0 表示免佣金
        min_commission:         最低单笔佣金（美元）
        slippage_bps:           滑点（基点）。买入 fill = ref * (1 + bps/10000)，卖出反之
        fill_delay_ms:          撮合延迟（毫秒）；0 表示立即成交（默认关闭延迟以兼容旧版）
        partial_fill_chance:    拆单概率 [0.0, 1.0]
        t_plus_one:             卖出资金次日才可买入（默认 False，保持向后兼容）
        market_hours_only:      仅允许在美股交易时段下单（默认 False）
    """

    commission_per_share: float = 0.0
    min_commission: float = 0.0
    slippage_bps: float = 0.0
    fill_delay_ms: int = 0
    partial_fill_chance: float = 0.0
    t_plus_one: bool = False
    market_hours_only: bool = False

    def compute_fill_price(self, ref_price: float, side_is_buy: bool) -> float:
        """根据滑点模型计算成交价。"""
        if ref_price <= 0:
            return ref_price
        direction = 1.0 if side_is_buy else -1.0
        return round(ref_price * (1.0 + direction * self.slippage_bps / 10000.0), 4)

    def compute_commission(self, quantity: int, fill_price: float) -> float:
        """计算单笔成交的佣金。"""
        per_share = quantity * self.commission_per_share
        return round(max(per_share, self.min_commission), 2)


# 向后兼容默认：完全关闭手续费、滑点、延迟、T+1
DEFAULT_RULES = SimExecutionRules()
