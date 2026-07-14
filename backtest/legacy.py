# -*- coding: utf-8 -*-
"""
旧 backtest.py 的 compat 兼容层

为保留 `from backtest import BacktestEngine` 调用不报 ImportError，
这里把旧 BacktestEngine 重新导出为 LegacyBacktestEngine。

调用方应迁移到：
    from backtest import BacktestEngine
详见 backtest.engine.BacktestEngine。
"""

import warnings

try:
    # 如果用户未升级路径，仍可直接运行旧脚本：兼容旧类名
    from backtest import BacktestEngine as LegacyBacktestEngine  # type: ignore
except Exception:
    LegacyBacktestEngine = None  # type: ignore


def run(*args, **kwargs):
    """旧的 backtest.run() 入口：留位置，新代码请直接用 BacktestEngine。"""
    warnings.warn(
        "backtest.legacy.run 已弃用，请改用 from backtest import BacktestEngine",
        DeprecationWarning,
        stacklevel=2,
    )
    if LegacyBacktestEngine is None:
        raise RuntimeError("新框架不可用，请先升级到 backtest >= 2.0")
    return LegacyBacktestEngine(*args, **kwargs).run()


__all__ = ["run"]
