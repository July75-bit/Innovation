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


# ---------- 重灌端点（第 6 天，POST /api/debug/reseed）----------


def test_reseed_rebuilds_16_players_and_clean_demo(client) -> None:
    resp = client.post(f"/api/debug/reseed?token={settings.reseed_token}&rounds=12&seed=42")

    assert resp.status_code == 200
    body = resp.json()
    assert body["点数自检"] == "OK"  # 15 名 trading 每人 ≥10 点
    assert body["重建"]["players"] == 16

    # 通过业务接口二次复核（不信任端点自己的返回）
    players = client.get("/api/players").json()
    assert len(players) == 16
    assert len({p["team"] for p in players}) == 8  # 8 队 × 2 人
    m0nesy = next(p for p in players if p["name"] == "m0NESY")
    assert m0nesy["team"] == "Falcons"  # 转会生效

    points3 = client.get("/api/players/3/prices").json()["points"]
    assert len(points3) >= 10  # 初始行 + 12 轮（其中 3 轮本队比赛暂停）

    account = client.get("/api/account").json()
    assert float(account["balance"]) == 5000.0  # demo 账户干净重置
    assert len(client.get("/api/trades").json()) == 0


def test_reseed_keeps_registered_account(client) -> None:
    """BUG-15 回归：重灌**不能删注册账号**（原先 drop_all 连 users 表一起删）。

    用户实测"注册的账户第二天就消失"，根因是重灌把 users 表删了。
    这里：注册 → 买 3 股造脏数据 → 重灌 → 原密码仍能登录，且余额/流水复位。
    """
    reg = client.post(
        "/api/auth/register", json={"username": "keep_me", "password": "Passw0rd123"}
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/trades/buy", json={"player_id": 1, "quantity": 3}, headers=auth).status_code == 200
    assert len(client.get("/api/trades", headers=auth).json()) == 1

    resp = client.post(f"/api/debug/reseed?token={settings.reseed_token}&rounds=2&seed=42")
    assert resp.status_code == 200, resp.text
    assert resp.json()["重建"]["注册账号（已复位余额、保留凭据）"] >= 1

    # 账号还在、原密码可用（用户真正关心的"账号别消失"）
    relogin = client.post(
        "/api/auth/login", json={"username": "keep_me", "password": "Passw0rd123"}
    )
    assert relogin.status_code == 200, relogin.text
    new_auth = {"Authorization": f"Bearer {relogin.json()['token']}"}

    # 余额与流水一起复位（行情回种子价，钱也回起点才自洽）
    account = client.get("/api/account", headers=new_auth).json()
    assert float(account["balance"]) == 5000.0
    assert client.get("/api/trades", headers=new_auth).json() == []


def test_reseed_rejects_wrong_token(client) -> None:
    resp = client.post("/api/debug/reseed?token=not-the-token")

    assert resp.status_code == 403
    assert resp.json()["code"] == "TOKEN_MISMATCH"


def test_reseed_can_be_disabled(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "debug_endpoints", False)

    resp = client.post(f"/api/debug/reseed?token={settings.reseed_token}")

    assert resp.status_code == 404
    assert resp.json()["code"] == "ENDPOINT_DISABLED"
