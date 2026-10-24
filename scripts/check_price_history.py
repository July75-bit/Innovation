"""价格历史一致性自查：对当前 `DATABASE_URL` 指向的库逐人核对价格链路。

负责人：C（第 5 天「线上价格核对」）

为什么需要：`/api/players/{id}/prices` 是前端折线图和 AI 输入的源头，线上灌数后
必须能证明「每一条历史都是自洽的」。本脚本只读、不写库，本地 SQLite 与 Render
Postgres 通用（`DATABASE_URL` 由环境注入），可在 Render Shell 里直接跑。

逐人检查 6 条：

1. 点数 ≥ `--min-points`（默认 10；暂停交易的选手豁免，只要求 ≥1）；
2. `ts` 严格升序；
3. 末点价 == `players.current_price`（否则前端现价与折线尾巴对不上）；
4. 引擎产生的点，`reason` 必须含「本轮得分」与 `S=`；
5. 相邻两点的实际涨跌幅 == 该点 `reason` 里写的百分比（±0.02 容差）；
6. `change_pct` 口径自洽：`price × (1 + 涨跌幅)` 能还原到 2 位小数。

种子行（`reason` 含「初始价格」/「种子数据」/「行情初始化」）属于开赛前的行情地板，
豁免第 4/5 条 —— 它们背后没有比赛，不能凭空编得分。

用法（仓库根目录）：

    python scripts/check_price_history.py
    python scripts/check_price_history.py --min-points 10
    python scripts/check_price_history.py --player-id 1
    python scripts/check_price_history.py --json

退出码：0 = 全部通过；1 = 有不一致（会逐条打印，方便贴进验收记录）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code" / "backend"))
sys.path.insert(0, str(ROOT / "code"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal, engine, init_db  # noqa: E402
from app.models import Player, PriceHistory  # noqa: E402

#: 种子行标记：这些点没有对应比赛，不能要求「得分 + S + 涨跌幅」
SEED_MARKERS = ("初始价格", "种子数据", "行情初始化")
PERCENT = re.compile(r"价格(上涨|下跌|维持不变)(?:\s+([\d.]+)%)?")
TOLERANCE = 0.02


def is_seed_row(reason: str) -> bool:
    return any(marker in reason for marker in SEED_MARKERS)


def check_player(db, player: Player, min_points: int) -> tuple[list[str], dict]:
    rows = list(
        db.scalars(
            select(PriceHistory)
            .where(PriceHistory.player_id == player.player_id)
            .order_by(PriceHistory.ts.asc(), PriceHistory.price_id.asc())
        ).all()
    )
    problems: list[str] = []
    suspended = player.status != "trading"
    need = 1 if suspended else min_points

    if len(rows) < need:
        problems.append(f"点数不足：{len(rows)} < {need}")

    stamps = [row.ts for row in rows]
    if stamps != sorted(stamps):
        problems.append("ts 非升序")

    if rows and abs(float(rows[-1].price) - float(player.current_price)) > 1e-6:
        problems.append(
            f"末点价 {float(rows[-1].price):.2f} != current_price {float(player.current_price):.2f}"
        )

    for prev, cur in zip(rows, rows[1:]):
        if is_seed_row(cur.reason):
            continue
        if "本轮得分" not in cur.reason or "S=" not in cur.reason:
            problems.append(f"reason 缺「得分/S」：{cur.reason}")
            break

        actual = round((float(cur.price) / float(prev.price) - 1) * 100, 2)
        matched = PERCENT.search(cur.reason)
        if matched is None:
            problems.append(f"reason 里找不到涨跌幅：{cur.reason}")
            break
        if matched.group(2) is not None:
            stated = float(matched.group(2)) * (1 if matched.group(1) == "上涨" else -1)
            if abs(actual - stated) > TOLERANCE:
                problems.append(f"涨跌幅不自洽：实际 {actual:+.2f}% vs reason {stated:+.2f}%")
                break
            restored = round(float(prev.price) * (1 + stated / 100), 2)
            # change_pct 只保留 2 位，还原到「分」必然有 ≤1 分的舍入误差，这里给 2 分钱余量
            if abs(restored - float(cur.price)) > 0.02:
                problems.append(
                    f"价格× 涨跌幅还原不上：{float(prev.price):.2f}×{1 + stated / 100:.4f}"
                    f"={restored:.2f} vs 实际 {float(cur.price):.2f}"
                )
                break

    engine_points = sum(1 for row in rows if not is_seed_row(row.reason))
    info = {
        "player_id": player.player_id,
        "name": player.display_name or player.name,
        "status": player.status,
        "points": len(rows),
        "engine_points": engine_points,
        "current_price": float(player.current_price),
        "last_price": float(rows[-1].price) if rows else None,
        "last_reason": rows[-1].reason if rows else "",
    }
    return problems, info


def main() -> int:
    parser = argparse.ArgumentParser(description="价格历史一致性自查（只读）")
    parser.add_argument("--min-points", type=int, default=10, help="可交易选手的最少价格点（默认 10）")
    parser.add_argument("--player-id", type=int, default=None, help="只查某一名选手")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出，便于贴进验收记录")
    args = parser.parse_args()

    init_db()
    print(f"[check] 数据库：{engine.url}（只读核对，不写库）")

    all_problems: list[str] = []
    infos: list[dict] = []

    with SessionLocal() as db:
        stmt = select(Player).order_by(Player.player_id)
        if args.player_id is not None:
            stmt = stmt.where(Player.player_id == args.player_id)
        players = list(db.scalars(stmt).all())
        if not players:
            print("[check] 库里没有选手数据：先跑 scripts/bootstrap_demo_data.py")
            return 1

        for player in players:
            problems, info = check_player(db, player, args.min_points)
            infos.append(info)
            if problems:
                all_problems.extend(f"{info['name']}：{p}" for p in problems)

    if args.json:
        print(json.dumps({"ok": not all_problems, "players": infos, "problems": all_problems},
                         ensure_ascii=False, indent=2))
    else:
        print(f"{'选手':<10}{'状态':<11}{'点数':>4}{'引擎点':>7}{'现价':>10}  末点 reason")
        for info in infos:
            print(
                f"{info['name']:<10}{info['status']:<11}{info['points']:>4}"
                f"{info['engine_points']:>7}{info['current_price']:>10.2f}  {info['last_reason']}"
            )
        print()
        if all_problems:
            print(f"[check] ❌ {len(all_problems)} 处不一致：")
            for problem in all_problems:
                print("  -", problem)
        else:
            print(
                "[check] ✅ 全部通过：点数达标、ts 升序、末点价 = current_price、"
                "reason 含得分+S、涨跌幅自洽（种子行已豁免）"
            )

    return 1 if all_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
