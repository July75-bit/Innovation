"""模拟比赛数据发生器。

负责人：C

用途：
1. 开发期没有真实赛事数据接口时的数据源（"数据源抽象为适配器"的适配器之一）；
2. 现场演示必须可复现：同一 seed 每次生成完全相同的比赛序列。

边界：这里只"造数据"，不改价格、不写库；
选手的基准评分由调用方从 `data/seed_players.json` 传入（本模块不硬编码任何选手）。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping, Sequence

#: 没传 base_rating 时的兜底基准评分（0-100），正常调用都应显式传入
DEFAULT_BASE_RATING = 70.0

#: 单场得分围绕基准评分的波动
DEFAULT_SCORE_STD = 7.0

_RATING_NOTES = {
    "S": "全场最佳，多次关键发挥",
    "A": "稳定发挥，节奏掌控到位",
    "B": "中规中矩，偶有失误",
    "C": "状态低迷，失误偏多",
}


@dataclass(frozen=True)
class MatchResult:
    """一场（或一局）模拟比赛的结果。"""

    player_id: int
    score: float  # 综合表现分（0-100）
    won: bool
    rating: str  # S / A / B / C
    note: str  # 人类可读说明，例如"三局两胜，场均得分最高"
    round_no: int = 0
    played_at: str = ""  # ISO 8601（UTC 口径，YYYY-MM-DD）


def _rng(seed: int | None, player_id: int, round_no: int) -> random.Random:
    """同一 (seed, player_id, round_no) 永远得到同一台随机数发生器。"""
    if seed is None:
        return random.Random()
    return random.Random(f"{seed}:{player_id}:{round_no}")


def _rating_of(score: float) -> str:
    if score >= 85:
        return "S"
    if score >= 75:
        return "A"
    if score >= 62:
        return "B"
    return "C"


def generate_match(
    player_id: int,
    *,
    seed: int | None = None,
    round_no: int = 0,
    played_at: str = "",
    base_rating: float | None = None,
) -> MatchResult:
    """生成一场模拟比赛结果。

    Args:
        player_id: 选手 ID。
        seed: 随机种子；演示时固定传值以保证可复现。
        round_no: 第几轮（参与随机种子，保证每轮不同、重跑一致）。
        played_at: 比赛日期（ISO）。
        base_rating: 该选手基准评分（0-100），应从 seed_players.json 传入。

    Returns:
        MatchResult(score, won, rating, note, round_no, played_at)。
    """
    base = DEFAULT_BASE_RATING if base_rating is None else float(base_rating)
    rng = _rng(seed, player_id, round_no)

    score = rng.gauss(base, DEFAULT_SCORE_STD)
    score = round(max(0.0, min(100.0, score)), 1)

    rating = _rating_of(score)

    # 胜负按"个人发挥相对自己平均水平"推导：高于平时更容易赢，低于平时更容易输，
    # 但保留随机性（爆冷/躺着赢都合理）。用同一个 rng，保证可复现。
    win_prob = max(0.05, min(0.95, 0.5 + (score - base) * 0.06))
    won = rng.random() < win_prob

    return MatchResult(
        player_id=player_id,
        score=score,
        won=won,
        rating=rating,
        note=_RATING_NOTES[rating],
        round_no=round_no,
        played_at=played_at,
    )


def generate_match_series(
    player_ids: Sequence[int],
    rounds: int,
    *,
    seed: int | None = None,
    start_date: str = "2026-11-01",
    base_ratings: Mapping[int, float] | None = None,
) -> list[MatchResult]:
    """生成多轮比赛序列（rounds 轮 × 每个选手一场）。

    返回顺序：轮次升序，轮内按 player_ids 顺序。
    """
    if rounds < 1:
        raise ValueError(f"rounds 必须 >= 1，收到 {rounds}")
    if not player_ids:
        return []

    start = date.fromisoformat(start_date)
    ratings: Mapping[int, float] = base_ratings or {}

    series: list[MatchResult] = []
    for round_no in range(1, rounds + 1):
        played_at = (start + timedelta(days=round_no - 1)).isoformat()
        for player_id in player_ids:
            series.append(
                generate_match(
                    player_id,
                    seed=seed,
                    round_no=round_no,
                    played_at=played_at,
                    base_rating=ratings.get(player_id),
                )
            )
    return series


def to_demand_signal(net_buy_volume: float, total_volume: float) -> float:
    """净买入量占比 → 需求信号 D(t) ∈ [-1, 1]。

    `total_volume <= 0` 时返回 0.0（避免除零）。初版 β=0，D(t) 不参与定价；
    等 B 的成交数据接进来后再启用。
    """
    if total_volume is None or not math.isfinite(float(total_volume)) or float(total_volume) <= 0:
        return 0.0
    if net_buy_volume is None or not math.isfinite(float(net_buy_volume)):
        return 0.0
    return max(-1.0, min(1.0, float(net_buy_volume) / float(total_volume)))
