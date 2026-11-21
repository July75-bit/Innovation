"""赛程与队伍级暂停派生（第 7 天批次一）。

守住的契约：

1. 赛程结构：28 轮单循环、每轮 2 支不同队伍、每对只打一次；
2. 均衡性：任意 4 轮的前缀覆盖全部 8 队 → 每人点数 = 2（种子点）+ 3k；
3. 派生：队伍在比赛 → `suspended`，否则 `trading`；16 人里 4 暂停 / 12 可交易；
4. 循环：第 29 轮等同第 1 轮（回测跑到 30+ 轮也不会"没人比赛"）；
5. 数据：seed 升到 v5（8 队 × 2 人、每人有 `team_id`、没有常驻暂停）；
6. 校验器：坏赛程能被 `validate()` 抓出来。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_engine.schedule import (
    SUSPENDED,
    TRADING,
    expected_points,
    load_schedule,
    matches_of_team,
    playing_teams,
    round_match,
    rounds,
    status_for,
    suspended_players,
    team_names,
    tradable_players,
    validate,
)

ROOT = Path(__file__).resolve().parents[2]
SEED = json.loads((ROOT / "data" / "seed_players.json").read_text(encoding="utf-8"))
SCHEDULE = load_schedule(ROOT / "data" / "match_schedule.json")
PLAYERS = SEED["players"]
TEAMS = team_names(SCHEDULE)


def test_schedule_has_28_rounds_of_two_distinct_teams() -> None:
    assert rounds(SCHEDULE) == 28
    for match in SCHEDULE["matches"]:
        sides = {match["team_a"], match["team_b"]}
        assert len(sides) == 2, f"第 {match['round']} 轮有两支相同的队伍"
        assert sides <= set(TEAMS)


def test_each_pair_plays_exactly_once() -> None:
    pairs = [tuple(sorted((m["team_a"], m["team_b"]))) for m in SCHEDULE["matches"]]
    assert len(pairs) == 28  # C(8,2)
    assert len(set(pairs)) == 28


def test_every_four_round_block_covers_all_teams() -> None:
    known = set(TEAMS)
    for start in range(0, rounds(SCHEDULE), 4):
        appeared: set[int] = set()
        for match in SCHEDULE["matches"][start : start + 4]:
            appeared |= {match["team_a"], match["team_b"]}
        assert appeared == known, f"第 {start + 1} 轮起的 4 轮没有覆盖全部队伍"


def test_featured_round_is_vitality_vs_spirit() -> None:
    featured = SCHEDULE["featured_round"]
    assert featured == 12
    assert playing_teams(SCHEDULE, featured) == {1, 2}


def test_status_splits_four_suspended_and_twelve_tradable() -> None:
    round_no = SCHEDULE["featured_round"]
    playing = playing_teams(SCHEDULE, round_no)

    suspended = suspended_players(PLAYERS, round_no, SCHEDULE)
    tradable = tradable_players(PLAYERS, round_no, SCHEDULE)
    assert len(suspended) == 4
    assert len(tradable) == 12
    assert {p["team"] for p in suspended} == {"Vitality", "Spirit"}

    for player in PLAYERS:
        expected = SUSPENDED if player["team_id"] in playing else TRADING
        assert status_for(player, round_no, SCHEDULE) == expected


def test_expected_points_after_twelve_and_twenty_eight_rounds() -> None:
    for team_id in TEAMS:
        assert matches_of_team(SCHEDULE, team_id, 12) == 3
        assert expected_points(SCHEDULE, team_id, 12) == 11  # 2 种子点 + 9 可交易轮
    assert expected_points(SCHEDULE, 1, 28) == 23  # 2 + 21


def test_round_cycles_beyond_schedule_length() -> None:
    assert round_match(SCHEDULE, 29) == round_match(SCHEDULE, 1)
    assert playing_teams(SCHEDULE, 29) == playing_teams(SCHEDULE, 1)


def test_validate_catches_broken_schedule() -> None:
    broken = json.loads(json.dumps(SCHEDULE))
    broken["matches"][0]["team_b"] = broken["matches"][0]["team_a"]
    problems = validate(broken)
    assert any("打自己" in problem for problem in problems)


def test_invalid_round_number_raises() -> None:
    with pytest.raises(ValueError):
        round_match(SCHEDULE, 0)
    with pytest.raises(ValueError):
        round_match(SCHEDULE, 1.5)  # type: ignore[arg-type]


def test_seed_v5_is_sixteen_players_in_eight_teams() -> None:
    assert SEED["schema_version"] == 5
    assert len(SEED["teams"]) == 8
    assert len(PLAYERS) == 16

    counts: dict[str, int] = {}
    for player in PLAYERS:
        assert player["team_id"] in TEAMS
        assert TEAMS[player["team_id"]] == player["team"]
        counts[player["team"]] = counts.get(player["team"], 0) + 1
    assert set(counts.values()) == {2}

    # 取消「常驻暂停」：暂停改由赛程逐轮派生，seed 里不应再有 suspended
    assert {p["status"] for p in PLAYERS} == {"trading"}
