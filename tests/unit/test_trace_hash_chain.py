"""审计记录哈希链（2026-11-28）：写入时串链，改内容、删记录都能被校验接口发现。"""

from __future__ import annotations

from sqlalchemy import text

import app.api.agent as agent_api
from app.core.trace_hash import GENESIS, compute_hash, verify_chain
from app.models import AgentTrace


def _write(n: int, monkeypatch, client) -> None:
    """用决策卡接口写 n 条审计（假模型，不联网）。"""
    monkeypatch.setattr(
        agent_api,
        "analyze",
        lambda ctx, **_kw: {
            "player_id": 1, "action": "HOLD", "reason": "测试", "risk_level": "LOW",
            "source": "rule_fallback", "disclaimer": "测试",
        },
    )
    for _ in range(n):
        assert client.get("/api/agent/decision/1").status_code == 200


def test_records_are_chained(client, session_factory, monkeypatch) -> None:
    _write(3, monkeypatch, client)
    db = session_factory()
    try:
        rows = db.query(AgentTrace).order_by(AgentTrace.trace_id).all()
        assert rows[0].prev_hash == GENESIS
        for prev, cur in zip(rows, rows[1:]):
            assert cur.prev_hash == prev.record_hash  # 一条接一条
        for row in rows:
            assert len(row.record_hash) == 64
            assert compute_hash(row, row.prev_hash) == row.record_hash
    finally:
        db.close()

    body = client.get("/api/agent/traces/verify").json()
    assert body["ok"] is True
    assert body["checked"] == 3
    listed = client.get("/api/agent/traces").json()["items"]
    assert all(item["record_hash"] for item in listed)


def test_tampered_content_is_detected(client, session_factory, monkeypatch) -> None:
    _write(3, monkeypatch, client)
    db = session_factory()
    try:
        second = db.query(AgentTrace).order_by(AgentTrace.trace_id).all()[1]
        db.execute(
            text("UPDATE agent_traces SET source = 'llm' WHERE trace_id = :id"), {"id": second.trace_id}
        )
        db.commit()
        broken_id = second.trace_id
    finally:
        db.close()

    body = client.get("/api/agent/traces/verify").json()
    assert body["ok"] is False
    assert body["broken_at"] == broken_id
    assert "内容被修改" in body["reason"]


def test_deleted_record_is_detected(client, session_factory, monkeypatch) -> None:
    _write(3, monkeypatch, client)
    db = session_factory()
    try:
        rows = db.query(AgentTrace).order_by(AgentTrace.trace_id).all()
        db.execute(text("DELETE FROM agent_traces WHERE trace_id = :id"), {"id": rows[1].trace_id})
        db.commit()
        third_id = rows[2].trace_id
    finally:
        db.close()

    body = client.get("/api/agent/traces/verify").json()
    assert body["ok"] is False
    assert body["broken_at"] == third_id
    assert "被删除" in body["reason"]


class _Row:
    def __init__(self, trace_id, record_hash=None, prev_hash=None):
        self.trace_id, self.record_hash, self.prev_hash = trace_id, record_hash, prev_hash


def test_legacy_rows_without_hash_are_counted_not_failed() -> None:
    body = verify_chain([_Row(1), _Row(2)])
    assert body == {**body, "ok": True, "checked": 0, "legacy_unhashed": 2}


def test_row_missing_hash_after_chain_started_is_broken() -> None:
    from types import SimpleNamespace

    from app.core.trace_hash import _ts

    first = SimpleNamespace(
        trace_id=1, created_at=None, mode="decision", player_id=1, source="llm", model=None,
        latency_ms=0, fallback_reason=None, input_digest=None, output_json="{}", prev_hash=GENESIS,
    )
    first.record_hash = compute_hash(first, GENESIS)
    body = verify_chain([first, _Row(2)])  # 链开始后又出现没有哈希的记录 → 视为被替换
    assert body["ok"] is False and body["broken_at"] == 2
    assert _ts(None) == ""


def test_old_table_gets_hash_columns(tmp_path, monkeypatch) -> None:
    """老库的 agent_traces 没有哈希列：启动时补上，且重复执行不出错。"""
    from sqlalchemy import create_engine, inspect

    import app.core.database as database

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE agent_traces (trace_id INTEGER PRIMARY KEY, mode VARCHAR(16))"))
    monkeypatch.setattr(database, "engine", engine)

    database._ensure_trace_hash_columns()
    database._ensure_trace_hash_columns()  # 幂等

    columns = {c["name"] for c in inspect(engine).get_columns("agent_traces")}
    assert {"prev_hash", "record_hash"} <= columns
