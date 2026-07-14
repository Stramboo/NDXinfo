# -*- coding: utf-8 -*-
"""
event_bus.py — 异步事件总线（用于把 MockEngine / 真 TradingEngine 的事件
                推送到 WebSocket 客户端）

设计：
- 内部存储一个 set[asyncio.Queue]，每个 WS 连接一个 queue
- emit_*() 方法被引擎线程 / MockEngine 同步调用，内部 schedule 到 event loop
- 消费者用 subscribe() 拿到 async iterator
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


class EventBus:
    """异步事件总线；自带订阅管理"""

    def __init__(self, maxsize: int = 1000):
        self._subscribers: list[asyncio.Queue] = []
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self.maxsize = maxsize

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    # 在主循环里 push 事件
    async def publish(self, event: dict) -> None:
        async with self._lock:
            queues = list(self._subscribers)
        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # 满了就丢——前端通常跟得上
                pass

    # 同步上下文（如 MockEngine.step()）里调用也能跑
    def publish_threadsafe(self, event: dict) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(
            lambda: asyncio.ensure_future(self.publish(event)))

    async def subscribe(self) -> AsyncIterator[dict]:
        q: asyncio.Queue = asyncio.Queue(maxsize=self.maxsize)
        async with self._lock:
            self._subscribers.append(q)
        try:
            while True:
                yield await q.get()
        finally:
            async with self._lock:
                if q in self._subscribers:
                    self._subscribers.remove(q)


# ----- 事件类型 (前端用 type 字段路由) -------------------------------------

def tick_event(symbol: str, price: float) -> dict:
    return {"type": "tick",
            "data": {"symbol": symbol, "price": price, "ts": int(time.time()*1000)}}


def order_event(order: dict) -> dict:
    return {"type": "order_update", "data": order}


def equity_event(snapshot: dict) -> dict:
    return {"type": "equity_update", "data": snapshot}


def signal_event(signal: dict) -> dict:
    return {"type": "signal", "data": signal}


def log_event(level: str, msg: str, **ctx) -> dict:
    return {"type": "log",
            "data": {"level": level, "msg": msg,
                     "context": ctx, "ts": int(time.time()*1000)}}


__all__ = ["EventBus", "tick_event", "order_event",
           "equity_event", "signal_event", "log_event"]
