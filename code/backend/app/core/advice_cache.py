"""建议卡与决策卡共用同一条建议（2026-11-28 加）。

**为什么**：详情页同时调用 `/api/analysis/{id}`（显示 BUY/SELL/HOLD）和
`/api/agent/decision/{id}`（显示「若采纳可买 N 股」）。两个接口以前各自问一次模型，
两次回答可能不一样——页面写着「买入」，下面却是按「持有」算出的 0 股。

**做法**：按「用户 + 选手 + 现价 + 持仓数 + 余额」缓存建议 120 秒，两个接口取同一条；
价格或持仓一变，键就变，自然重新分析。用户点「重新分析」时传 refresh 强制重算。
顺带省掉一半的模型调用。进程内缓存，单实例部署够用。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

TTL_SECONDS = 120.0

_store: dict[tuple, tuple[float, dict[str, Any]]] = {}
_lock = threading.Lock()


def _key(user_id: int, context: dict[str, Any]) -> tuple:
    position = context.get("position") or {}
    return (
        int(user_id),
        context.get("player_id"),
        str(context.get("current_price")),
        float(position.get("quantity") or 0),
        str((context.get("account") or {}).get("balance")),  # 余额变了也重新分析
    )


def shared_advice(
    user_id: int,
    context: dict[str, Any],
    compute: Callable[[], dict[str, Any]],
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """命中缓存直接返回同一条建议；未命中或 refresh 时调用 compute() 并存下。"""
    key = _key(user_id, context)
    now = time.monotonic()
    if not refresh:
        with _lock:
            hit = _store.get(key)
            if hit and now - hit[0] < TTL_SECONDS:
                return dict(hit[1])
    advice = compute()
    with _lock:
        _store[key] = (now, dict(advice))
        for stale in [k for k, (at, _) in _store.items() if now - at >= TTL_SECONDS]:
            _store.pop(stale, None)
    return dict(advice)


def clear() -> None:
    with _lock:
        _store.clear()


__all__ = ["TTL_SECONDS", "clear", "shared_advice"]
