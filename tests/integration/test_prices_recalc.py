"""`POST /api/prices/recalc` 的集成测试（第 4 天，C 负责定价与去重逻辑）。

覆盖 5 条验收口径：

1. **正常一轮**：两名选手各落一条 `price_history`，价格按 C 的公式更新，reason 带"本轮得分"；
2. **幂等**：同一份请求重放两次，第二次全部 `skipped`，库里不新增行（去重键 `(player_id, round)`）；
3. **暂停交易**：`status=suspended` 的选手被跳过，价格不变；
4. **选手不存在** → 404 `PLAYER_NOT_FOUND`；
5. **空 items** → 422（pydantic 校验）。

运行：`python -m pytest tests/integration/test_prices_recalc.py -v`
"""

from __future__ import annotations

from datetime import date

from core_engine import update_price
from sqlalchemy import select

from app.models import Player, PriceHistory

ROUND = 7
PLAYED_AT = "2026-11-07"
SEED_ZYWOO = 1
SEED_SH1RO = 7  # suspended
SEED_FLAMEZ = 8


def _payload(items: list[dict]) -> dict:
    return {"round_no": ROUND, "played_at": PLAYED_AT, "items": items}


def _history_rows(session_factory, player_id: int) -> list[PriceHistory]:
    with session_factory() as db:
        return list(
            db.scalars(
                select(PriceHistory)
                .where(PriceHistory.player_id == player_id)
                .order_by(PriceHistory.ts.asc(), PriceHistory.price_id.asc())
            ).all()
        )


def test_recalc_applies_prices_and_reason(client, session_factory) -> None:
    with session_factory() as db:
        current = float(db.get(Player, SEED_ZYWOO).current_price)
    expected = update_price(current, 0.5, score=90.0)

    resp = client.post(
        "/api/prices/recalc",
        json=_payload(
            [
                {"player_id": SEED_ZYWOO, "score": 90.0, "signal": 0.5},
                {"player_id": SEED_FLAMEZ, "score": 40.0, "signal": -1.0},
            ]
        ),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["round_no"] == ROUND
    assert [row["player_id"] for row in body["applied"]] == [SEED_ZYWOO, SEED_FLAMEZ]
    assert body["skipped"] == []

    applied = body["applied"][0]
    assert applied["old_price"] == 126.0
    assert applied["new_price"] == round(float(expected.new_price), 2)
    assert "本轮得分 90.0" in applied["reason"]
    assert "S=+0.50" in applied["reason"]

    # 落库：players 的两个价格与 price_history 新行都在
    with session_factory() as db:
        player = db.get(Player, SEED_ZYWOO)
        assert round(float(player.current_price), 2) == round(float(expected.new_price), 2)
        assert round(float(player.prev_price), 2) == 126.0

    rows = _history_rows(session_factory, SEED_ZYWOO)
    assert len(rows) == 3  # 种子 2 条 + 本轮 1 条
    assert round(float(rows[-1].price), 2) == round(float(expected.new_price), 2)
    assert rows[-1].ts.date() == date(2026, 11, 7)
    assert "本轮得分 90.0" in rows[-1].reason


def test_recalc_is_idempotent_per_round(client, session_factory) -> None:
    items = [
        {"player_id": SEED_ZYWOO, "score": 90.0, "signal": 0.5},
        {"player_id": SEED_FLAMEZ, "score": 40.0, "signal": -1.0},
    ]

    first = client.post("/api/prices/recalc", json=_payload(items))
    assert first.status_code == 200, first.text
    assert len(first.json()["applied"]) == 2

    second = client.post("/api/prices/recalc", json=_payload(items))
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["applied"] == []
    assert [row["player_id"] for row in body["skipped"]] == [SEED_ZYWOO, SEED_FLAMEZ]
    assert all("去重" in row["reason"] for row in body["skipped"])

    # 没有新增历史行，价格也没再被改
    assert len(_history_rows(session_factory, SEED_ZYWOO)) == 3
    with session_factory() as db:
        assert float(db.get(Player, SEED_ZYWOO).current_price) == round(
            float(update_price(126.0, 0.5, score=90.0).new_price), 2
        )


def test_recalc_skips_suspended_player(client, session_factory) -> None:
    resp = client.post(
        "/api/prices/recalc",
        json=_payload([{"player_id": SEED_SH1RO, "score": 70.0, "signal": 0.2}]),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["applied"] == []
    assert body["skipped"][0]["player_id"] == SEED_SH1RO
    assert "suspended" in body["skipped"][0]["reason"]

    with session_factory() as db:
        assert float(db.get(Player, SEED_SH1RO).current_price) == 136.5
    assert _history_rows(session_factory, SEED_SH1RO) == []


def test_recalc_unknown_player_returns_404(client) -> None:
    resp = client.post(
        "/api/prices/recalc",
        json=_payload([{"player_id": 999, "score": 70.0, "signal": 0.2}]),
    )

    assert resp.status_code == 404
    assert resp.json()["code"] == "PLAYER_NOT_FOUND"


def test_recalc_rejects_empty_items(client) -> None:
    resp = client.post(
        "/api/prices/recalc",
        json={"round_no": ROUND, "played_at": PLAYED_AT, "items": []},
    )

    assert resp.status_code == 422
