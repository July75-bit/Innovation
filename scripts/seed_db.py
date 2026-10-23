"""把 data/seed_players.json 写入数据库（8 名演示选手 + 每人的初始价格历史）。

负责人：B（数据落库） / C（价格字段来源）

用法（在仓库根目录）：
    python scripts/seed_db.py

待实现：B 建好 models 之后补全下面的 TODO。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "data" / "seed_players.json"

# 让脚本能 import 到 code/backend/app（避免依赖 PYTHONPATH）
sys.path.insert(0, str(ROOT / "code/backend"))


def load_seed() -> dict:
    with SEED_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    seed = load_seed()
    players = seed["players"]
    print(f"读取 {SEED_FILE.relative_to(ROOT)}")
    print(f"演示选手数量：{len(players)}，定价参数：{seed['pricing']}")

    # TODO(B)：
    # from app.core.database import SessionLocal, init_db
    # from app.models import Player, PriceHistory
    # init_db()
    # with SessionLocal() as db, db.begin():
    #     for p in players:
    #         db.add(Player(...))
    #         db.add(PriceHistory(player_id=p["player_id"], price=p["initial_price"],
    #                             reason="初始价格", ts=now()))
    for p in players:
        print(f"  [{p['player_id']}] {p['name']}({p['display_name']}) "
              f"@ {p['current_price']}  rating(模拟)={p['rating']}  status={p['status']}")

    raise SystemExit(
        "TODO(B)：数据库模型就绪后取消注释上面的写入逻辑并删除本行。"
    )


if __name__ == "__main__":
    main()
