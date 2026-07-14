# -*- coding: utf-8 -*-
"""
令牌桶限流器（TokenBucket）

装饰 / 上下文管理器用法：
    bucket = TokenBucket(rate=2.0, burst=5)

    @bucket.acquire
    def refresh_prices(): ...

    # 或上下文
    with bucket.acquire_ctx():
        yf.download(...)
"""

import threading
import time
from contextlib import contextmanager


class TokenBucket:
    """
    简单令牌桶实现；rate=每秒填入令牌数，burst=桶容量。
    调用 acquire() 时若无可用令牌则阻塞等待。
    """

    def __init__(self, rate: float = 2.0, burst: int = 5):
        if rate <= 0:
            raise ValueError("rate 必须为正数")
        if burst <= 0:
            raise ValueError("burst 必须为正数")
        self.rate = float(rate)
        self.burst = int(burst)
        self._tokens = float(burst)
        self._last = time.monotonic()
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        if elapsed <= 0:
            return
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last = now

    def acquire(self, timeout: float = 30.0) -> bool:
        """阻塞直到取得令牌。返回是否取得。"""
        with self._cond:
            deadline = time.monotonic() + max(0, timeout)
            while True:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
                # 还需要等多久才够 1 个令牌
                need = 1.0 - self._tokens
                wait = need / self.rate if self.rate > 0 else 1.0
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._cond.wait(timeout=min(wait, remaining))

    def try_acquire(self) -> bool:
        """非阻塞立即返回。"""
        with self._cond:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    @contextmanager
    def acquire_ctx(self, timeout: float = 30.0):
        ok = self.acquire(timeout=timeout)
        try:
            yield ok
        finally:
            pass

    def __call__(self, fn):
        """装饰器用法：fn() 前自动获取令牌"""
        def wrapper(*args, **kwargs):
            self.acquire()
            return fn(*args, **kwargs)
        wrapper.__name__ = getattr(fn, "__name__", "wrapped")
        return wrapper
