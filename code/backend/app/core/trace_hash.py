"""审计记录哈希链（2026-11-28 加）：让 agent_traces 被改、被删能被发现。

**做法**：每条审计记录写入时，把它的内容和**上一条记录的哈希**一起算 SHA-256，存进
`record_hash`；上一条的哈希存进 `prev_hash`。这样记录一条接一条串成链：

    record_hash(n) = SHA-256( 第 n 条的内容 + record_hash(n-1) )

任何一条的内容被改，它自己的哈希就对不上；删掉中间一条，下一条的 `prev_hash`
就接不上；改完再重算哈希，后面所有记录都要跟着重算，否则同样对不上。
`GET /api/agent/traces/verify` 从头到尾重算一遍，报告第一处断开的位置。

**参与哈希的字段**：trace_id、created_at、mode、player_id、source、model、latency_ms、
fallback_reason、input_digest、output_json、prev_hash。按固定顺序序列化成 JSON 再算，
保证 SQLite 和 Postgres 上结果一致（时间统一成 UTC、精确到微秒）。

**边界（如实写）**：
- 能发现篡改，但不能阻止篡改；能直接改库的人可以把整条链重算一遍。要防这一点，
  需要把最新哈希定期存到库外（比如打印到日志、提交到仓库），本项目没做；
- 加哈希之前写入的旧记录没有哈希，校验时单独计数，链从第一条有哈希的记录开始；
- 写入时用进程内锁保证顺序，适合单实例部署（线上就是 1 个实例）。
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from typing import Any, Iterable

#: 链的起点：第一条有哈希的记录的 prev_hash
GENESIS = "0" * 64

#: 写入审计时串行化「读上一条哈希 → 写新记录」，避免两条记录接到同一个前驱上
WRITE_LOCK = threading.Lock()


def _ts(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:  # SQLite 读回来是 naive，按 UTC 处理
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")


def compute_hash(row: Any, prev_hash: str) -> str:
    """按固定字段与顺序算一条审计记录的 SHA-256（十六进制 64 位）。"""
    payload = {
        "trace_id": row.trace_id,
        "created_at": _ts(row.created_at),
        "mode": row.mode,
        "player_id": row.player_id,
        "source": row.source,
        "model": row.model,
        "latency_ms": int(row.latency_ms or 0),
        "fallback_reason": row.fallback_reason,
        "input_digest": row.input_digest,
        "output_json": row.output_json,
        "prev_hash": prev_hash,
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_chain(rows: Iterable[Any]) -> dict[str, Any]:
    """按 trace_id 升序传入全部记录，重算并检查链是否完整。"""
    checked = 0
    legacy = 0
    expected_prev: str | None = None
    for row in rows:
        if not row.record_hash:
            if expected_prev is None:
                legacy += 1  # 加哈希之前的旧记录
                continue
            return _broken(row, checked, legacy, "记录缺少哈希")
        prev = row.prev_hash or ""
        if expected_prev is None:
            expected_prev = prev  # 链起点：第一条有哈希的记录，前驱应是 GENESIS 或旧链尾
        if prev != expected_prev:
            return _broken(row, checked, legacy, "prev_hash 与上一条记录的哈希不一致（中间记录被删除或替换）")
        if compute_hash(row, prev) != row.record_hash:
            return _broken(row, checked, legacy, "记录内容与哈希不一致（内容被修改）")
        expected_prev = row.record_hash
        checked += 1
    return {
        "ok": True,
        "checked": checked,
        "legacy_unhashed": legacy,
        "last_hash": expected_prev,
        "message": f"哈希链完整：校验 {checked} 条" + (f"，另有 {legacy} 条加哈希前的旧记录" if legacy else ""),
    }


def _broken(row: Any, checked: int, legacy: int, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "checked": checked,
        "legacy_unhashed": legacy,
        "broken_at": row.trace_id,
        "reason": reason,
        "message": f"哈希链在 trace_id={row.trace_id} 处断开：{reason}",
    }


__all__ = ["GENESIS", "WRITE_LOCK", "compute_hash", "verify_chain"]
