# -*- coding: utf-8 -*-
"""
配置加载器（trading.config_loader）

用法:
    from trading.config_loader import load_config, apply_env_overrides
    cfg = load_config("config/default.yaml")
    apply_env_overrides(cfg, prefix="NDX_")

特性:
- 找不到文件 → 返回内置默认 AppConfig
- 环境变量覆盖：`NDX_<SECTION>__<FIELD>=value`
- 类型自动转换（int/float/bool 智能判断）
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from trading.config_models import (
    AppConfig, BrokerConfig, MonitorConfig, IndicatorConfig,
    StrategyConfig, make_default_config,
)
from trading.risk_manager import RiskLimits
from trading.sim_rules import SimExecutionRules, DEFAULT_RULES

logger = logging.getLogger(__name__)


def _cast(value: str) -> Any:
    """把字符串转成合适的 Python 类型"""
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False
    if value.lower() in ("null", "none", ""):
        return None
    # int
    try:
        if re.fullmatch(r"-?\d+", value):
            return int(value)
    except Exception:
        pass
    # float
    try:
        return float(value)
    except Exception:
        pass
    # 列表（逗号分隔）
    if "," in value:
        return [_cast(v.strip()) for v in value.split(",")]
    return value


def _try_load_yaml(path: Path) -> Optional[dict]:
    try:
        import yaml  # PyYAML
    except ImportError:
        logger.debug("PyYAML 未安装，使用内置 JSON 兜底")
        return None
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"读取 {path} 失败: {e}，回退到默认")
        return None


def load_config(path: str | os.PathLike | None = None) -> AppConfig:
    """
    加载 AppConfig；按以下优先级：
        1. 显式传入的 path
        2. 环境变量 NDX_CONFIG 指向的文件
        3. ./config/default.yaml
        4. 内置默认
    """
    candidates = []
    if path:
        candidates.append(Path(path))
    env_path = os.environ.get("NDX_CONFIG")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path("config/default.yaml"))

    raw: dict = {}
    for p in candidates:
        d = _try_load_yaml(p)
        if d:
            logger.info(f"已加载配置: {p}")
            raw = d
            break

    return _build_app_config(raw)


def _build_app_config(raw: dict) -> AppConfig:
    cfg = make_default_config()
    # broker
    b = raw.get("broker", {})
    cfg.broker = BrokerConfig(
        type=b.get("type", cfg.broker.type),
        initial_cash=float(b.get("initial_cash", cfg.broker.initial_cash)),
        paper=bool(b.get("paper", cfg.broker.paper)),
    )
    # risk
    r = raw.get("risk", {})
    cfg.risk = RiskLimits(
        max_position_pct=float(r.get("max_position_pct", 0.25)),
        stop_loss_pct=float(r.get("stop_loss_pct", -8.0)),
        trailing_stop_pct=float(r.get("trailing_stop_pct", -5.0)),
        max_daily_trades=int(r.get("max_daily_trades", 20)),
        cooldown_seconds=int(r.get("cooldown_seconds", 60)),
        atr_multiple=float(r.get("atr_multiple", 2.0)),
        atr_period=int(r.get("atr_period", 14)),
        use_atr_stop=bool(r.get("use_atr_stop", False)),
    )
    # monitor
    m = raw.get("monitor", {})
    cfg.monitor = MonitorConfig(
        symbols=tuple(m.get("symbols", cfg.monitor.symbols)),
        refresh_interval=int(m.get("refresh_interval", 30)),
    )
    # indicators
    i = raw.get("indicators", {})
    cfg.indicators = IndicatorConfig(
        ma_periods=tuple(i.get("ma_periods", [5, 10, 20, 60])),
        rsi_period=int(i.get("rsi_period", 14)),
        macd_fast=int(i.get("macd_fast", 12)),
        macd_slow=int(i.get("macd_slow", 26)),
        macd_signal=int(i.get("macd_signal", 9)),
        boll_period=int(i.get("boll_period", 20)),
        boll_std=float(i.get("boll_std", 2.0)),
    )
    # sim_rules
    s = raw.get("sim_rules", {})
    cfg.sim_rules = SimExecutionRules(
        commission_per_share=float(s.get("commission_per_share", DEFAULT_RULES.commission_per_share)),
        min_commission=float(s.get("min_commission", DEFAULT_RULES.min_commission)),
        slippage_bps=float(s.get("slippage_bps", DEFAULT_RULES.slippage_bps)),
        fill_delay_ms=int(s.get("fill_delay_ms", DEFAULT_RULES.fill_delay_ms)),
        partial_fill_chance=float(s.get("partial_fill_chance", DEFAULT_RULES.partial_fill_chance)),
        t_plus_one=bool(s.get("t_plus_one", DEFAULT_RULES.t_plus_one)),
        market_hours_only=bool(s.get("market_hours_only", DEFAULT_RULES.market_hours_only)),
    )
    # strategy
    st = raw.get("strategies", {})
    cfg.strategy = StrategyConfig(
        name=st.get("name", "multi"),
        weights=(st.get("multi", {}) or {}).get("weights", {}) or {},
    )
    cfg.notify_level = str(raw.get("notify_level", "info"))
    cfg.log_dir = str(raw.get("log_dir", "logs"))
    cfg.log_json = bool(raw.get("log_json", False))
    return cfg


def apply_env_overrides(cfg: AppConfig, prefix: str = "NDX_") -> AppConfig:
    """通过环境变量覆盖任意字段；路径用 "__" 分隔。例：NDX_RISK__STOP_LOSS_PCT"""
    # dataclass 不直接 setattr 子对象字段，这里通过临时重建实现
    from dataclasses import replace

    flat: dict[str, tuple[Any, str]] = {}
    flat["BROKER__TYPE"] = (cfg.broker.type, "broker.type")
    flat["BROKER__INITIAL_CASH"] = (cfg.broker.initial_cash, "broker.initial_cash")
    flat["BROKER__PAPER"] = (cfg.broker.paper, "broker.paper")

    risk_kv = {
        "max_position_pct": cfg.risk.max_position_pct,
        "stop_loss_pct": cfg.risk.stop_loss_pct,
        "trailing_stop_pct": cfg.risk.trailing_stop_pct,
        "max_daily_trades": cfg.risk.max_daily_trades,
        "cooldown_seconds": cfg.risk.cooldown_seconds,
        "atr_multiple": cfg.risk.atr_multiple,
        "atr_period": cfg.risk.atr_period,
        "use_atr_stop": cfg.risk.use_atr_stop,
    }
    risk_changed: dict[str, Any] = {}
    for k, v in risk_kv.items():
        env_key = f"{prefix}RISK__{k.upper()}"
        if env_key in os.environ:
            new = _cast(os.environ[env_key])
            risk_changed[k] = new
            logger.info(f"env override {env_key} = {new}")

    monitor_changed: dict[str, Any] = {}
    if f"{prefix}MONITOR__REFRESH_INTERVAL" in os.environ:
        monitor_changed["refresh_interval"] = _cast(os.environ[f"{prefix}MONITOR__REFRESH_INTERVAL"])
    if f"{prefix}MONITOR__SYMBOLS" in os.environ:
        monitor_changed["symbols"] = tuple(_cast(os.environ[f"{prefix}MONITOR__SYMBOLS"]))

    sim_rules_changed: dict[str, Any] = {}
    for k in [
        "commission_per_share", "min_commission", "slippage_bps",
        "fill_delay_ms", "partial_fill_chance", "t_plus_one", "market_hours_only",
    ]:
        env_key = f"{prefix}SIM_RULES__{k.upper()}"
        if env_key in os.environ:
            sim_rules_changed[k] = _cast(os.environ[env_key])
            logger.info(f"env override {env_key} = {os.environ[env_key]}")

    new_broker = cfg.broker
    if f"{prefix}BROKER__TYPE" in os.environ:
        new_broker = replace(new_broker, type=_cast(os.environ[f"{prefix}BROKER__TYPE"]))
    if f"{prefix}BROKER__INITIAL_CASH" in os.environ:
        new_broker = replace(new_broker, initial_cash=_cast(os.environ[f"{prefix}BROKER__INITIAL_CASH"]))
    if f"{prefix}BROKER__PAPER" in os.environ:
        new_broker = replace(new_broker, paper=_cast(os.environ[f"{prefix}BROKER__PAPER"]))

    new_risk = cfg.risk
    if risk_changed:
        new_risk = replace(new_risk, **risk_changed)

    new_monitor = cfg.monitor
    if monitor_changed:
        new_monitor = replace(new_monitor, **monitor_changed)

    new_sim_rules = cfg.sim_rules
    if sim_rules_changed:
        new_sim_rules = replace(new_sim_rules, **sim_rules_changed)

    cfg = replace(
        cfg,
        broker=new_broker,
        risk=new_risk,
        monitor=new_monitor,
        sim_rules=new_sim_rules,
    )
    return cfg


__all__ = ["load_config", "apply_env_overrides"]
