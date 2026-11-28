"""简单的进程内限流（滑动窗口），2026-11-26 加。

**为什么要有**：线上是免费档（0.1 vCPU）+ 按次计费的模型接口，此前任何人都能：
1. 反复点「重新生成」或写脚本刷 AI 接口 → 一直消耗模型额度；
2. 对同一个用户名不停试密码 → 暴力破解。

**怎么限**（刻意不按 IP：Render 前面有代理，取到的 IP 不可靠，按 IP 限容易误伤所有人）：
- 模型调用：全站每分钟最多 `LLM_CALLS_PER_MINUTE` 次（默认 60）。超了**不报错**，
  直接走规则版——和"模型挂了"同一条路，接口照样 200（AI 契约不变）；
- 登录：同一用户名 10 分钟内输错 `LOGIN_MAX_FAILURES` 次（默认 5）就先锁 10 分钟，429；
- 注册：全站每分钟最多 `REGISTER_PER_MINUTE` 个（默认 30），429。

**局限**（如实写）：计数在内存里，单进程有效；重启清零；多实例需要换成 Redis 之类。
本项目线上只有 1 个实例，够用。
"""

from __future__ import annotations

import threading
import time
from collections import deque


class SlidingWindow:
    """按 key 记录最近 window 秒内的事件时间戳。"""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _trim(self, key: str, window: float, now: float) -> deque[float]:
        events = self._events.setdefault(key, deque())
        while events and now - events[0] >= window:
            events.popleft()
        return events

    def count(self, key: str, window: float) -> int:
        with self._lock:
            return len(self._trim(key, window, time.monotonic()))

    def record(self, key: str, window: float) -> None:
        with self._lock:
            self._trim(key, window, time.monotonic()).append(time.monotonic())

    def try_acquire(self, key: str, limit: int, window: float) -> bool:
        """还有额度就记一次并返回 True；满了返回 False（不记）。limit<=0 表示不限。"""
        if limit <= 0:
            return True
        with self._lock:
            now = time.monotonic()
            events = self._trim(key, window, now)
            if len(events) >= limit:
                return False
            events.append(now)
            return True

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


#: 全进程共用一份（测试里由 conftest 每条用例前清空）
limiter = SlidingWindow()

LLM_KEY = "llm"
REGISTER_KEY = "register"
LOGIN_WINDOW_SECONDS = 600.0


def llm_budget_ok(settings: object | None = None) -> bool:
    """模型调用前问一句"这分钟还有额度吗"；有就占一个名额。"""
    limit = int(getattr(settings, "llm_calls_per_minute", 60) if settings is not None else 60)
    return limiter.try_acquire(LLM_KEY, limit, 60.0)


def login_key(username: str) -> str:
    return f"login-fail:{username.strip().lower()}"


__all__ = [
    "LLM_KEY",
    "LOGIN_WINDOW_SECONDS",
    "REGISTER_KEY",
    "SlidingWindow",
    "limiter",
    "llm_budget_ok",
    "login_key",
]
