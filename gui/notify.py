# -*- coding: utf-8 -*-
"""
系统通知（Notifier）

统一封装：
- plyer.notification（桌面通知）  ← 优先
- QSystemTrayIcon                  ← 次
- QMessageBox                      ← 兜底

向后兼容：plyer / tray 可选，未安装时自动降级。
"""

import logging
from typing import Optional

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox, QWidget

logger = logging.getLogger(__name__)


class Notifier:
    """统一通知器；方法静默失败，不抛错以免破坏主流程。"""

    def __init__(self, app: Optional[QApplication] = None, level: str = "info"):
        self.app = app
        self.level = level  # "info" | "warn" | "error"
        self._tray: Optional[QSystemTrayIcon] = None
        if app is not None and QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = QSystemTrayIcon(app)
            self._tray.show()

    def _send_native(self, title: str, message: str) -> bool:
        try:
            from plyer import notification  # type: ignore
            notification.notify(
                title=title,
                message=message,
                app_name="ndxinfo trader",
                timeout=5,
            )
            return True
        except Exception as e:
            logger.debug(f"plyer 不可用: {e}")
        return False

    def _send_tray(self, title: str, message: str) -> bool:
        if self._tray is None:
            return False
        try:
            self._tray.showMessage(title, message, QSystemTrayIcon.Information, 5000)
            return True
        except Exception as e:
            logger.debug(f"tray 不可用: {e}")
        return False

    def _send_messagebox(self, title: str, message: str, icon: int) -> bool:
        try:
            QMessageBox.information(
                None, title, message,
                QMessageBox.Ok if icon == QMessageBox.Information else QMessageBox.Ok,
            )
            return True
        except Exception as e:
            logger.debug(f"messagebox 不可用: {e}")
        return False

    def info(self, title: str, message: str) -> None:
        self._emit("info", title, message)

    def warn(self, title: str, message: str) -> None:
        self._emit("warn", title, message)

    def error(self, title: str, message: str) -> None:
        self._emit("error", title, message)

    def _emit(self, level: str, title: str, message: str) -> None:
        order = ["info", "warn", "error"]
        if order.index(level) < order.index(self.level):
            return
        # 优先级：plyer → tray → messagebox
        if self._send_native(title, message):
            return
        if self._send_tray(title, message):
            return
        icon = (
            QMessageBox.Warning if level == "warn"
            else QMessageBox.Critical if level == "error"
            else QMessageBox.Information
        )
        self._send_messagebox(title, message, icon)


__all__ = ["Notifier"]
