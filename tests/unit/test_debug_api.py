"""只读运维自检接口的测试（`GET /api/debug/db`，第 5 天 B）。

这个接口是"验收时截个图"用的探针，最容易踩的两类问题都要有测试兜住：
1. **别把敏感信息带出去**——只允许方言/表名/行数，不能有连接串；
2. **能一键关掉**——`DEBUG_ENDPOINTS=0` 时必须 404，而不是"关不掉"。
"""

from __future__ import annotations

import pytest

from app.core.config import settings


def test_debug_db_returns_metadata_only(client) -> None:
    resp = client.get("/api/debug/db")

    assert resp.status_code == 200
    body = resp.json()
    assert body["数据库方言"] == "sqlite"  # 测试环境
    # conftest 建了 5 张表
    assert set(body["表清单"]) >= {"users", "players", "positions", "trades", "price_history"}
    assert body["表行数"]["players"] >= 1
    assert body["业务核对"]["选手数"] >= 1


def test_debug_db_never_leaks_connection_string(client) -> None:
    """只读元信息：不能把 DATABASE_URL / 密码带出去。"""
    text = client.get("/api/debug/db").text

    assert "sqlite:///" not in text
    assert "postgresql" not in text.lower()
    assert "password" not in text.lower()


def test_debug_db_can_be_disabled(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug_endpoints", False)

    resp = client.get("/api/debug/db")

    assert resp.status_code == 404
    assert resp.json()["code"] == "ENDPOINT_DISABLED"
