# -*- coding: utf-8 -*-
"""
应用配置 dataclass（AppConfig）

把 `config.py` 顶层常量逐步迁移到 typed 配置类。
当前仅作为薄包装层，老 config.py 模块继续提供旧常量；
未来完全替换时不破坏任何 import。
"""

from dataclasses import dataclass, field
from typing import Optional, Sequence

from trading.risk_manager import RiskLimits
from trading.sim_rules import SimExecutionRules, DEFAULT_RULES


@dataclass
class BrokerConfig:
    """券商配置"""
    type: str = "simulation"            # "simulation" | "alpaca"
    initial_cash: float = 100000.0
    paper: bool = True                  # 仅 alpaca 有效


@dataclass
class MonitorConfig:
    """监控标的配置"""
    symbols: Sequence[str] = field(default_factory=tuple)
    refresh_interval: int = 30          # 秒


@dataclass
class IndicatorConfig:
    """指标配置"""
    ma_periods: Sequence[int] = field(default_factory=lambda: (5, 10, 20, 60))
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    boll_period: int = 20
    boll_std: float = 2.0


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str = "multi"
    weights: dict = field(default_factory=dict)   # 仅 multi 使用


@dataclass
class AppConfig:
    """应用顶层配置"""
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    risk: RiskLimits = field(default_factory=RiskLimits)
    monitor: MonitorConfig = field(default_factory=MonitorConfig)
    indicators: IndicatorConfig = field(default_factory=IndicatorConfig)
    sim_rules: SimExecutionRules = field(default_factory=lambda: DEFAULT_RULES)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    notify_level: str = "info"           # "info" | "warn" | "error"
    log_dir: str = "logs"
    log_json: bool = False


def make_default_config() -> AppConfig:
    """工厂：构造默认值"""
    return AppConfig()


def replace_config(cfg: AppConfig, **changes) -> AppConfig:
    """友好地替换字段：基于 dataclasses.replace 包装。"""
    from dataclasses import replace as _replace
    return _replace(cfg, **changes)


__all__ = [
    "BrokerConfig", "MonitorConfig", "IndicatorConfig", "StrategyConfig",
    "AppConfig", "make_default_config", "replace_config",
]
