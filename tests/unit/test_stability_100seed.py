"""100 seed 稳定性脚本（`scripts/stability_100seed.py`）的冒烟测试。

负责人：C

守两件事：

1. **可复现**：同一组参数跑两次，`per_seed` 明细必须逐条相同（`generated_at` 除外）；
2. **口径正确**：每 seed 的更新条数 = 轮次 × 12（每轮 2 队 4 人停牌），且 CLI 能落 JSON。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import stability_100seed  # noqa: E402


def test_small_study_is_deterministic_and_well_formed() -> None:
    """2 seed × 2 轮：结构完整、同参数两次一致、条数 = 轮次 × 12。"""
    kwargs = {"seeds": 2, "rounds": 2, "window": 5, "warmup": 3, "alphas": (0.15,)}
    first = stability_100seed.run_study(**kwargs)
    second = stability_100seed.run_study(**kwargs)

    assert first["per_seed"] == second["per_seed"], "同参数两次 per_seed 应完全一致"
    assert first["config"]["seeds"] == 2
    assert len(first["per_seed"]) == 2
    assert first["aggregate"]["points_per_seed"] == [24], "2 轮 × 12 人 = 24 条"
    assert first["alpha_sensitivity"][0]["alpha"] == 0.15
    assert 0 < first["aggregate"]["mean_consistency_pct"] <= 100


def test_cli_writes_json(tmp_path: Path) -> None:
    """CLI 能跑通并把完整结果写进 JSON。"""
    out = tmp_path / "study.json"
    code = stability_100seed.main(
        ["--seeds", "2", "--rounds", "2", "--alphas", "0.15", "--json", str(out)]
    )

    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["config"]["rounds"] == 2
    assert len(payload["per_seed"]) == 2
    assert payload["aggregate"]["mean_consistency_pct"] >= 99.0


def test_rejects_non_positive_seeds() -> None:
    """--seeds 0 应显式报错（返回 2），而不是跑出空结果。"""
    assert stability_100seed.main(["--seeds", "0"]) == 2
