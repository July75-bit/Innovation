"""市场与选手接口。

负责人：B（实现） / A（前端消费） / C（价格字段来源）

契约见 docs/software/api_contract.md §4.2 / §4.3，字段名以契约为准：
- 主键叫 player_id，不叫 id；
- 当前价叫 current_price，上一价叫 prev_price；
- change_pct 由后端算好（(current - prev) / prev × 100），前端不要自己算；
- rating 是 0–100 的项目模拟综合表现分，不是 HLTV Rating。
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Player, PriceHistory
from app.schemas.player import PlayerDetail, PlayerSummary

router = APIRouter(prefix="/players", tags=["players"])

CENT = Decimal("0.01")


def _change_pct(current: Decimal, prev: Decimal) -> float:
    if prev <= 0:
        return 0.0
    return float(((current - prev) / prev * Decimal(100)).quantize(CENT))


def _to_summary(player: Player) -> PlayerSummary:
    return PlayerSummary(
        player_id=player.player_id,
        name=player.name,
        display_name=player.display_name,
        team=player.team,
        role=player.role,
        current_price=float(player.current_price),
        prev_price=float(player.prev_price),
        change_pct=_change_pct(Decimal(player.current_price), Decimal(player.prev_price)),
        rating=int(player.rating),
        status=player.status,
    )


@router.get("", response_model=list[PlayerSummary], summary="市场选手列表")
def list_players(db: Session = Depends(get_db)) -> list[PlayerSummary]:
    """8 名选手无分页，按 player_id 升序。"""
    players = db.scalars(select(Player).order_by(Player.player_id)).all()
    return [_to_summary(player) for player in players]


@router.get("/{player_id}", response_model=PlayerDetail, summary="单个选手详情")
def get_player(player_id: int, db: Session = Depends(get_db)) -> PlayerDetail:
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    latest = db.scalars(
        select(PriceHistory)
        .where(PriceHistory.player_id == player_id)
        .order_by(PriceHistory.ts.desc(), PriceHistory.price_id.desc())
        .limit(1)
    ).first()

    summary = _to_summary(player)
    return PlayerDetail(
        **summary.model_dump(),
        latest_reason=latest.reason if latest else None,
    )
