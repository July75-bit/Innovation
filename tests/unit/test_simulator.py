"""模拟比赛数据的可复现性测试（TC-106 / FR-M2-01）。

负责人：C

对应 `docs/acceptance/test_plan.md` 的 TC-106：「同 seed 跑两次 → 结果完全一致」。
答辩现场的价格曲线之所以敢说"可复现"，靠的就是这三条断言：

1. 同一 seed 连续生成两次，比赛序列逐条相等（含得分、胜负、评级、轮次、日期）；
2. 单场比赛用同一 (seed, player_id, round_no) 生成两次，结果相等；
3. 换一个 seed 必须得到不同结果（防止"假复现"——比如函数忽略了 seed 参数）。

运行方式：
- pytest（仓库根目录）：`python -m pytest tests/unit/test_simulator.py -v`
- 零依赖直跑：`python tests/unit/test_simulator.py`
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from core_engine import generate_match, generate_match_series  # noqa: E402

PLAYER_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
BASE_RATINGS = {pid: 80.0 for pid in PLAYER_IDS}
ROUNDS = 5


def _series(seed: int):
    return generate_match_series(
        PLAYER_IDS, ROUNDS, seed=seed, base_ratings=BASE_RATINGS
    )


def test_same_seed_reproduces_identical_series() -> None:
    """同 seed 跑两次：比赛序列必须逐条相等（TC-106 的核心断言）。"""
    first = _series(42)
    second = _series(42)

    assert len(first) == ROUNDS * len(PLAYER_IDS)
    assert first == second, "同一 seed 两次生成的比赛序列必须完全一致"

    # 逐字段抽查，失败时能直接看出是哪一项漂了
    for a, b in zip(first, second):
        assert (a.player_id, a.round_no) == (b.player_id, b.round_no)
        assert a.score == b.score
        assert a.won == b.won
        assert a.rating == b.rating
        assert a.played_at == b.played_at


def test_same_seed_single_match_is_stable() -> None:
    """单场：同一 (seed, player_id, round_no) 生成两次结果相等。"""
    one = generate_match(3, seed=42, round_no=2, base_rating=80.0)
    another = generate_match(3, seed=42, round_no=2, base_rating=80.0)

    assert one == another
    assert one.score == another.score


def test_different_seed_changes_results() -> None:
    """换 seed 必须得到不同序列，否则说明 seed 根本没生效（假复现）。"""
    assert _series(42) != _series(43), "不同 seed 应生成不同比赛"


# ---------------------------------------------------------------- 零依赖运行器
def _run_all() -> int:
    """没有 pytest 也能跑（课程环境/CI 未装依赖时用）。"""
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failed = 0
    print(f"运行 {len(tests)} 个模拟器测试 …\n")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {exc}")
    print(f"\n结果：{len(tests) - failed}/{len(tests)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
