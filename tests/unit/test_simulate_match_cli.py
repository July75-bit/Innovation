"""scripts/simulate_match.py 的 CLI 冒烟测试。

负责人：C

对应第 3 天验收项「命令行 8 条变化及原因」：

- 8 名选手中 1 名 `suspended`，因此固定 seed 下应打印 **7 条价格更新 + 1 条跳过**；
- 每条更新都必须带中文 `reason`（答辩要拆解归因）；
- `--json` 导出的 `ts` 必须是 UTC ISO 8601（以 `Z` 结尾），交给 B 直接落 `price_history.ts`。

运行方式：
- pytest：`python -m pytest tests/unit/test_simulate_match_cli.py -v`
- 想跳过 conftest（本机没装 fastapi 时）：`python -m pytest tests/unit/test_simulate_match_cli.py --noconftest -q`
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "simulate_match.py"


@pytest.fixture()
def script_module():
    """把脚本当模块加载（它自己会 sys.path 指向 code/，无需 subprocess）。"""
    spec = importlib.util.spec_from_file_location("simulate_match_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(module, argv: list[str]) -> str:
    """跑一次 main()，返回打印到 stdout 的内容。"""
    buffer = io.StringIO()
    original = sys.argv
    sys.argv = ["simulate_match.py", *argv]
    try:
        with contextlib.redirect_stdout(buffer):
            module.main()
    finally:
        sys.argv = original
    return buffer.getvalue()


def test_cli_prints_one_line_per_trading_player(script_module) -> None:
    output = _run_main(script_module, ["--seed", "42"])

    assert "模拟比赛：1 轮 × 8 名选手（seed=42）" in output
    assert "状态 suspended，本轮跳过定价" in output  # sh1ro 停赛跳过
    assert "共 7 条价格更新" in output               # 8 人 − 1 名停赛
    assert output.count("评分") == 7                 # 每名可交易选手一行
    assert output.count("｜") == 7                   # 每行都带中文 reason


def test_cli_json_export_uses_iso_utc_ts(script_module, tmp_path) -> None:
    target = tmp_path / "updates.json"
    _run_main(script_module, ["--seed", "42", "--json", str(target)])

    payload = json.loads(target.read_text(encoding="utf-8"))
    updates = payload["updates"]

    assert payload["seed"] == 42
    assert len(updates) == 7
    assert all(item["reason"] for item in updates)
    assert all(item["ts"].endswith("Z") and "T" in item["ts"] for item in updates)
