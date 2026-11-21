"""市场 / 详情 / 价格历史 / 账户 / 持仓的接口契约测试。

负责人：B

守住 docs/software/api_contract.md 里的字段名与结构：
- player_id 不叫 id；
- current_price / prev_price / change_pct 由后端算好；
- 价格历史是 {player_id, points: [...]}，升序、带 reason、空数组不 404；
- rating 是 0–100 的模拟分。
"""

from __future__ import annotations

import pytest

SEED_ZYWOO = 1
SEED_ROPZ = 2


def test_market_list_contract_fields(client):
    response = client.get("/api/players")

    assert response.status_code == 200
    players = response.json()
    assert len(players) == 4

    first = players[0]
    assert "id" not in first, "契约规定主键字段叫 player_id，不叫 id"
    assert {
        "player_id",
        "name",
        "display_name",
        "team",
        "role",
        "current_price",
        "prev_price",
        "change_pct",
        "rating",
        "status",
    } <= set(first)
    assert first["player_id"] == SEED_ZYWOO
    assert first["current_price"] == 126.0
    assert first["prev_price"] == 120.0
    # (126 - 120) / 120 = +5%
    assert first["change_pct"] == 5.0
    assert first["rating"] == 88
    assert first["status"] == "trading"

    # 下跌案例：flameZ 70 -> 63
    flamez = next(player for player in players if player["name"] == "flameZ")
    assert flamez["change_pct"] == -10.0


def test_player_detail_has_latest_reason(client):
    response = client.get(f"/api/players/{SEED_ZYWOO}")

    assert response.status_code == 200
    body = response.json()
    assert body["player_id"] == SEED_ZYWOO
    assert body["latest_reason"] == "模拟比赛表现提升（测试数据）"


def test_player_detail_unknown_returns_404(client):
    response = client.get("/api/players/999")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "选手不存在",
        "code": "PLAYER_NOT_FOUND",
    }


def test_price_history_ascending_with_reason(client):
    response = client.get(f"/api/players/{SEED_ZYWOO}/prices")

    assert response.status_code == 200
    body = response.json()
    assert body["player_id"] == SEED_ZYWOO
    points = body["points"]
    assert [point["price"] for point in points] == [120.0, 126.0]
    assert all(point["reason"] for point in points)
    assert points[0]["ts"] <= points[1]["ts"]
    assert points[1]["ts"].endswith("Z")


def test_price_history_empty_points_not_404(client):
    response = client.get(f"/api/players/{SEED_ROPZ}/prices")

    assert response.status_code == 200
    assert response.json() == {"player_id": SEED_ROPZ, "points": []}


def test_price_history_unknown_player_404(client):
    response = client.get("/api/players/999/prices")

    assert response.status_code == 404
    assert response.json()["code"] == "PLAYER_NOT_FOUND"


def test_account_and_positions_flow(client):
    account = client.get("/api/account").json()
    assert account == {
        "user_id": 1,
        "balance": 5000.0,
        "initial_balance": 5000.0,
        "position_value": 0.0,
        "total_asset": 5000.0,
    }
    assert client.get("/api/positions").json() == []

    assert client.post(
        "/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 2}
    ).status_code == 200

    account = client.get("/api/account").json()
    assert account["balance"] == pytest.approx(4748.00)
    assert account["position_value"] == pytest.approx(252.00)
    assert account["total_asset"] == pytest.approx(5000.00)

    position = client.get("/api/positions").json()[0]
    assert position == {
        "player_id": SEED_ZYWOO,
        "name": "ZywOo",
        "quantity": 2,
        "avg_cost": 126.0,
        "current_price": 126.0,
        "market_value": 252.0,
        "profit": 0.0,
        "profit_pct": 0.0,
    }
