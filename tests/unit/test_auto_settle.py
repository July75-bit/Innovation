"""惰性自动结算（app/core/auto_settle.py）单元测试。

重点考察：
1. **链条复现**：用部署侧镜像名单（DEMO_ROSTER）从基线补算第 1..12 轮，
   选手 3（m0NESY）2026-11-12 的价格必须等于 77.79——那是同 seed bootstrap
   实测落库、且 scripts/settle_round.py 已与线上库比对过的锚点；
   后端自己的重放若与 simulate_match 链条有任何偏差，这条必红；
2. 停牌规则：本轮有比赛的队伍选手，当天不应有点；
3. 幂等：同一"今天"再跑不新增；AUTO_SETTLE=0 时直接 off；
4. 空库不造数据（empty-db）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.core import auto_settle
from app.core.auto_settle import settle_if_due
from app.core.database import Base
from app.core.demo_roster import DEMO_ROSTER
from app.models import Player, PriceHistory


@pytest.fixture()
def settle_db(tmp_path, monkeypatch):
    """16 名镜像选手 + 10-31 基线点；开关打开，as_of 由用例指定。"""
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'settle.db').as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    with factory() as db:
        for p in DEMO_ROSTER:
            db.add(
                Player(
                    player_id=int(p["player_id"]),
                    name=str(p["name"]),
                    display_name=str(p.get("display_name") or p["name"]),
                    team=str(p["team"]),
                    role=str(p.get("role") or ""),
                    current_price=Decimal(str(p["current_price"])),
                    prev_price=Decimal(str(p["initial_price"])),
                    rating=int(p["rating"]),
                    status=str(p["status"]),
                )
            )
            db.add(
                PriceHistory(
                    player_id=int(p["player_id"]),
                    price=Decimal(str(p["current_price"])),
                    reason="行情初始化（测试）",
                    ts=datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc),
                )
            )
        db.commit()

    s = auto_settle.settings
    monkeypatch.setattr(s, "auto_settle", True, raising=False)
    monkeypatch.setattr(s, "auto_settle_min_interval", 0, raising=False)
    monkeypatch.setattr(auto_settle, "_last_check", None)
    yield factory
    engine.dispose()


def price_of(db, player_id: int, day: str) -> Decimal | None:
    ts = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return db.scalar(
        select(PriceHistory.price).where(
            PriceHistory.player_id == player_id,
            PriceHistory.ts >= ts,
            PriceHistory.ts < ts + timedelta(days=1),
        )
    )


def count_of(db, player_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(PriceHistory.price_id)).where(
                PriceHistory.player_id == player_id
            )
        )
    )


def test_settles_12_rounds_matching_bootstrap_chain(settle_db, monkeypatch):
    """补到 11-12（第 12 轮）：m0NESY 当天应等于 bootstrap 链条实测值 77.79。"""
    monkeypatch.setattr(auto_settle.settings, "auto_settle_as_of", "2026-11-12", raising=False)
    with settle_db() as db:
        result = settle_if_due(db, force=True)
        assert result == "settled:12", result
        # 锚点：与 scripts/settle_round.py 上线验证过的同一链条
        assert price_of(db, 3, "2026-11-12") == Decimal("77.79")
        # m0NESY（Falcons）前 12 轮打了 3 场（r3/r8/r9，圆桌法允许连续出场）→ 停牌 3 轮
        # → 引擎点 12-3=9 + 基线 1 = 10 个点（与线上库第 12 轮后实测一致）
        assert count_of(db, 3) == 10

        # 再跑一次同样日期：无事发生（幂等）
        assert settle_if_due(db, force=True) == "up-to-date"
        assert count_of(db, 3) == 10

def test_suspended_team_has_no_point_on_match_day(settle_db, monkeypatch):
    """先补到 11-12，再快进到 11-13：第 13 轮 Vitality vs NAVI（选手 1/8/6/10 停牌）。"""
    with settle_db() as db:
        monkeypatch.setattr(auto_settle.settings, "auto_settle_as_of", "2026-11-12", raising=False)
        settle_if_due(db, force=True)
        monkeypatch.setattr(auto_settle.settings, "auto_settle_as_of", "2026-11-13", raising=False)
        assert settle_if_due(db, force=True) == "settled:1"

        # ZywOo/flameZ（Vitality #1,#8）与 jL/w0nderful（NAVI #6,#10）当天无点
        assert price_of(db, 1, "2026-11-13") is None
        assert price_of(db, 8, "2026-11-13") is None
        assert price_of(db, 6, "2026-11-13") is None
        # m0NESY 没比赛 → 有
        assert price_of(db, 3, "2026-11-13") is not None
        # G2 的 Snax(#12) 也没比赛 → 有
        assert price_of(db, 12, "2026-11-13") is not None


def test_off_by_default(settle_db, monkeypatch):
    """AUTO_SETTLE=0（缺省）：入口直接 off，一条都不写。"""
    monkeypatch.setattr(auto_settle.settings, "auto_settle", False, raising=False)
    with settle_db() as db:
        before = count_of(db, 1)
        assert settle_if_due(db, force=True) == "off"
        assert count_of(db, 1) == before


def test_throttle_skips_second_call(settle_db, monkeypatch):
    """间隔闸门：force 检查过之后，非 force 调用应被 throttled。"""
    monkeypatch.setattr(auto_settle.settings, "auto_settle_as_of", "2026-11-12", raising=False)
    monkeypatch.setattr(auto_settle.settings, "auto_settle_min_interval", 3600, raising=False)
    with settle_db() as db:
        assert settle_if_due(db, force=True) == "settled:12"
        assert settle_if_due(db) == "throttled"


def test_empty_db_not_touched(settle_db):
    """空库（没有任何 price_history）不补：留给 reseed，避免凭空造基线。"""
    with settle_db() as db:
        db.query(PriceHistory).delete()
        db.commit()
        assert settle_if_due(db, force=True) == "empty-db"
        assert int(db.scalar(select(func.count(PriceHistory.price_id)))) == 0
