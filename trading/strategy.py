# -*- coding: utf-8 -*-
"""
交易策略引擎

设计模式: 策略模式 (Strategy Pattern)
所有策略继承自 StrategyBase，实现 generate_signal() 方法。

内置策略:
- MACrossoverStrategy:      MACD 金叉/死叉策略
- RSIReversalStrategy:      RSI 超买超卖反转策略
- MATrendStrategy:          均线趋势跟踪策略
- MultiIndicatorStrategy:   多指标综合策略（推荐）
- BollingerBreakoutStrategy: 布林带突破策略
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """交易信号"""
    symbol: str
    action: SignalAction
    strength: float = 0.0  # 信号强度 0~1
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    price: float = 0.0
    contributors: list[str] = field(default_factory=list)   # 加权来源（H 任务）

    @property
    def is_trade_signal(self) -> bool:
        return self.action != SignalAction.HOLD


# ============================================================
# 策略基类
# ============================================================

class StrategyBase(ABC):
    """策略抽象基类"""

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    @abstractmethod
    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        """
        根据历史数据生成交易信号

        参数:
            symbol: 股票代码
            df:     含 OHLCV 和技术指标的 DataFrame

        返回:
            Signal 对象
        """
        ...

    def _get_last(self, df: pd.DataFrame, col: str, default=None):
        """安全获取最新值"""
        if df is None or df.empty or col not in df.columns:
            return default
        val = df[col].iloc[-1]
        if isinstance(val, float) and np.isnan(val):
            return default
        return val

    def __repr__(self):
        return f"{self.name}(enabled={self.enabled})"


# ============================================================
# MACD 金叉/死叉策略
# ============================================================

class MACrossoverStrategy(StrategyBase):
    """
    MACD 金叉死叉策略

    买入: DIF 上穿 DEA（金叉）
    卖出: DIF 下穿 DEA（死叉）
    """

    def __init__(self):
        super().__init__("MACD金叉死叉")

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        if df is None or df.empty or len(df) < 2:
            return Signal(symbol, SignalAction.HOLD, reason="数据不足")

        if "DIF" not in df.columns or "DEA" not in df.columns:
            return Signal(symbol, SignalAction.HOLD, reason="缺少MACD指标")

        last_dif = self._get_last(df, "DIF")
        last_dea = self._get_last(df, "DEA")
        prev_dif = df["DIF"].iloc[-2] if len(df) >= 2 else None
        prev_dea = df["DEA"].iloc[-2] if len(df) >= 2 else None

        if any(v is None or (isinstance(v, float) and np.isnan(v))
               for v in [last_dif, last_dea, prev_dif, prev_dea]):
            return Signal(symbol, SignalAction.HOLD, reason="指标数据无效")

        close = self._get_last(df, "Close", 0)

        # 金叉
        if prev_dif <= prev_dea and last_dif > last_dea:
            hist = self._get_last(df, "MACD_HIST", 0)
            strength = min(abs(hist) / 5, 1.0) if hist else 0.5
            return Signal(symbol, SignalAction.BUY, strength=strength,
                          reason=f"MACD金叉 DIF={last_dif:.2f} > DEA={last_dea:.2f}", price=close)

        # 死叉
        if prev_dif >= prev_dea and last_dif < last_dea:
            return Signal(symbol, SignalAction.SELL, strength=0.7,
                          reason=f"MACD死叉 DIF={last_dif:.2f} < DEA={last_dea:.2f}", price=close)

        return Signal(symbol, SignalAction.HOLD, reason="无MACD交叉信号", price=close)


# ============================================================
# RSI 超买超卖策略
# ============================================================

class RSIReversalStrategy(StrategyBase):
    """
    RSI 超买超卖反转策略

    买入: RSI < oversold_threshold（默认30，超卖反弹）
    卖出: RSI > overbought_threshold（默认70，超买回落）
    """

    def __init__(self, oversold: float = 30, overbought: float = 70):
        super().__init__(f"RSI反转({oversold}/{overbought})")
        self.oversold = oversold
        self.overbought = overbought

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        if df is None or df.empty:
            return Signal(symbol, SignalAction.HOLD, reason="数据不足")

        rsi = self._get_last(df, "RSI")
        if rsi is None or np.isnan(rsi):
            return Signal(symbol, SignalAction.HOLD, reason="缺少RSI指标")

        close = self._get_last(df, "Close", 0)

        if rsi < self.oversold:
            strength = (self.oversold - rsi) / self.oversold
            return Signal(symbol, SignalAction.BUY, strength=min(strength, 1.0),
                          reason=f"RSI超卖={rsi:.1f} < {self.oversold}", price=close)

        if rsi > self.overbought:
            strength = (rsi - self.overbought) / (100 - self.overbought)
            return Signal(symbol, SignalAction.SELL, strength=min(strength, 1.0),
                          reason=f"RSI超买={rsi:.1f} > {self.overbought}", price=close)

        return Signal(symbol, SignalAction.HOLD, reason=f"RSI中性={rsi:.1f}", price=close)


# ============================================================
# 均线趋势策略
# ============================================================

class MATrendStrategy(StrategyBase):
    """
    均线趋势跟踪策略

    买入: MA5 > MA20 且 价格在 MA20 上方（上升趋势确认）
    卖出: MA5 < MA20 且 价格在 MA20 下方（下降趋势确认）

    额外过滤: 价格必须在 MA60 上方才买入（中长期多头保护）
    """

    def __init__(self):
        super().__init__("均线趋势跟踪")

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        if df is None or df.empty:
            return Signal(symbol, SignalAction.HOLD, reason="数据不足")

        ma5 = self._get_last(df, "MA5")
        ma20 = self._get_last(df, "MA20")
        ma60 = self._get_last(df, "MA60")
        close = self._get_last(df, "Close", 0)

        if any(v is None or (isinstance(v, float) and np.isnan(v)) for v in [ma5, ma20]):
            return Signal(symbol, SignalAction.HOLD, reason="均线数据不足", price=close)

        has_ma60 = ma60 is not None and not (isinstance(ma60, float) and np.isnan(ma60))

        # 买入：短期均线上穿长期均线 + 价格确认
        if ma5 > ma20 and close > ma20:
            if has_ma60 and close < ma60:
                return Signal(symbol, SignalAction.HOLD, reason=f"价格低于MA60", price=close)
            strength = min((ma5 / ma20 - 1) * 10, 1.0) if ma20 > 0 else 0.5
            return Signal(symbol, SignalAction.BUY, strength=max(strength, 0.3),
                          reason=f"MA5({ma5:.2f}) > MA20({ma20:.2f})", price=close)

        # 卖出：短期均线下穿长期均线
        if ma5 < ma20 and close < ma20:
            strength = min((1 - ma5 / ma20) * 10, 1.0) if ma20 > 0 else 0.5
            return Signal(symbol, SignalAction.SELL, strength=max(strength, 0.3),
                          reason=f"MA5({ma5:.2f}) < MA20({ma20:.2f})", price=close)

        return Signal(symbol, SignalAction.HOLD,
                      reason=f"均线纠缠 MA5={ma5:.2f} MA20={ma20:.2f}", price=close)


# ============================================================
# 布林带突破策略
# ============================================================

class BollingerBreakoutStrategy(StrategyBase):
    """
    布林带突破策略

    买入: 价格突破上轨（强势突破）
    卖出: 价格跌破中轨（趋势转弱）
    """

    def __init__(self):
        super().__init__("布林带突破")

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        if df is None or df.empty:
            return Signal(symbol, SignalAction.HOLD, reason="数据不足")

        close = self._get_last(df, "Close", 0)
        upper = self._get_last(df, "BOLL_UPPER")
        mid = self._get_last(df, "BOLL_MID")
        lower = self._get_last(df, "BOLL_LOWER")

        if any(v is None or (isinstance(v, float) and np.isnan(v))
               for v in [close, upper, mid, lower]):
            return Signal(symbol, SignalAction.HOLD, reason="布林带数据不足", price=close)

        # 价格突破上轨
        if close > upper:
            return Signal(symbol, SignalAction.BUY, strength=0.6,
                          reason=f"突破布林上轨 {close:.2f} > {upper:.2f}", price=close)

        # 价格跌破下轨 - 超卖反弹信号
        if close < lower:
            return Signal(symbol, SignalAction.BUY, strength=0.4,
                          reason=f"跌破布林下轨反弹机会 {close:.2f} < {lower:.2f}", price=close)

        # 价格跌破中轨（趋势转弱）
        prev_close = df["Close"].iloc[-2] if len(df) >= 2 else None
        if prev_close is not None and prev_close >= mid and close < mid:
            return Signal(symbol, SignalAction.SELL, strength=0.5,
                          reason=f"跌破布林中轨 {close:.2f} < {mid:.2f}", price=close)

        return Signal(symbol, SignalAction.HOLD, price=close)


# ============================================================
# 多指标综合策略（推荐）
# ============================================================

class MultiIndicatorStrategy(StrategyBase):
    """
    多指标综合策略

    使用加权投票机制:
    - MACD:    权重 30%
    - RSI:     权重 25%
    - MA趋势:  权重 25%
    - 布林带:  权重 20%

    综合得分 > 0.5 且无冲突时生成信号
    """

    def __init__(self):
        super().__init__("多指标综合")
        self.macd = MACrossoverStrategy()
        self.rsi = RSIReversalStrategy(oversold=30, overbought=75)
        self.ma = MATrendStrategy()
        self.boll = BollingerBreakoutStrategy()

        self.weights = {
            "macd": 0.30,
            "rsi": 0.25,
            "ma": 0.25,
            "boll": 0.20,
        }

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        if df is None or df.empty:
            return Signal(symbol, SignalAction.HOLD, reason="数据不足")

        close = self._get_last(df, "Close", 0)

        # 采集各策略信号
        signals = {
            "macd": self.macd.generate_signal(symbol, df),
            "rsi": self.rsi.generate_signal(symbol, df),
            "ma": self.ma.generate_signal(symbol, df),
            "boll": self.boll.generate_signal(symbol, df),
        }

        # 计算加权得分
        buy_score = 0.0
        sell_score = 0.0
        buy_reasons = []
        sell_reasons = []

        for name, sig in signals.items():
            w = self.weights[name]
            if sig.action == SignalAction.BUY:
                buy_score += w * sig.strength
                buy_reasons.append(sig.reason)
            elif sig.action == SignalAction.SELL:
                sell_score += w * sig.strength
                sell_reasons.append(sig.reason)

        # 判断最终信号
        net_score = buy_score - sell_score
        threshold = 0.3

        if net_score > threshold and buy_reasons:
            return Signal(symbol, SignalAction.BUY,
                          strength=min(net_score, 1.0),
                          reason="; ".join(buy_reasons), price=close)

        if net_score < -threshold and sell_reasons:
            return Signal(symbol, SignalAction.SELL,
                          strength=min(abs(net_score), 1.0),
                          reason="; ".join(sell_reasons), price=close)

        return Signal(symbol, SignalAction.HOLD,
                      reason=f"信号分散 buy={buy_score:.2f} sell={sell_score:.2f}", price=close)


# ============================================================
# 策略注册表
# ============================================================

STRATEGY_REGISTRY = {
    "macd": MACrossoverStrategy,
    "rsi": RSIReversalStrategy,
    "ma_trend": MATrendStrategy,
    "bollinger": BollingerBreakoutStrategy,
    "multi": MultiIndicatorStrategy,
}


# ============================================================
# H 任务增强策略
# ============================================================

class KDJReversalStrategy(StrategyBase):
    """KDJ 反转策略：金叉买入 / 死叉卖出；J 极端值加分减分。"""

    def __init__(self, oversold: float = 20.0, overbought: float = 80.0):
        super().__init__(name="KDJReversal")
        self.oversold = float(oversold)
        self.overbought = float(overbought)

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        k = self._get_last(df, "K"); d = self._get_last(df, "D"); j = self._get_last(df, "J")
        close = self._get_last(df, "Close", 0.0)
        if k is None or d is None or j is None:
            return Signal(symbol, SignalAction.HOLD, reason="KDJ 指标缺失", price=close or 0.0)
        k_prev = df["K"].iloc[-2] if len(df) >= 2 else k
        d_prev = df["D"].iloc[-2] if len(df) >= 2 else d
        # 金叉：K 上穿 D；死叉：K 下穿 D
        if k_prev <= d_prev and k > d and j < self.overbought:
            strength = 0.55 if j > self.oversold else 0.7
            return Signal(
                symbol, SignalAction.BUY, strength=strength,
                reason=f"KDJ 金叉 K={k:.1f} D={d:.1f} J={j:.1f}",
                price=close, contributors=["kdj"],
            )
        if k_prev >= d_prev and k < d and j > self.oversold:
            strength = 0.55 if j < self.overbought else 0.7
            return Signal(
                symbol, SignalAction.SELL, strength=strength,
                reason=f"KDJ 死叉 K={k:.1f} D={d:.1f} J={j:.1f}",
                price=close, contributors=["kdj"],
            )
        return Signal(symbol, SignalAction.HOLD, reason=f"KDJ 观望 K={k:.1f} D={d:.1f} J={j:.1f}", price=close)


class BollingerWidthStrategy(StrategyBase):
    """布林带宽度策略：收缩后突破 → 跟入；扩张后趋势衰减 → 平仓。"""

    def __init__(self, width_threshold: float = 0.04):
        super().__init__(name="BollingerWidth")
        self.width_threshold = float(width_threshold)

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        upper = self._get_last(df, "BOLL_UPPER")
        mid = self._get_last(df, "BOLL_MID")
        lower = self._get_last(df, "BOLL_LOWER")
        close = self._get_last(df, "Close", 0.0)
        if upper is None or mid is None or lower is None or not mid:
            return Signal(symbol, SignalAction.HOLD, reason="布林带数据不足", price=close or 0.0)
        width = (upper - lower) / mid
        if width < self.width_threshold:
            # 宽度收缩 + 收盘站上中轨：潜在突破
            if close > mid:
                return Signal(
                    symbol, SignalAction.BUY, strength=0.55,
                    reason=f"布林收窄待突破 width={width:.3f}",
                    price=close, contributors=["boll_width"],
                )
        elif width > self.width_threshold * 3 and close < mid:
            # 过度扩张 + 跌破中轨：离场
            return Signal(
                symbol, SignalAction.SELL, strength=0.5,
                reason=f"布林扩张回落 width={width:.3f}",
                price=close, contributors=["boll_width"],
            )
        return Signal(symbol, SignalAction.HOLD, reason=f"布林宽度观望 width={width:.3f}", price=close)


class WeightedEnsembleStrategy(StrategyBase):
    """多策略并行：把若干子策略按权重合并投票，超阈值触发。"""

    def __init__(self, strategies: Optional[list[tuple]] = None,
                 threshold: float = 0.2):
        super().__init__(name="WeightedEnsemble")
        # 默认 4 子策略，等权重 = 0.25；与 MultiIndicator 等权重行为一致
        if strategies is None:
            strategies = [
                (MACrossoverStrategy(), 0.30),
                (RSIReversalStrategy(), 0.25),
                (MATrendStrategy(),     0.25),
                (BollingerBreakoutStrategy(), 0.20),
            ]
        self.strategies = [(s, w) for s, w in strategies]
        self.threshold = float(threshold)

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Signal:
        scores = {"BUY": 0.0, "SELL": 0.0}
        contributors = []
        for strat, weight in self.strategies:
            sig = strat.generate_signal(symbol, df)
            if sig.action == SignalAction.BUY:
                scores["BUY"] += weight * sig.strength
                contributors.append(f"{strat.name}:BUY")
            elif sig.action == SignalAction.SELL:
                scores["SELL"] += weight * sig.strength
                contributors.append(f"{strat.name}:SELL")

        action = SignalAction.HOLD
        strength = 0.0
        reason = "加权综合观望"
        if scores["BUY"] - scores["SELL"] > self.threshold:
            action = SignalAction.BUY
            strength = scores["BUY"]
            reason = f"加权综合买入 buy={scores['BUY']:.2f} sell={scores['SELL']:.2f}"
        elif scores["SELL"] - scores["BUY"] > self.threshold:
            action = SignalAction.SELL
            strength = scores["SELL"]
            reason = f"加权综合卖出 sell={scores['SELL']:.2f} buy={scores['BUY']:.2f}"

        return Signal(
            symbol, action, strength=strength, reason=reason,
            price=self._get_last(df, "Close", 0.0) or 0.0,
            contributors=contributors,
        )


# 保持向后兼容：默认 multi 注册表不变；H 任务新策略仅追加
STRATEGY_REGISTRY = {
    "macd": MACrossoverStrategy,
    "rsi": RSIReversalStrategy,
    "ma_trend": MATrendStrategy,
    "bollinger": BollingerBreakoutStrategy,
    "multi": MultiIndicatorStrategy,
    "kdj": KDJReversalStrategy,
    "boll_width": BollingerWidthStrategy,
    "ensemble": WeightedEnsembleStrategy,
}


def create_strategy(strategy_name: str = "multi", **kwargs) -> StrategyBase:
    """
    策略工厂函数

    参数:
        strategy_name: "macd" | "rsi" | "ma_trend" | "bollinger" | "multi"
                       "kdj" | "boll_width" | "ensemble"
        **kwargs:      传递给策略构造函数的额外参数
    """
    strategy_name = strategy_name.lower()
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"未知策略: {strategy_name}，可选: {list(STRATEGY_REGISTRY.keys())}")

    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    return strategy_cls(**kwargs)
