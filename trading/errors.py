# -*- coding: utf-8 -*-
"""
统一错误类型

所有业务模块抛出的异常都应继承 TradingError，便于上层按类捕获，
避免裸 except Exception 静默吞错。
"""


class TradingError(Exception):
    """所有业务异常的根类"""


class BrokerError(TradingError):
    """券商接口失败（连接 / 下单回报错误）"""


class DataError(TradingError):
    """行情 / 历史数据失败"""


class RiskRejected(TradingError):
    """风控拦截"""


class StrategyError(TradingError):
    """策略逻辑 / 信号生成失败"""


class ConfigError(TradingError):
    """配置错误"""
