"""价格历史响应模型（契约 §4.4）。

结构固定为 {player_id, points: [...]}，points 按 ts 升序；空历史返回 points: []。

另含第 4 天新增的赛后结算模型（`POST /api/prices/recalc`）：请求带一轮的
`(score, signal)`，响应区分 `applied` 与 `skipped`（暂停交易 / 重复轮次）。
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import UtcDateTime


class PricePoint(BaseModel):
    ts: UtcDateTime
    price: float
    reason: str


class PriceHistoryResponse(BaseModel):
    player_id: int
    points: list[PricePoint]


class PriceRecalcItem(BaseModel):
    """一名选手这一轮的输入：原始得分（用于 reason）+ 标准化信号 S（用于定价）。"""

    player_id: int
    score: float = Field(ge=0, le=100, description="本轮原始得分 0-100")
    signal: float = Field(ge=-1, le=1, description="标准化表现信号 S(t)")


class PriceRecalcRequest(BaseModel):
    round_no: int = Field(ge=1, description="轮次，从 1 开始")
    played_at: date = Field(description="比赛日期，写入 price_history.ts 并作为轮次去重键")
    items: list[PriceRecalcItem] = Field(min_length=1, description="本轮参与的选手")


class PriceRecalcApplied(BaseModel):
    player_id: int
    old_price: float
    new_price: float
    change_pct: float
    reason: str


class PriceRecalcSkipped(BaseModel):
    player_id: int
    reason: str


class PriceRecalcResponse(BaseModel):
    round_no: int
    applied: list[PriceRecalcApplied]
    skipped: list[PriceRecalcSkipped]
