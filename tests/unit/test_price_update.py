"""价格更新落库（T3-01）的测试。

负责人：B

守三件事：
1. **写得对**：`players.current_price/prev_price` 与 `price_history` 同步变化，
   涨跌幅用落库的两个价格现算，`/prices` 升序、每点带中文 `reason`；
2. **不越界**：本模块只碰 `players` 与 `price_history`，余额与持仓一动不动
   （`database_design.md` §3 的 C/B 边界，违反就是事故）；
3. **失败即回滚**：一批里任何一条非法，整批都不落库。

定价公式本身是 C 的资产，这里用假的计算器（stub）替代，不测公式。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.core.price_update import (
    PlannedUpdate,
    apply_updates,
    plan_for_player,
    plan_updates,
    price_history_count,
    touched_tables,
)

SEED_ZYWOO = 1


@dataclass(frozen=True)
class FakePriceUpdate:
    """替代 C 的 `PriceUpdate`：字段和用法完全一样。"""

    new_price: float
    change_pct: float
    reason: str


def _calc(new_price: float, reason: str = "模拟比赛表现提升（S=+0.42）"):
    return lambda current_price: FakePriceUpdate(
        new_price=new_price, change_pct=0.0, reason=reason
    )


def test_touched_tables_are_players_and_history_only() -> None:
    """白纸黑字声明边界：价格更新只允许碰这两张表。"""
    assert touched_tables() == ("players", "price_history")


def test_plan_recomputes_change_pct_from_prices(session_factory) -> None:
    """涨跌幅必须用落库的两个价格现算，不信计算器返回的值。"""
    with session_factory() as db:
        from app.models import Player

        player = db.get(Player, SEED_ZYWOO)
        planned = plan_for_player(player, _calc(133.00))

    # 126.00 → 133.00 = +5.5555...% → 四舍五入两位 = 5.56
    assert planned.old_price == Decimal("126.00")
    assert planned.new_price == Decimal("133.00")
    assert planned.change_pct == pytest.approx(5.56)


def test_plan_rejects_bad_price_or_reason(session_factory) -> None:
    """新价 <= 0、reason 为空或超长，都要在写库前就被拒绝。"""
    with session_factory() as db:
        from app.models import Player

        player = db.get(Player, SEED_ZYWOO)

        with pytest.raises(ValueError, match="新价非法"):
            plan_for_player(player, _calc(0.0))

        with pytest.raises(ValueError, match="缺少 reason"):
            plan_for_player(player, _calc(130.0, reason="   "))

        with pytest.raises(ValueError, match="超过 200"):
            plan_for_player(player, _calc(130.0, reason="涨" * 201))


def test_apply_updates_writes_price_and_history(session_factory, client) -> None:
    """一次落库：current/prev 换位、历史多一个点，接口返回升序且带 reason。"""
    before = client.get(f"/api/players/{SEED_ZYWOO}/prices").json()["points"]
    assert len(before) == 2

    with session_factory() as db:
        from app.models import Player

        player = db.get(Player, SEED_ZYWOO)
        planned = plan_updates([player], _calc(130.00))
        applied = apply_updates(db, planned)
    assert len(applied) == 1

    with session_factory() as db:
        from app.models import Player

        db.expire_all()
        player = db.get(Player, SEED_ZYWOO)
        assert Decimal(player.current_price).quantize(Decimal("0.01")) == Decimal("130.00")
        # prev_price 取的是数据库里"更新前"的当前价
        assert Decimal(player.prev_price).quantize(Decimal("0.01")) == Decimal("126.00")
        assert price_history_count(db, SEED_ZYWOO) == 3

    after = client.get(f"/api/players/{SEED_ZYWOO}/prices").json()["points"]
    assert len(after) == 3
    assert [p["price"] for p in after] == [120.0, 126.0, 130.0]  # 升序
    assert all(p["reason"] for p in after), "每个点都必须带 reason"
    assert "模拟" in after[-1]["reason"], "reason 必须是可读中文"

    # 详情页的 change_pct 也跟着变了：(130-126)/126 = +3.17%
    detail = client.get(f"/api/players/{SEED_ZYWOO}").json()
    assert detail["current_price"] == 130.00
    assert detail["prev_price"] == 126.00
    assert detail["change_pct"] == pytest.approx(3.17)


def test_apply_updates_never_touches_balance_or_positions(session_factory, client) -> None:
    """C/B 边界：价格更新绝不能改余额和持仓。

    注意区分两件事：`balance` 与持仓的 `quantity` / `avg_cost` 必须**一动不动**；
    而 `position_value` / `total_asset` 本来就该随价格重估（这正是"按市价计"的含义），
    所以它们变化是对的。
    """
    assert client.post(
        "/api/trades/buy", json={"player_id": SEED_ZYWOO, "quantity": 2}
    ).status_code == 200
    account_before = client.get("/api/account").json()
    positions_before = client.get("/api/positions").json()
    assert account_before["balance"] == pytest.approx(4748.00)
    assert account_before["position_value"] == pytest.approx(252.00)

    with session_factory() as db:
        from app.models import Player

        planned = plan_updates([db.get(Player, SEED_ZYWOO)], _calc(140.00))
        apply_updates(db, planned)

    account_after = client.get("/api/account").json()
    # 钱和股数不许动
    assert account_after["balance"] == account_before["balance"]
    assert account_after["initial_balance"] == account_before["initial_balance"]
    assert account_after["user_id"] == account_before["user_id"]

    positions_after = client.get("/api/positions").json()
    assert positions_after[0]["quantity"] == positions_before[0]["quantity"] == 2
    assert positions_after[0]["avg_cost"] == pytest.approx(126.00)
    # 市值按新价重估：2 股 × 140.00 = 280.00，浮盈 28.00
    assert positions_after[0]["current_price"] == 140.00
    assert positions_after[0]["market_value"] == pytest.approx(280.00)
    assert positions_after[0]["profit"] == pytest.approx(28.00)
    assert account_after["position_value"] == pytest.approx(280.00)
    assert account_after["total_asset"] == pytest.approx(4748.00 + 280.00)


def test_apply_updates_rolls_back_whole_batch(session_factory) -> None:
    """一批里有一条非法 → 整批回滚，前面已经 UPDATE 的也要撤销。"""
    with session_factory() as db:
        from app.models import Player

        players = list(db.query(Player).order_by(Player.player_id).all())
        good = plan_for_player(players[0], _calc(130.00))
        bad = PlannedUpdate(
            player_id=players[1].player_id,
            name=players[1].name,
            old_price=Decimal("105.00"),
            new_price=Decimal("0.00"),  # 违反 CHECK (current_price > 0)
            change_pct=-100.0,
            reason="故意非法的一条",
        )

        with pytest.raises(Exception):
            apply_updates(db, [good, bad])

    with session_factory() as db:
        from app.models import Player

        db.expire_all()
        first = db.get(Player, SEED_ZYWOO)
        # 第一条的 UPDATE 必须被回滚
        assert Decimal(first.current_price).quantize(Decimal("0.01")) == Decimal("126.00")
        assert Decimal(first.prev_price).quantize(Decimal("0.01")) == Decimal("120.00")
        assert price_history_count(db, SEED_ZYWOO) == 2
