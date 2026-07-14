# -*- coding: utf-8 -*-
"""
GUI 状态持久化（StateStore）

用 QSettings 跨会话保存：
- 窗口 geometry
- 主窗口 splitter 比例
- 表格列宽
- 监控列表
- 主题名

向后兼容：调用方可不显式创建 StateStore；首次构造即可读写。
"""

from typing import Any, Optional

from PyQt5.QtCore import QByteArray, QSettings
from PyQt5.QtWidgets import QMainWindow, QSplitter


class StateStore:
    """薄包装 QSettings，集中键名。"""

    ORG = "ndxinfo"
    APP = "trader"

    def __init__(self):
        self._s = QSettings(self.ORG, self.APP)

    # ---------- 通用 ----------

    def get(self, key: str, default: Any = None) -> Any:
        v = self._s.value(key, default)
        return v

    def set(self, key: str, value: Any) -> None:
        self._s.setValue(key, value)
        self._s.sync()

    # ---------- 便捷方法 ----------

    def restore_main_window(self, win: QMainWindow) -> None:
        geom = self._s.value("main_window/geometry")
        if isinstance(geom, QByteArray) or isinstance(geom, (bytes, bytearray)):
            try:
                win.restoreGeometry(geom)
            except Exception:
                pass
        state = self._s.value("main_window/state")
        if isinstance(state, QByteArray) or isinstance(state, (bytes, bytearray)):
            try:
                win.restoreState(state)
            except Exception:
                pass

    def save_main_window(self, win: QMainWindow) -> None:
        try:
            self._s.setValue("main_window/geometry", win.saveGeometry())
            self._s.setValue("main_window/state", win.saveState())
            self._s.sync()
        except Exception:
            pass

    def restore_splitter(self, splitter: QSplitter, name: str = "main_splitter") -> None:
        sizes = self._s.value(f"splitter/{name}")
        if sizes:
            try:
                splitter.setSizes([int(x) for x in sizes])
            except Exception:
                pass

    def save_splitter(self, splitter: QSplitter, name: str = "main_splitter") -> None:
        try:
            self._s.setValue(f"splitter/{name}", splitter.sizes())
        except Exception:
            pass

    # ---------- 主题 ----------

    def get_theme(self) -> str:
        v = self._s.value("ui/theme", "dark")
        return v or "dark"

    def set_theme(self, name: str) -> None:
        self._s.setValue("ui/theme", name)
        self._s.sync()


__all__ = ["StateStore"]
