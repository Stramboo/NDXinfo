# -*- coding: utf-8 -*-
"""
结构化日志（observability）

- setup_logging(): 初始化 dictConfig + RotatingFileHandler + 可选 JSON 格式
- JsonFormatter: 自带实现，不依赖 python-json-logger

字段统一为：ts / level / module / msg / context (dict)

向后兼容：未设置 log_json=True 时与原 basicConfig 行为一致。
"""

from __future__ import annotations

import json
import logging
import logging.config
import os
from datetime import datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """将 LogRecord 序列化为单行 JSON"""

    DEFAULT_KEYS = {
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info", "lineno",
        "funcName", "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # 提取 extra 自定义字段
        ctx: dict[str, Any] = {}
        for k, v in record.__dict__.items():
            if k in self.DEFAULT_KEYS or k.startswith("_"):
                continue
            try:
                json.dumps(v)
                ctx[k] = v
            except Exception:
                ctx[k] = repr(v)
        if ctx:
            payload["context"] = ctx
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    初始化日志：
        - 控制台输出（始终 human-readable）
        - 文件输出 RotatingFileHandler（按 json_format 决定格式）
    """
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "trader.log")

    formatter_cls = JsonFormatter if json_format else logging.Formatter
    if json_format:
        file_formatter: logging.Formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {"()": "logging.Formatter",
                         "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s"},
            "file": {"()": type(file_formatter).__module__ + "." + type(file_formatter).__name__,
                     "format": ""},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "level": level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file,
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "formatter": "file",
                "level": level,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": level,
        },
    })


__all__ = ["setup_logging", "JsonFormatter"]
