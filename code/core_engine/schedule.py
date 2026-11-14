"""赛程与「可交易状态」派生（队伍 × 轮次）。

负责人：C（第 7 天：把「单人常驻暂停」升级为「队伍级派生暂停」）

设计要点
--------
- **状态是派生值，不是存储值**：`players.status` 只表示"开赛前/当前"的初始状态；
  第 N 轮到底能不能交易，由 `status_for(player, round_no, schedule)` 现算。
  这样不需要每轮改库，也不会和 `(player_id, round)` 的去重逻辑打架。
- **每轮一场比赛**：参赛两队（每队 2 人）在该轮暂停交易，其余选手正常定价。
- **确定性 + 均衡**：赛程来自 `data/match_schedule.json`（圆桌法生成），
  每 4 轮 8 队各出场一次 → 每人被暂停轮次数一致，点数可直接算：`2 + 3k`。
- **超长轮次循环**：`round_no` 超出赛程长度时按 `(round_no - 1) % 轮数` 循环，
  保证回测跑到 30/32 轮也有确定的对手，不会"没人比赛"。

数据形状（data/match_schedule.json）::

    {"schema_version": 1,
     "teams": [{"team_id": 1, "name": "Vitality"}],
     "matches": [{"round": 1, "played_at": "2026-11-01", "team_a": 1, "team_b": 5}]}

用法::

    from core_engine import load_schedule, status_for, tradable_players

    schedule = load_schedule()
    status_for(player, 12, schedule)          # "trading" / "suspended"
    tradable_players(players, 12, schedule)   # 当轮可交易的 12 人
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

DEFAULT_SCHEDULE_PATH = Path(__file__).resolve().parents[2] / "data" / "match_schedule.json"
SUSPENDED = "suspended"
TRADING = "trading"


# ---------------------------------------------------------------- 装载
def load_schedule(path: str | Path | None = None) -> dict:
    """读取赛程文件；不传路径就用仓库里的 `data/match_schedule.json`。"""
    target = Path(path) if path else DEFAULT_SCHEDULE_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"找不到赛程文件 {target}：先跑 python scripts/build_schedule.py"
        )
    payload = json.loads(target.read_text(encoding="utf-8"))
    problems = validate(payload)
    if problems:
        raise ValueError("赛程文件不合法：\n  - " + "\n  - ".join(problems))
    return payload


# ---------------------------------------------------------------- 基础查询
def rounds(schedule: Mapping[str, Any]) -> int:
    return len(schedule["matches"])


def team_names(schedule: Mapping[str, Any]) -> dict[int, str]:
    return {int(t["team_id"]): t["name"] for t in schedule.get("teams", [])}


def round_match(schedule: Mapping[str, Any], round_no: int) -> dict:
    """第 round_no 轮的那场比赛；超过赛程长度时循环。"""
    if not isinstance(round_no, int) or round_no < 1:
        raise ValueError(f"round_no 必须是 >= 1 的整数，收到 {round_no!r}")
    matches = schedule["matches"]
    return matches[(round_no - 1) % len(matches)]


def playing_teams(schedule: Mapping[str, Any], round_no: int) -> set[int]:
    """这一轮正在比赛的两支队伍（它们整队暂停交易）。"""
    match = round_match(schedule, round_no)
    return {int(match["team_a"]), int(match["team_b"])}


def _team_id(player: Mapping[str, Any], schedule: Mapping[str, Any]) -> int:
    """优先用 team_id；没有就按队伍名反查（兼容旧数据）。"""
    if player.get("team_id") is not None:
        return int(player["team_id"])
    by_name = {name: tid for tid, name in team_names(schedule).items()}
    team = player.get("team")
    if team not in by_name:
        raise ValueError(f"选手 {player.get('name')} 的队伍 {team!r} 不在赛程里")
    return by_name[team]


# ---------------------------------------------------------------- 状态派生
def status_for(player: Mapping[str, Any], round_no: int, schedule: Mapping[str, Any]) -> str:
    """第 round_no 轮这名选手的状态：队伍在比赛 → suspended，否则 trading。"""
    return SUSPENDED if _team_id(player, schedule) in playing_teams(schedule, round_no) else TRADING


def tradable_players(
    players: Iterable[Mapping[str, Any]], round_no: int, schedule: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    return [p for p in players if status_for(p, round_no, schedule) == TRADING]


def suspended_players(
    players: Iterable[Mapping[str, Any]], round_no: int, schedule: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    return [p for p in players if status_for(p, round_no, schedule) == SUSPENDED]


# ---------------------------------------------------------------- 管线复用的判定
def resolve_team_id(team: int | str, schedule: Mapping[str, Any]) -> int:
    """队伍编号或队伍名 → team_id（兼容 ORM 只有 `team` 字符串的场景）。"""
    if isinstance(team, int) or (isinstance(team, str) and team.isdigit()):
        return int(team)
    by_name = {name: tid for tid, name in team_names(schedule).items()}
    if team not in by_name:
        raise ValueError(f"队伍 {team!r} 不在赛程里")
    return by_name[team]


def match_of_team(
    team: int | str, round_no: int, schedule: Mapping[str, Any]
) -> dict | None:
    """这名选手所在队伍这一轮的比赛（不比赛返回 None）。"""
    team_id = resolve_team_id(team, schedule)
    match = round_match(schedule, round_no)
    return match if team_id in {int(match["team_a"]), int(match["team_b"])} else None


def team_playing(team: int | str, round_no: int, schedule: Mapping[str, Any]) -> bool:
    """队伍这一轮是否在比赛（= 整队暂停交易）。"""
    return match_of_team(team, round_no, schedule) is not None


def suspension_reason(
    player: Mapping[str, Any], round_no: int, schedule: Mapping[str, Any]
) -> str | None:
    """这一轮为什么不能交易；可交易返回 None。

    两类来源，**手动 status 优先**（运维临时冻结仍然有效）：
    1. `player["status"] != "trading"` → "状态 X（手动暂停）"；
    2. 队伍这一轮有比赛 → "Vitality vs Spirit 比赛中，暂停交易"。
    """
    status = str(player.get("status", TRADING))
    if status != TRADING:
        return f"状态 {status}（手动暂停）"

    team = player.get("team_id", player.get("team"))
    if team is None:
        return None
    match = match_of_team(team, round_no, schedule)
    if match is None:
        return None
    names = team_names(schedule)
    team_id = resolve_team_id(team, schedule)
    opponent = int(match["team_b"]) if int(match["team_a"]) == team_id else int(match["team_a"])
    return f"{names[team_id]} vs {names[opponent]} 比赛中，暂停交易"


# ---------------------------------------------------------------- 点数与校验
def matches_of_team(
    schedule: Mapping[str, Any], team_id: int, total_rounds: int | None = None
) -> int:
    """这支队伍在前 total_rounds 轮里打了几场（即被暂停几轮）。"""
    total = total_rounds or rounds(schedule)
    if total < 0:
        raise ValueError(f"total_rounds 不能为负，收到 {total}")
    return sum(1 for r in range(1, total + 1) if team_id in playing_teams(schedule, r))


def expected_points(
    schedule: Mapping[str, Any],
    team_id: int,
    total_rounds: int,
    seed_points: int = 2,
) -> int:
    """这支队伍的选手在 total_rounds 轮后应有的价格点数。

    = 种子点（初始价格 + 行情初始化，默认 2） + 可交易轮次数
    """
    return seed_points + total_rounds - matches_of_team(schedule, team_id, total_rounds)


def _check_rounds(matches: list[dict], known: set[int]) -> list[str]:
    """逐轮检查：轮次连续、两队不相同、队伍已知、对局不重复。"""
    problems: list[str] = []
    seen_pairs: set[tuple[int, int]] = set()
    for index, match in enumerate(matches, start=1):
        if int(match.get("round", -1)) != index:
            problems.append(f"第 {index} 条的 round 字段不连续：{match.get('round')}")
        sides = [int(match.get("team_a", -1)), int(match.get("team_b", -1))]
        if sides[0] == sides[1]:
            problems.append(f"第 {index} 轮同一支队打自己：{sides}")
        elif known and not set(sides) <= known:
            problems.append(f"第 {index} 轮出现未知队伍：{sides}")
        pair = tuple(sorted(sides))
        if pair in seen_pairs:
            problems.append(f"重复对局：{pair}")
        seen_pairs.add(pair)
    return problems


def _check_blocks(matches: list[dict], known: set[int], block: int) -> list[str]:
    """每 `block` 轮应覆盖全部队伍一次（不足一组的部分不检查）。"""
    total = len(matches)
    if not known or total % block:
        return []
    if 2 * block != len(known):
        return [f"每 {block} 轮只有 {2 * block} 个出场名额，与 {len(known)} 支队不匹配"]

    problems: list[str] = []
    for start in range(0, total, block):
        appeared: set[int] = set()
        for match in matches[start : start + block]:
            appeared.update({int(match["team_a"]), int(match["team_b"])})
        if appeared != known:
            missing = sorted(known - appeared)
            problems.append(f"第 {start + 1}–{start + block} 轮没有覆盖全部队伍：缺 {missing}")
    return problems


def validate(schedule: Mapping[str, Any], block: int = 4) -> list[str]:
    """结构校验；返回问题列表（空表示通过）。"""
    matches = schedule.get("matches")
    if not matches:
        return ["matches 为空"]

    known = set(team_names(schedule))
    problems: list[str] = [] if known else ["缺少 teams[]，无法校验队伍编号"]
    problems += _check_rounds(matches, known)
    problems += _check_blocks(matches, known, block)

    featured = schedule.get("featured_round")
    if featured is not None and not (1 <= int(featured) <= len(matches)):
        problems.append(f"featured_round={featured} 超出 1–{len(matches)}")
    return problems


__all__ = [
    "DEFAULT_SCHEDULE_PATH",
    "SUSPENDED",
    "TRADING",
    "expected_points",
    "load_schedule",
    "match_of_team",
    "matches_of_team",
    "playing_teams",
    "resolve_team_id",
    "round_match",
    "rounds",
    "status_for",
    "suspension_reason",
    "suspended_players",
    "team_names",
    "team_playing",
    "tradable_players",
    "validate",
]
