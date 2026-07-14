# -*- coding: utf-8 -*-
"""
文件变更监听（FileWatcher）

通过 mtime 监听 yaml 文件变化（线程安全），触发回调。
注意：仅供 F1 验证 / 简单使用，重型需求建议用 watchdog。
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class FileWatcher:
    """
    用 mtime 比较实现的轻量文件变更监听。

    用法:
        w = FileWatcher("config/default.yaml",
                        on_change=lambda p: print("changed", p))
        w.start()
        ...
        w.stop()
    """

    def __init__(self, path: str | Path, on_change: Callable[[Path], None],
                 interval: float = 1.0):
        self.path = Path(path)
        self.on_change = on_change
        self.interval = interval
        self._last_mtime: float | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._last_mtime = self._read_mtime()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="FileWatcher"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _read_mtime(self) -> float | None:
        try:
            return self.path.stat().st_mtime
        except FileNotFoundError:
            return None

    def _loop(self) -> None:
        while self._running:
            time.sleep(self.interval)
            try:
                mtime = self._read_mtime()
                if mtime is None:
                    continue
                if self._last_mtime is None:
                    self._last_mtime = mtime
                elif mtime > self._last_mtime:
                    self._last_mtime = mtime
                    logger.info(f"检测到 {self.path} 变更")
                    try:
                        self.on_change(self.path)
                    except Exception as e:
                        logger.warning(f"on_change 回调异常: {e}")
            except Exception as e:
                logger.debug(f"watcher 异常: {e}")


__all__ = ["FileWatcher"]
