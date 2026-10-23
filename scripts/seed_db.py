"""把 data/seed_players.json 写入数据库（8 名演示选手 + 每人的初始价格历史）。

负责人：B（数据落库） / C（价格字段来源）

用法（在仓库根目录）：
    python scripts/seed_db.py            # 建表 + 写入演示账户与选手（幂等）
    python scripts/seed_db.py --reset    # 先删表再重建（仅本地开发）
    python scripts/seed_db.py --check    # 只打印表结构与数据条数

落库口径（与 docs/software/database_design.md 一致）：
- players 存 current_price / prev_price / rating（0–100 模拟分）/ status；
- JSON 里的 initial_price 不是 players 字段，写成 price_history 的第一条
  （reason = 初始价格）；若 current_price 与 initial_price 不同，再补一条当前价，
  让前端折线图与 AI 输入都有据可查；
- 演示账户 nickname = "demo"，初始 5000 虚拟币。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "data" / "seed_players.json"

# 让脚本能 import 到 code/backend/app（避免依赖 PYTHONPATH）
sys.path.insert(0, str(ROOT / "code/backend"))

CENT = Decimal("0.01")


def load_seed() -> dict:
    with SEED_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def seed(reset: bool) -> None:
    from sqlalchemy import func, select

    from app.core.config import settings
    from app.core.database import Base, SessionLocal, engine, init_db
    from app.core.time import utcnow
    from app.models import Player, PriceHistory, User

    if reset:
        Base.metadata.drop_all(bind=engine)
        print("[seed] 已删除全部表（--reset）")

    init_db()
    print("[seed] 表结构已就绪")

    seed_data = load_seed()
    players = seed_data["players"]
    print(f"[seed] 读取 {SEED_FILE.relative_to(ROOT)}：{len(players)} 名选手")

    with SessionLocal() as db:
        created = 0
        for row in players:
            player_id = int(row["player_id"])
            if db.get(Player, player_id) is not None:
                continue

            initial_price = Decimal(str(row["initial_price"])).quantize(CENT)
            prev_price = Decimal(str(row["prev_price"])).quantize(CENT)
            current_price = Decimal(str(row["current_price"])).quantize(CENT)
            now = utcnow()

            db.add(
                Player(
                    player_id=player_id,
                    name=str(row["name"]),
                    display_name=str(row.get("display_name") or row["name"]),
                    team=str(row.get("team") or ""),
                    role=str(row.get("role") or ""),
                    current_price=current_price,
                    prev_price=prev_price,
                    rating=int(row["rating"]),
                    status=str(row.get("status", "trading")),
                )
            )
            db.flush()

            # initial_price 落库为价格历史第一条（设计文档 §2.2 说明）
            db.add(
                PriceHistory(
                    player_id=player_id,
                    price=initial_price,
                    reason="初始价格",
                    ts=now - timedelta(hours=1),
                )
            )
            if current_price != initial_price:
                db.add(
                    PriceHistory(
                        player_id=player_id,
                        price=current_price,
                        reason="模拟比赛表现调整（种子数据，待 C 的定价引擎接管）",
                        ts=now,
                    )
                )
            created += 1

        demo = db.scalar(select(User).where(User.nickname == "demo"))
        created_user = False
        if demo is None:
            initial_balance = Decimal(settings.initial_balance)
            db.add(
                User(
                    nickname="demo",
                    balance=initial_balance,
                    initial_balance=initial_balance,
                )
            )
            created_user = True

        db.commit()

        counts = {
            "players": db.scalar(select(func.count(Player.player_id))),
            "price_history": db.scalar(select(func.count(PriceHistory.price_id))),
            "users": db.scalar(select(func.count(User.user_id))),
        }
        balance = db.scalar(select(User.balance).where(User.nickname == "demo"))

    print(f"[seed] 新增选手 {created} 名；演示账户{'已创建' if created_user else '已存在'}")
    print(f"[seed] 当前数据：{counts}")
    print(f"[seed] 演示账户 demo 余额 = {balance}")
    print("[seed] 完成，可执行：python -m uvicorn app.main:app --reload --port 8000")


def check() -> None:
    from sqlalchemy import func, inspect, select

    from app.core.database import SessionLocal, engine, init_db
    from app.models import Player, PriceHistory, Position, Trade, User

    init_db()
    inspector = inspect(engine)
    print(f"[check] 数据库：{engine.url}")
    print(f"[check] 表：{', '.join(sorted(inspector.get_table_names()))}")

    with SessionLocal() as db:
        for model in (User, Player, Position, Trade, PriceHistory):
            count = db.scalar(select(func.count()).select_from(model))
            print(f"[check] {model.__tablename__}: {count}")

    print(f"[check] positions 唯一约束：{[c['name'] for c in inspector.get_unique_constraints('positions')]}")
    print(f"[check] positions 索引：{[i['name'] for i in inspector.get_indexes('positions')]}")
    print(f"[check] trades 索引：{[i['name'] for i in inspector.get_indexes('trades')]}")
    print(f"[check] price_history 索引：{[i['name'] for i in inspector.get_indexes('price_history')]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PlayerStock 种子数据脚本")
    parser.add_argument("--reset", action="store_true", help="先删表再重建（仅本地）")
    parser.add_argument("--check", action="store_true", help="只打印表结构与数据条数")
    args = parser.parse_args()

    if args.check:
        check()
    else:
        seed(reset=args.reset)


if __name__ == "__main__":
    main()
