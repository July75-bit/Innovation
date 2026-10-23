"""生成一轮模拟比赛，触发价格更新，并把新价格写进 price_history。

负责人：C（模拟与定价） / B（落库）

用法（在仓库根目录）：
    python scripts/simulate_match.py
    python scripts/simulate_match.py --rounds 5 --seed 42   # 演示用固定种子

待实现：C 完成 code/core_engine/ 之后补全 TODO。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(ROOT / "code/backend"))

from core_engine.simulator import generate_match_series  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="生成模拟比赛并更新选手价格")
    parser.add_argument("--rounds", type=int, default=1, help="生成几轮比赛")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（演示时必须固定）")
    args = parser.parse_args()

    player_ids = list(range(1, 9))
    # TODO(C)：generate_match_series 实现后这里即可跑通
    matches = generate_match_series(player_ids, args.rounds, seed=args.seed)

    for m in matches:
        print(f"player {m.player_id}: score={m.score} won={m.won} rating={m.rating}")

    # TODO(B+C)：
    # 1. 用 pricing.update_price 逐个算新价格；
    # 2. 把 (player_id, new_price, reason, ts) 写入 price_history；
    # 3. 更新 players.current_price / prev_price；
    # 4. 注意：不要在这一步改用户余额或持仓。


if __name__ == "__main__":
    main()
