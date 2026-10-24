"""生成模拟比赛 → 触发价格更新 → 打印"旧价 → 新价 + 原因"。

负责人：C（模拟与定价） / B（落库）

用法（在仓库根目录）：
    python scripts/simulate_match.py
    python scripts/simulate_match.py --rounds 5 --seed 42
    python scripts/simulate_match.py --rounds 5 --seed 42 --json data/price_updates.json

要点：
- **不写数据库**：price_history 与 players.current_price/prev_price 由 B 的
  `app/api/prices.py` 落库；本脚本只算价，`--json` 导出明细给 B 用；
- 标准化需要至少 2 场历史才有意义（1 场时标准差为 0 → S=0）。
  `--warmup N`（默认 3）在内存里用同一 seed 回填最近 N 场评分，
  **不写进 data/seed_players.json**，种子文件保持数据合约不变；
- 同一 --seed 下输出完全可复现；
- `status != trading` 的选手跳过定价（与 B 的暂停交易规则一致）。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台中文不乱码

from core_engine import (  # noqa: E402
    MAX_STEP_PCT,
    generate_match,
    generate_match_series,
    standardize_score,
    update_price,
)

SEED_FILE = ROOT / "data" / "seed_players.json"


def load_players(path: Path = SEED_FILE) -> list[dict]:
    """读取固定演示数据（8 名真实 CS2 选手，价格与评分为模拟值）。"""
    if not path.exists():
        raise SystemExit(f"找不到种子数据：{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["players"]


def warmup_history(player: dict, count: int, seed: int) -> list[float]:
    """用同一 seed 回填最近 N 场评分（负 round_no，与正式轮次错开）。"""
    if count <= 0:
        return []
    return [
        generate_match(
            player["player_id"],
            seed=seed,
            round_no=round_no,
            base_rating=float(player["rating"]),
        ).score
        for round_no in range(-count, 0)
    ]


def format_history(history: list[float], window: int) -> str:
    recent = history[-window:]
    if not recent:
        return "无历史"
    return f"近 {len(recent)} 场均分 {sum(recent) / len(recent):.1f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成模拟比赛并更新选手价格")
    parser.add_argument("--rounds", type=int, default=3, help="生成几轮比赛（默认 3）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（演示必须固定）")
    parser.add_argument("--window", type=int, default=5, help="标准化窗口（默认 5 场）")
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="开赛前回填最近 N 场历史评分（默认 3；只在内存，不写种子文件）",
    )
    parser.add_argument("--alpha", type=float, default=None, help="覆盖表现权重 α")
    parser.add_argument("--beta", type=float, default=None, help="覆盖需求权重 β")
    parser.add_argument("--floor", type=float, default=None, help="覆盖价格下限")
    parser.add_argument("--json", type=str, default=None, help="导出更新明细，交给 B 落库")
    args = parser.parse_args()

    players = load_players()
    by_id = {p["player_id"]: p for p in players}
    player_ids = [p["player_id"] for p in players]
    base_ratings = {p["player_id"]: float(p["rating"]) for p in players}

    # 运行状态：上一价、当前价、历史评分
    state = {
        pid: {
            "prev_price": float(by_id[pid].get("prev_price", by_id[pid]["current_price"])),
            "price": float(by_id[pid]["current_price"]),
            "history": warmup_history(by_id[pid], args.warmup, args.seed),
        }
        for pid in player_ids
    }

    matches = generate_match_series(
        player_ids, args.rounds, seed=args.seed, base_ratings=base_ratings
    )

    print(f"模拟比赛：{args.rounds} 轮 × {len(player_ids)} 名选手（seed={args.seed}）")
    print(
        f"参数：α={args.alpha if args.alpha is not None else 0.15}，"
        f"β={args.beta if args.beta is not None else 0.0}，"
        f"单次涨幅上限 +{MAX_STEP_PCT * 100:.0f}%，窗口 N={args.window}，"
        f"回填历史 {args.warmup} 场"
    )
    print("说明：rating 为项目模拟评分，非 HLTV / 官方数据；回填历史只在内存，不改种子文件")
    print("-" * 104)

    updates: list[dict] = []
    up = down = flat = capped_count = floored_count = 0
    best: dict | None = None
    worst: dict | None = None

    for round_no in range(1, args.rounds + 1):
        round_matches = [m for m in matches if m.round_no == round_no]
        played_at = round_matches[0].played_at if round_matches else ""
        print(f"\n第 {round_no} 轮 · {played_at}")
        if round_no == 1 and args.warmup <= 0:
            print("  （无历史评分 → S=0，价格不变；历史不足 2 场时标准差为 0）")

        for match in round_matches:
            player = by_id[match.player_id]
            label = f"{player.get('display_name', player['name'])}（{player['team']} / {player['role']}）"
            st = state[match.player_id]

            if player.get("status") != "trading":
                print(f"  {label:<32} 状态 {player.get('status')}，本轮跳过定价")
                continue

            signal = standardize_score(match.score, st["history"], window=args.window)
            update = update_price(
                st["price"],
                signal,
                demand_signal=0.0,
                alpha=args.alpha,
                beta=args.beta,
                floor=args.floor,
            )

            flag = "胜" if match.won else "负"
            print(
                f"  {label:<32} 评分 {match.score:5.1f} 评级 {match.rating} {flag}  "
                f"{update.old_price:>7.2f} → {update.new_price:>7.2f}  {update.change_pct:+6.2f}%"
            )
            print(
                f"  {'':<32} {format_history(st['history'], args.window)}，"
                f"S={signal:+.2f} ｜ {update.reason}"
            )

            if update.change_pct > 0:
                up += 1
            elif update.change_pct < 0:
                down += 1
            else:
                flat += 1
            capped_count += 1 if update.capped else 0
            floored_count += 1 if update.floored else 0

            if best is None or update.change_pct > best["change_pct"]:
                best = {"player": label, "round": round_no, "change_pct": update.change_pct}
            if worst is None or update.change_pct < worst["change_pct"]:
                worst = {"player": label, "round": round_no, "change_pct": update.change_pct}

            updates.append(
                {
                    "player_id": match.player_id,
                    "round_no": round_no,
                    "ts": match.played_at,          # 与 api_contract 的 price_history.ts 对齐
                    "score": match.score,
                    "signal": update.signal,
                    "old_price": update.old_price,
                    "new_price": update.new_price,
                    "change_pct": update.change_pct,
                    "prev_price": st["prev_price"],
                    "reason": update.reason,
                }
            )

            st["prev_price"] = update.old_price
            st["price"] = update.new_price
            st["history"].append(match.score)

    # ---------------- 汇总 ----------------
    print("\n" + "-" * 104)
    print(f"共 {len(updates)} 条价格更新：上涨 {up} / 下跌 {down} / 持平 {flat}")
    if best and worst:
        print(
            f"最大单次涨幅 {best['change_pct']:+.2f}%（{best['player']} 第 {best['round']} 轮），"
            f"最大单次跌幅 {worst['change_pct']:+.2f}%（{worst['player']} 第 {worst['round']} 轮）"
        )
    print(f"触发 +{MAX_STEP_PCT * 100:.0f}% 涨幅上限 {capped_count} 次，触及价格下限 {floored_count} 次")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "seed": args.seed,
            "rounds": args.rounds,
            "window": args.window,
            "updates": updates,
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"更新明细已写入：{out.resolve()}（交给 B 写入 price_history / 更新 current_price）")
    else:
        print("提示：加 --json data/price_updates.json 可导出明细，交给 B 落库。")


if __name__ == "__main__":
    main()
