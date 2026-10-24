"""一键灌数脚本（`scripts/bootstrap_demo_data.py`）的集成测试。

负责人：B

守的是"演示数据可复现"这件事本身：换一台机器 / 换一个库（本地 SQLite 或 Render Postgres），
只要跑同一条命令，就能得到「每名可交易选手都有 >= N 个价格点」的同一套数据
（同 seed 完全一致，见 `database_design.md` §4.1 / §4.2）。

测试用独立临时库，不碰仓库里的 `playerstock.db`。
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap_demo_data.py"


class BootstrapRun(NamedTuple):
    returncode: int
    output: str  # 已按 UTF-8 解码，坏字节替换为 \ufffd，不会抛异常


def _run_bootstrap(db_path: Path, *extra: str) -> BootstrapRun:
    """用独立 DATABASE_URL 跑脚本。

    输出写进**文件**而不是管道：① 避免沙箱/CI 对管道 stdio 的限制；② 读回来时统一
    `decode("utf-8", errors="replace")`，这样即使子进程吐的是 GBK 字节也不会抛
    `UnicodeDecodeError`（第 4 天 BUG-10：Windows 中文控制台 0xd2，CI 的 ubuntu 不暴露）。
    """
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path.as_posix()}"}
    env.pop("PYTHONPATH", None)  # 让脚本自己的 sys.path 生效，避免被测试环境带偏
    # 双保险：子进程自己也说 UTF-8（seed_db/simulate_match 都会 reconfigure），
    # 测试结果不依赖跑测试的人是什么控制台。
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    log_path = db_path.parent / "bootstrap.log"
    with log_path.open("wb") as log_file:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), *extra],
            cwd=REPO_ROOT,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=180,
        )
    output = log_path.read_bytes().decode("utf-8", errors="replace")
    if completed.returncode != 0:  # 失败时把日志打出来，方便定位是哪个步骤挂了
        print(output[-4000:])
    return BootstrapRun(completed.returncode, output)


def test_bootstrap_fills_points_for_every_trading_player(tmp_path: Path) -> None:
    db = tmp_path / "demo.db"

    completed = _run_bootstrap(db, "--rounds", "2", "--min-points", "2", "--seed", "42")
    assert completed.returncode == 0, "bootstrap 应当成功并返回 0"
    # 脚本自己的自检行必须在输出里（证明它真的核对了点数，而不只是"跑完没报错"）
    assert "结果核对" in completed.output
    assert "OK" in completed.output

    conn = sqlite3.connect(db)
    try:
        players = conn.execute(
            "select player_id, name, status from players order by player_id"
        ).fetchall()
        assert len(players) == 8, "应当写入 8 名选手"

        for player_id, name, status in players:
            points = conn.execute(
                "select count(*) from price_history where player_id = ?", (player_id,)
            ).fetchone()[0]
            if status == "trading":
                assert points >= 2, f"{name} 的价格点太少：{points}"
            else:
                # 暂停交易的选手按规则不定价，只保留种子写入的历史
                assert points >= 1, f"{name} 连种子历史都没有：{points}"

        # 余额与持仓不会被灌数脚本改动
        balance = conn.execute("select balance from users").fetchone()[0]
        assert float(balance) == 5000.0
        assert conn.execute("select count(*) from positions").fetchone()[0] == 0
        assert conn.execute("select count(*) from trades").fetchone()[0] == 0
    finally:
        conn.close()


def test_bootstrap_is_repeatable_with_same_seed(tmp_path: Path) -> None:
    """同 seed 再跑一次（--keep，只补价格）价格序列仍然按同一剧本延续，不报错。"""
    db = tmp_path / "demo2.db"

    first = _run_bootstrap(db, "--rounds", "1", "--min-points", "1", "--seed", "42")
    assert first.returncode == 0

    # --keep 不 drop 表，相当于在现有库上继续灌
    second = _run_bootstrap(
        db, "--rounds", "1", "--min-points", "1", "--seed", "42", "--keep"
    )
    assert second.returncode == 0

    conn = sqlite3.connect(db)
    try:
        total = conn.execute("select count(*) from price_history").fetchone()[0]
        assert total > 15, "第二次运行应当继续追加价格历史"
    finally:
        conn.close()
