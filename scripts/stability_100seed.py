"""100 seed 稳定性统计（定价机制评测，可一键复现）。

负责人：C

做什么
-----
对 seed = 1..N 逐个重放「16 名选手 × R 轮」的模拟行情（与演示/回测同一套
`simulator.generate_match` + `pricing.standardize_score/update_price`），统计：

- **区间收益**：每个 seed 内所有可交易选手的平均涨跌幅；
- **盈利人数**：每个 seed 有多少名选手期末价高于起始价；
- **平均单次变动幅度** / **单次最大变动** / **方向一致率** / **每 seed 更新条数**；
- **α 敏感性**：同一批 seed 下 α=0.15 / 0.08 / 0.05 的逐人区间收益中位数与平均单次幅度。

口径与 `docs/algorithm/pricing_model.md` §7.2 完全一致：28 轮、窗口 N=5、回填 3 场、
暂停交易按 `data/match_schedule.json` 逐轮派生（每轮 2 队 = 4 人停牌，12 人参与）。

用法
----
    python scripts/stability_100seed.py
    python scripts/stability_100seed.py --seeds 100 --json docs/algorithm/stability_100seed.json
    python scripts/stability_100seed.py --seeds 5 --rounds 12 --alphas 0.15
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

DEFAULT_SEEDS = 100
DEFAULT_ROUNDS = 28
DEFAULT_WINDOW = 5
DEFAULT_WARMUP = 3
DEFAULT_ALPHAS = (0.15, 0.08, 0.05)
SEED_FILE = ROOT / "data" / "seed_players.json"
SCHEDULE_FILE = ROOT / "data" / "match_schedule.json"


def _load_inputs() -> tuple[list[dict[str, Any]], dict]:
    from core_engine import load_schedule

    players = json.loads(SEED_FILE.read_text(encoding="utf-8"))["players"]
    return players, load_schedule(SCHEDULE_FILE)


def _signals_for_seed(
    players: list[dict[str, Any]],
    schedule: dict,
    *,
    seed: int,
    rounds: int,
    window: int,
    warmup: int,
) -> dict[int, list[tuple[int, float, float]]]:
    """按 seed 生成每名选手的 (轮次, 得分, 信号 S)；停牌轮不参与、也不进历史。"""
    from core_engine import generate_match, standardize_score, suspension_reason

    out: dict[int, list[tuple[int, float, float]]] = {int(p["player_id"]): [] for p in players}
    for player in players:
        pid = int(player["player_id"])
        base = float(player["rating"])
        history = [
            generate_match(pid, seed=seed, round_no=r, base_rating=base).score
            for r in range(-warmup, 0)
        ]
        for round_no in range(1, rounds + 1):
            match = generate_match(pid, seed=seed, round_no=round_no, base_rating=base)
            if suspension_reason(player, round_no, schedule):
                continue
            signal = standardize_score(match.score, history, window=window)
            out[pid].append((round_no, match.score, signal))
            history.append(match.score)
    return out


def _simulate_alpha(
    players: list[dict[str, Any]],
    signals: dict[int, list[tuple[int, float, float]]],
    alpha: float,
) -> tuple[list[float], list[float], list[float]]:
    """按给定 α 走一遍价格，返回 (逐人区间收益 %, 全部单次变动 %, 对应信号 S)。"""
    from core_engine import update_price

    returns: list[float] = []
    steps: list[float] = []
    step_signals: list[float] = []
    for player in players:
        pid = int(player["player_id"])
        series = signals[pid]
        if not series:
            continue
        price = float(player["current_price"])
        start = price
        for _round_no, score, signal in series:
            update = update_price(price, signal, alpha=alpha, score=score)
            steps.append(float(update.change_pct))
            step_signals.append(signal)
            price = update.new_price
        returns.append((price / start - 1) * 100)
    return returns, steps, step_signals


def _seed_metrics(
    players: list[dict[str, Any]],
    signals: dict[int, list[tuple[int, float, float]]],
    alpha: float,
    seed: int,
) -> dict[str, Any]:
    returns, steps, step_signals = _simulate_alpha(players, signals, alpha)
    consistent = sum(
        1
        for signal, change in zip(step_signals, steps)
        if (signal > 0 and change > 0)
        or (signal < 0 and change < 0)
        or (signal == 0 and change == 0)
    )
    return {
        "seed": seed,
        "points": len(steps),
        "avg_return_pct": round(statistics.fmean(returns), 4) if returns else 0.0,
        "profitable_players": sum(1 for r in returns if r > 0),
        "mean_abs_step_pct": round(statistics.fmean(abs(s) for s in steps), 4) if steps else 0.0,
        "max_step_pct": round(max(abs(s) for s in steps), 4) if steps else 0.0,
        "consistent_points": consistent,
    }


def _aggregate(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    avg = [row["avg_return_pct"] for row in seed_rows]
    ups = [row["profitable_players"] for row in seed_rows]
    mean_abs = [row["mean_abs_step_pct"] for row in seed_rows]
    max_step = [row["max_step_pct"] for row in seed_rows]
    points = sorted({row["points"] for row in seed_rows})
    consistent = [row["consistent_points"] / row["points"] for row in seed_rows]
    return {
        "median_avg_return_pct": round(statistics.median(avg), 4),
        "mean_avg_return_pct": round(statistics.fmean(avg), 4),
        "min_avg_return_pct": round(min(avg), 4),
        "max_avg_return_pct": round(max(avg), 4),
        "median_profitable_players": statistics.median(ups),
        "min_profitable_players": min(ups),
        "max_profitable_players": max(ups),
        "pct_seeds_with_4plus_profitable": round(
            sum(1 for u in ups if u >= 4) / len(ups) * 100, 2
        ),
        "median_mean_abs_step_pct": round(statistics.median(mean_abs), 4),
        "min_mean_abs_step_pct": round(min(mean_abs), 4),
        "max_mean_abs_step_pct": round(max(mean_abs), 4),
        "max_step_pct": round(max(max_step), 4),
        "min_consistency_pct": round(min(consistent) * 100, 2),
        "mean_consistency_pct": round(statistics.fmean(consistent) * 100, 2),
        "points_per_seed": points,
    }


def run_study(
    *,
    seeds: int,
    rounds: int,
    window: int = DEFAULT_WINDOW,
    warmup: int = DEFAULT_WARMUP,
    alphas: tuple[float, ...] = DEFAULT_ALPHAS,
) -> dict[str, Any]:
    """跑完整研究并返回可直接写 JSON 的字典（纯函数，便于测试）。"""
    players, schedule = _load_inputs()
    seed_rows: list[dict[str, Any]] = []
    alpha_rows: list[dict[str, Any]] = []
    signals_by_seed: dict[int, dict[int, list[tuple[int, float, float]]]] = {}

    for seed in range(1, seeds + 1):
        signals = _signals_for_seed(
            players, schedule, seed=seed, rounds=rounds, window=window, warmup=warmup
        )
        signals_by_seed[seed] = signals
        seed_rows.append(_seed_metrics(players, signals, alphas[0], seed))

    for alpha in alphas:
        pooled_returns: list[float] = []
        pooled_steps: list[float] = []
        for seed in range(1, seeds + 1):
            returns, steps, _signals = _simulate_alpha(players, signals_by_seed[seed], alpha)
            pooled_returns += returns
            pooled_steps += steps
        alpha_rows.append(
            {
                "alpha": alpha,
                "median_return_pct": round(statistics.median(pooled_returns), 4),
                "mean_abs_step_pct": round(
                    statistics.fmean(abs(s) for s in pooled_steps), 4
                ),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": {
            "seeds": seeds,
            "rounds": rounds,
            "window": window,
            "warmup": warmup,
            "alphas": list(alphas),
            "seed_file": str(SEED_FILE.relative_to(ROOT)),
            "schedule_file": str(SCHEDULE_FILE.relative_to(ROOT)),
        },
        "aggregate": _aggregate(seed_rows),
        "per_seed": seed_rows,
        "alpha_sensitivity": alpha_rows,
    }


def _print_summary(payload: dict[str, Any]) -> None:
    agg = payload["aggregate"]
    print(
        f"seed 数 {payload['config']['seeds']} · 轮次 {payload['config']['rounds']} · "
        f"每 seed 更新 {agg['points_per_seed']} 条"
    )
    print(
        f"区间收益：中位 {agg['median_avg_return_pct']:+.2f}% / 均值 "
        f"{agg['mean_avg_return_pct']:+.2f}% / 范围 {agg['min_avg_return_pct']:+.2f}%"
        f" ~ {agg['max_avg_return_pct']:+.2f}%"
    )
    print(
        f"盈利人数：中位 {agg['median_profitable_players']:.0f} "
        f"（{agg['min_profitable_players']}–{agg['max_profitable_players']}）；"
        f"≥4 人的 seed 占 {agg['pct_seeds_with_4plus_profitable']:.0f}%"
    )
    print(
        f"平均单次幅度：中位 {agg['median_mean_abs_step_pct']:.2f}%"
        f"（{agg['min_mean_abs_step_pct']:.2f}–{agg['max_mean_abs_step_pct']:.2f}%）；"
        f"单次最大 {agg['max_step_pct']:.2f}%"
    )
    print(
        f"方向一致率：最低 {agg['min_consistency_pct']:.2f}% / "
        f"平均 {agg['mean_consistency_pct']:.2f}%"
    )
    print("α 敏感性：")
    for row in payload["alpha_sensitivity"]:
        print(
            f"  α={row['alpha']:.2f} → 逐人收益中位 {row['median_return_pct']:+.2f}%"
            f"，平均单次 {row['mean_abs_step_pct']:.2f}%"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="100 seed 稳定性统计（可复现）")
    parser.add_argument("--seeds", type=int, default=DEFAULT_SEEDS, help="seed 个数（1..N）")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="每个 seed 的轮次")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW, help="S(t) 的窗口 N")
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP, help="回填历史场数")
    parser.add_argument(
        "--alphas",
        default=",".join(str(a) for a in DEFAULT_ALPHAS),
        help="α 敏感性列表，逗号分隔",
    )
    parser.add_argument("--json", help="把完整结果写到这个路径（父目录需已存在）")
    args = parser.parse_args(argv)

    if args.seeds < 1:
        print("❌ --seeds 至少为 1", file=sys.stderr)
        return 2
    alphas = tuple(float(x) for x in args.alphas.split(",") if x.strip())
    payload = run_study(
        seeds=args.seeds,
        rounds=args.rounds,
        window=args.window,
        warmup=args.warmup,
        alphas=alphas,
    )
    _print_summary(payload)
    if args.json:
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"结果已写入 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
