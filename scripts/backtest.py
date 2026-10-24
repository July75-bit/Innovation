"""智能体回测初版（T4-07 / 第 4 天）。

负责人：D

做什么
-----
在**完全可复现**的模拟行情上，对比几种交易策略的期末资产/收益率/最大回撤/交易次数：

- **S1 规则版 AI**：直接复用 `code/backend/ai/fallback.py::rule_based_advice`
  （与线上 `source=rule_fallback` 同源阈值：近 5 点涨 > +5% 且 rating < 60 → SELL；
  跌 < -5% 且 rating >= 75 → BUY；其余 HOLD），每轮对每名可交易选手决策，买卖 1 股。
- **S2 随机**：固定 seed 的 RNG，随机 BUY/SELL/HOLD 1 股（证明不是"运气"）。
- **S3 买入持有**：第 1 轮等权买入后不再操作（证明不是"靠大盘"）。
- **S4 全现金**：不交易，作基线。

行情从 `data/seed_players.json` 出发：C 的 `simulator.generate_match(seed)` 生成比赛得分，
`pricing.standardize_score` 转 S(t)，`pricing.update_price` 得到每轮新价。
同一 `--seed` 重跑结果完全一致，报告里的每个数字都来自本脚本输出。

用法
----
    python scripts/backtest.py --seed 42 --rounds 20
    python scripts/backtest.py --seed 42 --rounds 20 --output docs/algorithm/backtest_result.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(ROOT / "code" / "backend"))

from ai.fallback import rule_based_advice  # noqa: E402
from core_engine import generate_match, standardize_score, update_price  # noqa: E402

DEFAULT_CASH = Decimal("5000.00")
WARMUP = 3
WINDOW = 5
TRADE_SIZE = 1  # 每次买卖 1 股，避免资金曲线被单次操作主导


def load_players(seed_path: Path) -> list[dict]:
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    players = [p for p in payload.get("players", []) if p.get("status") == "trading"]
    if not players:
        raise SystemExit(f"{seed_path} 里没有可交易选手")
    return players


def build_price_paths(players: list[dict], seed: int, rounds: int, start_date: str) -> dict:
    """用 C 的模拟器 + 定价引擎生成每名选手 rounds 轮的价格/得分序列。"""
    paths: dict[int, dict] = {}
    start = date.fromisoformat(start_date)
    for player in players:
        pid = int(player["player_id"])
        base = float(player["rating"])
        price = float(player["current_price"])
        history = [
            generate_match(pid, seed=seed, round_no=round_no, base_rating=base).score
            for round_no in range(-WARMUP, 0)
        ]
        prices: list[float] = []
        ts: list[str] = []
        for round_no in range(1, rounds + 1):
            match = generate_match(pid, seed=seed, round_no=round_no, base_rating=base)
            signal = standardize_score(match.score, history, window=WINDOW)
            update = update_price(price, signal)
            price = float(update.new_price)
            history.append(match.score)
            prices.append(price)
            ts.append((start + timedelta(days=round_no - 1)).isoformat())
        paths[pid] = {"prices": prices, "ts": ts, "base_rating": base}
    return paths


def _equity(cash: Decimal, quantities: dict[int, int], paths: dict, index: int) -> float:
    total = cash
    for pid, qty in quantities.items():
        total += Decimal(str(paths[pid]["prices"][index])) * qty
    return float(total)


def _advice_context(pid: int, paths: dict, index: int, ratings: dict[int, float], qty: int) -> dict:
    prices = paths[pid]["prices"][: index + 1][-6:]
    prev = prices[-2] if len(prices) >= 2 else prices[-1]
    change_pct = (prices[-1] - prev) / prev * 100.0 if prev else 0.0
    return {
        "player_id": pid,
        "current_price": prices[-1],
        "rating": ratings[pid],
        "change_pct": change_pct,
        "recent_prices": [{"price": value} for value in prices],
        "position": {"quantity": qty},
    }


def _decide_action(
    kind: str, rng: random.Random, pid: int, paths: dict, index: int, ratings: dict, qty: int
) -> str:
    if kind == "rule":
        return rule_based_advice(
            _advice_context(pid, paths, index, ratings, qty)
        )["action"]
    if kind == "random":
        return rng.choice(["BUY", "SELL", "HOLD"])
    return "HOLD"


def _apply_buy(cash: Decimal, price: Decimal, quantities: dict, pid: int):
    if cash < price:
        return cash, False
    quantities[pid] += TRADE_SIZE
    return cash - price, True


def _apply_sell(cash: Decimal, price: Decimal, quantities: dict, pid: int):
    if quantities[pid] < TRADE_SIZE:
        return cash, False
    quantities[pid] -= TRADE_SIZE
    return cash + price, True


def _record_decision(
    decisions: list, index: int, pid: int, action: str, price: Decimal, ratings: dict
) -> None:
    if len(decisions) >= 6:
        return
    note = "近 5 点累计跌幅触发 BUY" if action == "BUY" else "近 5 点累计涨幅触发 SELL"
    decisions.append(
        {
            "round_no": index + 1,
            "player_id": pid,
            "action": action,
            "price": float(price),
            "rating": ratings[pid],
            "note": note,
        }
    )


def _init_hold(cash: Decimal, pids: list[int], quantities: dict, paths: dict):
    budget = cash / len(pids)
    trades = 0
    for pid in pids:
        price = Decimal(str(paths[pid]["prices"][0]))
        shares = int(budget // price)
        if shares > 0:
            cash -= price * shares
            quantities[pid] += shares
            trades += 1
    return cash, trades


def _simulate_trading(
    kind: str,
    pids: list[int],
    paths: dict,
    ratings: dict,
    seed: int,
    rounds: int,
    initial_cash: Decimal,
    collect_decisions: bool,
):
    rng = random.Random(f"playerstock-backtest-{seed}")
    cash = initial_cash
    quantities = {pid: 0 for pid in pids}
    trades = 0
    decisions: list[dict] = []
    equity_curve: list[float] = []
    for index in range(rounds):
        for pid in pids:
            price = Decimal(str(paths[pid]["prices"][index]))
            action = _decide_action(
                kind, rng, pid, paths, index, ratings, quantities[pid]
            )
            if action == "BUY":
                cash, executed = _apply_buy(cash, price, quantities, pid)
                trades += int(executed)
                if executed and collect_decisions:
                    _record_decision(decisions, index, pid, action, price, ratings)
            elif action == "SELL":
                cash, executed = _apply_sell(cash, price, quantities, pid)
                trades += int(executed)
                if executed and collect_decisions:
                    _record_decision(decisions, index, pid, action, price, ratings)
        equity_curve.append(_equity(cash, quantities, paths, index))
    return cash, quantities, trades, decisions, equity_curve


def _max_drawdown(equity_curve: list[float]) -> float:
    peak, drawdown = 0.0, 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            drawdown = max(drawdown, (peak - value) / peak * 100.0)
    return drawdown


def run_strategy(
    kind: str,
    players: list[dict],
    paths: dict,
    seed: int,
    rounds: int,
    initial_cash: Decimal,
    collect_decisions: bool = False,
) -> dict:
    """运行一种策略，返回摘要 + 每轮权益曲线。"""
    pids = [int(p["player_id"]) for p in players]
    ratings = {int(p["player_id"]): float(p["rating"]) for p in players}
    cash = initial_cash
    quantities = {pid: 0 for pid in pids}
    trades = 0
    decisions: list[dict] = []

    if kind == "hold":
        cash, trades = _init_hold(cash, pids, quantities, paths)
        equity_curve = [
            _equity(cash, quantities, paths, index) for index in range(rounds)
        ]
    else:
        cash, quantities, trades, decisions, equity_curve = _simulate_trading(
            kind, pids, paths, ratings, seed, rounds, initial_cash, collect_decisions
        )

    final_asset = equity_curve[-1]
    total_return = (final_asset / float(initial_cash) - 1) * 100.0

    return {
        "strategy": kind,
        "initial_cash": float(initial_cash),
        "final_asset": round(final_asset, 2),
        "total_return_pct": round(total_return, 2),
        "max_drawdown_pct": round(_max_drawdown(equity_curve), 2),
        "trade_count": trades,
        "equity_curve": [round(value, 2) for value in equity_curve],
        "decisions": decisions,
    }


STRATEGY_LABELS = {
    "rule": "S1 规则版 AI（rule_fallback 同源阈值）",
    "random": "S2 随机（同 seed 可复现）",
    "hold": "S3 买入持有（等权）",
    "cash": "S4 全现金（不交易）",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="智能体回测初版（可重跑）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（固定才可复现）")
    parser.add_argument("--rounds", type=int, default=20, help="回测轮次")
    parser.add_argument("--initial-cash", type=float, default=float(DEFAULT_CASH), help="初始虚拟币")
    parser.add_argument("--start-date", default="2026-11-01", help="第 1 轮日期（ISO）")
    parser.add_argument("--seed-file", default=str(ROOT / "data" / "seed_players.json"))
    parser.add_argument(
        "--output", default=str(ROOT / "docs" / "algorithm" / "backtest_result.json")
    )
    args = parser.parse_args()

    players = load_players(Path(args.seed_file))
    paths = build_price_paths(players, args.seed, args.rounds, args.start_date)
    initial_cash = Decimal(str(args.initial_cash))

    summary = []
    for kind in ("rule", "random", "hold"):
        summary.append(
            run_strategy(
                kind,
                players,
                paths,
                args.seed,
                args.rounds,
                initial_cash,
                collect_decisions=(kind == "rule"),
            )
        )
    summary.append(
        {
            "strategy": "cash",
            "initial_cash": float(initial_cash),
            "final_asset": float(initial_cash),
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "trade_count": 0,
            "equity_curve": [float(initial_cash)] * args.rounds,
        }
    )

    print(
        f"[backtest] seed={args.seed} rounds={args.rounds} "
        f"players={len(players)} start={args.start_date} cash={args.initial_cash:.2f}"
    )
    print(f"{'策略':<34}{'期末资产':>10}{'收益率':>9}{'最大回撤':>9}{'交易次数':>8}")
    for item in summary:
        print(
            f"{STRATEGY_LABELS[item['strategy']]:<34}"
            f"{item['final_asset']:>10.2f}"
            f"{item['total_return_pct']:>8.2f}%"
            f"{item['max_drawdown_pct']:>8.2f}%"
            f"{item['trade_count']:>8}"
        )

    result = {
        "generated_at": "2026-10-24T15:50:00+08:00",
        "seed": args.seed,
        "rounds": args.rounds,
        "start_date": args.start_date,
        "initial_cash": float(initial_cash),
        "players": [
            {
                "player_id": int(p["player_id"]),
                "name": p["name"],
                "base_rating": float(p["rating"]),
                "start_price": float(p["current_price"]),
                "end_price": round(paths[int(p["player_id"])]["prices"][-1], 2),
            }
            for p in players
        ],
        "strategies": summary,
        "price_paths": {
            str(pid): [round(value, 2) for value in item["prices"]]
            for pid, item in paths.items()
        },
        "note": "S1 为 rule_fallback 阈值策略代理（LLM 版需密钥，第 5 天线上补跑）；S4 全现金为基线。",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        shown = output.resolve().relative_to(ROOT)
    except ValueError:
        shown = output
    print(f"[backtest] 结果已写入 {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
