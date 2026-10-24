"""一键把演示数据落到「当前 DATABASE_URL 指向的库」——本地 SQLite 与 Render Postgres 通用。

负责人：B

为什么需要它：`code/backend/playerstock.db` 和 `data/price_updates.json` 都被 `.gitignore`
忽略了，**演示数据不能靠提交文件共享，只能靠可复现的配方**。这个脚本就是那条配方的一键版，
等价于手跑这三条（见 `docs/software/database_design.md` §4.1）：

    python scripts/seed_db.py --reset
    python scripts/simulate_match.py --seed 42 --rounds 9 --json data/price_updates.json
    python scripts/update_prices.py --from-json data/price_updates.json

它**不重写任何算法**：只是按顺序调用上述三个脚本（C 的模拟+定价、B 的入库、B 的种子），
所以换环境后跑出来的数据与本地完全一致（同 seed 可复现）。

用法（仓库根目录）：

    python scripts/bootstrap_demo_data.py                  # 清库重建 + 9 轮价格
    python scripts/bootstrap_demo_data.py --rounds 12      # 想要更长的价格历史
    python scripts/bootstrap_demo_data.py --seed 7         # 换一套可复现的剧本
    python scripts/bootstrap_demo_data.py --keep           # 不 drop 表，只补价格
    python scripts/bootstrap_demo_data.py --json-out /tmp/price_updates.json   # 顺带留明细

在 Render（PostgreSQL）上：控制台 → 后端服务 → **Shell** →

    python scripts/bootstrap_demo_data.py

`DATABASE_URL` 由 Render 注入，脚本不需要额外参数；跑完退出码为 0 即表示
「每名可交易选手都有 >= --min-points 个价格点」。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code" / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台中文不乱码
    except Exception:  # noqa: BLE001 - 被 pytest 捕获时 stdout 可能不支持重配置
        pass

DEFAULT_SEED = 42
DEFAULT_ROUNDS = 9  # 9 轮：种子只给 ropz 1 条历史，8 轮只到 9 点，9 轮才能让所有人 >= 10
DEFAULT_MIN_POINTS = 10


def masked_db_url() -> str:
    """打印用：把密码掩掉，避免把连接串写进日志/截图。"""
    from app.core.config import settings

    return re.sub(r"(://[^:/@]+:)[^@]+@", r"\1***@", settings.database_url)


def _run_step(label: str, args: list[str]) -> None:
    """跑一个子脚本；输出直接继承到当前终端（不走管道），失败即中止。"""
    print(f"\n=== {label} ===", flush=True)
    print("  $ " + " ".join([Path(sys.executable).name, *args]), flush=True)
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"[bootstrap] 步骤失败（exit={completed.returncode}）：{' '.join(args)}")


def verify(min_points: int) -> bool:
    """核对每名可交易选手的价格点数，顺带把库里的其他计数打出来。"""
    from sqlalchemy import func, select

    from app.core.database import SessionLocal
    from app.models import Player, Position, PriceHistory, Trade, User

    with SessionLocal() as db:
        counts = dict(
            db.execute(
                select(PriceHistory.player_id, func.count()).group_by(PriceHistory.player_id)
            ).all()
        )
        players = list(db.scalars(select(Player).order_by(Player.player_id)).all())
        balance = db.scalar(select(User.balance).where(User.nickname == "demo"))
        positions = db.scalar(select(func.count()).select_from(Position))
        trades = db.scalar(select(func.count()).select_from(Trade))
        total_points = db.scalar(select(func.count()).select_from(PriceHistory))

    print("\n=== 结果核对 ===", flush=True)
    all_ok = True
    for player in players:
        n = int(counts.get(player.player_id, 0))
        ok = n >= min_points or player.status != "trading"
        all_ok = all_ok and ok
        note = "" if player.status == "trading" else f"（{player.status}，按规则不定价）"
        print(
            f"  {'OK' if ok else '!!'} #{player.player_id} {player.name:<7} "
            f"{n:>2} 点  现价 {player.current_price}{note}",
            flush=True,
        )
    print(
        f"  price_history 合计 = {total_points} 条；"
        f"demo 余额 = {balance}；持仓 = {positions} 条；流水 = {trades} 条",
        flush=True,
    )
    return all_ok


def run(args: argparse.Namespace) -> int:
    from app.core.database import init_db

    # 先把库地址打出来（掩掉密码），避免在 Render 上灌错库
    init_db()  # 确保表存在；seed 的 --reset 会重建
    print(f"[bootstrap] 目标库：{masked_db_url()}", flush=True)
    print(
        f"[bootstrap] 参数：seed={args.seed} rounds={args.rounds} "
        f"reset={not args.keep} min_points={args.min_points}",
        flush=True,
    )

    seed_args = ["scripts/seed_db.py"] + ([] if args.keep else ["--reset"])
    _run_step("1/3 写入种子数据（8 名选手 + demo 账户）", seed_args)

    if args.json_out:
        json_path = Path(args.json_out).expanduser().resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        cleanup = None
    else:
        # 默认写临时文件：Render 上不污染仓库，本地也不必留 data/price_updates.json
        tmp = tempfile.NamedTemporaryFile(prefix="price_updates-", suffix=".json", delete=False)
        tmp.close()
        json_path = Path(tmp.name)
        cleanup = json_path

    try:
        _run_step(
            f"2/3 生成 {args.rounds} 轮模拟赛程明细（C 的 simulate_match）",
            [
                "scripts/simulate_match.py",
                "--seed",
                str(args.seed),
                "--rounds",
                str(args.rounds),
                "--json",
                str(json_path),
            ],
        )
        _run_step(
            "3/3 落库（B 的 update_prices：players + price_history 同事务）",
            ["scripts/update_prices.py", "--from-json", str(json_path)],
        )
    finally:
        if cleanup is not None:
            cleanup.unlink(missing_ok=True)

    ok = verify(args.min_points)
    if not ok:
        print(
            f"\n[bootstrap] 有可交易选手的价格点少于 {args.min_points} 个，"
            f"可加大 --rounds 重跑",
            flush=True,
        )
        return 1

    print("\n[bootstrap] 完成：演示数据已就绪，可直接 uvicorn 起服务", flush=True)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="一键把演示数据（8 名选手 + 10+ 个价格点）落到当前 DATABASE_URL"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="随机种子（演示固定 42）")
    parser.add_argument(
        "--rounds", type=int, default=DEFAULT_ROUNDS, help="生成几轮比赛（默认 9，保证每人 >= 10 点）"
    )
    parser.add_argument("--keep", action="store_true", help="不 drop 表，只在现有库上补价格")
    parser.add_argument("--json-out", type=str, default=None, help="把价格更新明细另存一份")
    parser.add_argument(
        "--min-points", type=int, default=DEFAULT_MIN_POINTS, help="可交易选手的最少价格点数"
    )
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
