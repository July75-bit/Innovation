"""赛程模块的**非法输入/防御分支**测试（补覆盖率，不改产品代码）。

覆盖 `code/core_engine/schedule.py` 里主路径之外的 17 行：
- 赛程文件缺失 / 内容非法（报错信息要能指导用户去跑生成脚本）
- 选手缺 `team_id` 时按队名反查；队名不存在 → 明确报错
- 未知队伍的 `resolve_team_id`
- 选手完全没有队伍信息时 `status_for` 返回 None（不抛异常）
- `expected_points` 的负数轮次校验
- 校验器：轮次错位、未知队伍、重复对局、分块不整除、空 matches、featured_round 越界

为什么值得测：这些分支决定"坏数据进来时是清晰报错还是静默算错"，
历史上前端就吃过"赛程坏了但接口仍返回价格"的亏（见 `lifecycle_issues.md`）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core_engine.schedule import (
    _check_blocks,
    _check_rounds,
    _team_id,
    load_schedule,
    matches_of_team,
    resolve_team_id,
    rounds,
    suspension_reason,
    team_names,
    validate,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = load_schedule(ROOT / "data" / "match_schedule.json")
TEAMS = team_names(SCHEDULE)  # {team_id: name}


# ---------------------------------------------------------------- 装载
def test_load_missing_file_points_to_generator(tmp_path: Path) -> None:
    """赛程文件不存在时，报错要提示去跑生成脚本（而不是裸 FileNotFoundError）。"""
    with pytest.raises(FileNotFoundError) as exc:
        load_schedule(tmp_path / "不存在.json")
    assert "build_schedule" in str(exc.value)


def test_load_invalid_payload_raises_with_reasons(tmp_path: Path) -> None:
    """赛程内容非法（空 matches）时，报错要列出校验问题。"""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"teams": {}, "matches": []}), encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        load_schedule(bad)
    assert "matches" in str(exc.value)


# ---------------------------------------------------------------- 队伍解析
def test_team_id_falls_back_to_team_name() -> None:
    """选手没有 team_id 时按队名反查；队名未知 → 明确报错。"""
    team_id, team_name = next(iter(TEAMS.items()))

    assert _team_id({"name": "甲", "team": team_name}, SCHEDULE) == team_id

    with pytest.raises(ValueError) as exc:
        _team_id({"name": "乙", "team": "不存在的队"}, SCHEDULE)
    assert "不存在的队" in str(exc.value)


def test_resolve_team_id_rejects_unknown_name() -> None:
    with pytest.raises(ValueError):
        resolve_team_id("不存在的队", SCHEDULE)


def test_suspension_reason_returns_none_without_any_team_info() -> None:
    """选手连队伍信息都没有 → 返回 None（由调用方决定如何展示），而不是抛异常。"""
    assert suspension_reason({"name": "无队选手", "status": "trading"}, 1, SCHEDULE) is None


def test_matches_of_team_rejects_negative_rounds() -> None:
    """负数轮次属于调用方 bug，必须显式报错而不是算出一个负数场次。"""
    team_id = next(iter(TEAMS))
    with pytest.raises(ValueError):
        matches_of_team(SCHEDULE, team_id, -1)


# ---------------------------------------------------------------- 校验器
def _match(round_no: int, a: int, b: int) -> dict:
    return {"round": round_no, "team_a": a, "team_b": b}


def test_check_rounds_detects_misaligned_round_field() -> None:
    """round 字段与位置不一致（第 1 场写着 round=2）要被抓出来。"""
    known = set(TEAMS)
    problems = _check_rounds([_match(2, 1, 2), _match(2, 3, 4)], known)
    assert any("round" in p for p in problems)


def test_check_rounds_detects_unknown_team() -> None:
    known = set(TEAMS)
    unknown = max(known) + 1
    problems = _check_rounds([_match(1, 1, unknown), _match(2, 3, 4)], known)
    assert any("未知" in p for p in problems)


def test_check_rounds_detects_duplicate_pair() -> None:
    known = set(TEAMS)
    problems = _check_rounds([_match(1, 1, 2), _match(2, 1, 2)], known)
    assert any("重复" in p for p in problems)


def test_check_blocks_skips_when_shape_unknown_or_uneven() -> None:
    """块校验在"队伍集合未知"或"场次不是块大小整数倍"时直接跳过（返回空）。"""
    assert _check_blocks([_match(1, 1, 2)], set(), 4) == []
    assert _check_blocks([_match(1, 1, 2), _match(2, 3, 4), _match(3, 5, 6)], {1, 2, 3, 4, 5, 6}, 4) == []


def test_check_blocks_flags_team_count_mismatch() -> None:
    """每块 4 场需要 8 支队伍；只有 6 支时要把原因写出来。"""
    known = {1, 2, 3, 4, 5, 6}
    matches = [_match(i, 1, 2) for i in range(1, 5)]
    problems = _check_blocks(matches, known, 4)
    assert problems and "8" in problems[0]


def test_validate_flags_empty_matches() -> None:
    assert validate({"teams": [], "matches": []}) == ["matches 为空"]


def test_validate_flags_featured_round_out_of_range() -> None:
    """featured_round 越界要被抓出来（前端会拿它做"本轮焦点"）。"""
    payload = {
        "teams": [{"team_id": 1, "name": "A"}, {"team_id": 2, "name": "B"}],
        "matches": [_match(1, 1, 2)],
        "featured_round": 99,
    }
    problems = validate(payload)
    assert any("featured_round" in p for p in problems)


def test_rounds_matches_matches_length() -> None:
    """rounds() 与 matches 数一致（防止赛程结构漂移）。"""
    assert rounds(SCHEDULE) == len(SCHEDULE["matches"])
