"""生成一轮模拟比赛，触发价格更新，并把新价格写进 price_history。

负责人：C（模拟与定价） / B（落库）

用法（在仓库根目录）：
    python scripts/simulate_match.py
    python scripts/simulate_match.py --rounds 5 --seed 42   # 演示用固定种子
    python scripts/simulate_match.py --rounds 5 --seed 42 --json data/price_updates.json

待实现：C 完成 backend/pricing/ 之后补全 TODO。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from pricing.pricing import MAX_STEP_PCT, standardize_score, update_price  # noqa: E402
from pricing.simulator import generate_match_series  # noqa: E402

SEED_FILE = ROOT / "data" / "seed_players.json"
FALLBACK_HISTORY = 3
def load_players(path: Path = SEED_FILE) -> list[dict]:
    """读取固定演示数据（8 名虚构选手）。"""
    if not path.exists():
        raise SystemExit(f"找不到种子数据：{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["players"]
def initial_history(player: dict, seed: int) -> list[float]:
    """取选手的初始历史评分。
    优先用 seed_players.json 里的 `recent_scores`（固定值，演示可复现）；
    字段缺失时用同一 seed 现生成 3 场（负 round_no，与正式轮次错开）。
    """
    recent = player.get("recent_scores")
    if recent:
        return [float(x) for x in recent]
    return [
        generate_match(
            player["player_id"],
            seed=seed,
            round_no=round_no,
            base_rating=player.get("rating"),
        ).score
        for round_no in range(-FALLBACK_HISTORY, 0)
    ]
def format_mean(history: list[float], window: int) -> str:
    recent = history[-window:]
    if not recent:
        return "无历史"
    return f"近 {len(recent)} 场均分 {sum(recent) / len(recent):.1f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成模拟比赛并更新选手价格")
    parser.add_argument("--rounds", type=int, default=1, help="生成几轮比赛")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（演示时必须固定）")
    parser.add_argument("--window", type=int, default=5, help="标准化窗口（默认 5 局）")
    parser.add_argument("--alpha", type=float, default=None, help="覆盖表现权重 α")
    parser.add_argument("--beta", type=float, default=None, help="覆盖需求权重 β")
    parser.add_argument("--floor", type=float, default=None, help="覆盖价格下限")
    parser.add_argument("--json", type=str, default=None, help="把本次更新写成 JSON，交给 B 落库")
    args = parser.parse_args()

    players = load_players()
    by_id = {p["player_id"]: p for p in players}
    player_ids = list(range(1, 9))
    # TODO(C)：generate_match_series 实现后这里即可跑通
    # 每名选手的运行状态：上一价、当前价、历史评分
    state = {
        pid: {
            "prev_price": float(by_id[pid]["prev_price"]),
            "price": float(by_id[pid]["current_price"]),
            "history": initial_history(by_id[pid], args.seed),
        }
        for pid in player_ids
    }

    matches = generate_match_series(player_ids, args.rounds, seed=args.seed)

    
    # TODO(B+C)：
    # 1. 用 pricing.update_price 逐个算新价格；
    # 2. 把 (player_id, new_price, reason, ts) 写入 price_history；
    # 3. 更新 players.current_price / prev_price；
    # 4. 注意：不要在这一步改用户余额或持仓。
    alpha_text = args.alpha if args.alpha is not None else 0.15
    beta_text = args.beta if args.beta is not None else 0.0
    print(f"模拟比赛：{args.rounds} 轮 × {len(player_ids)} 名选手（seed={args.seed}）")
    print(
        f"参数：α={alpha_text}，β={beta_text}，单次涨幅上限 +{MAX_STEP_PCT * 100:.0f}%，"
        f"窗口 N={args.window}，初始历史取自 seed_players.json 的 recent_scores"
    )
    print("-" * 108)
    updates: list[dict] = []
    up = down = flat = capped_count = floored_count = 0
    best: dict | None = None
    worst: dict | None = None
    for round_no in range(1, args.rounds + 1):
        round_matches = [m for m in matches if m.round_no == round_no]
        played_at = round_matches[0].played_at if round_matches else ""
        print(f"\n第 {round_no} 轮 · {played_at}")
        for match in round_matches:
            player = by_id[match.player_id]
            label = f"{player['display_name']} {player['name']}"
            st = state[match.player_id]
            # 比赛进行中 / 停赛的选手：按规则跳过定价（B 那边同样禁止交易）
            if player.get("status") != "trading":
                print(f"  {label:<14} 状态 {player.get('status')}，本轮跳过定价")
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
                f"  {label:<14} 评分 {match.score:5.1f} 评级 {match.rating} {flag}  "
                f"{update.old_price:>7.2f} → {update.new_price:>7.2f}  {update.change_pct:+6.2f}%"
            )
            print(
                f"  {'':<14} {format_mean(st['history'], args.window)}，S={signal:+.2f} ｜ {update.reason}"
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
                    "played_at": match.played_at,
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
    print("\n" + "-" * 108)
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
        print(f"更新明细已写入：{out.resolve()}（可直接交给 B 的落库脚本）")
    else:
        print("提示：加 --json data/price_updates.json 可导出明细，交给 B 写入 price_history。")


if __name__ == "__main__":
    main()
