"""看一眼当前 `DATABASE_URL` 指向的库：方言、表清单、行数、（可选）关键业务校验。

负责人：B｜第 5 天上线收尾

**为什么需要**：检查单里有一项是"Postgres 控制台能看到 `players` / `trades` 等表"。
Render 免费 Postgres 没有网页版数据浏览器，要么装 psql 连、要么用这个脚本——
后者不用装任何东西，一条命令把"表 + 行数"打出来，直接截图就是证据。

用法：

    # 线上（用 External Database URL，含密码，勿提交）
    $env:DATABASE_URL = "<External Database URL>"
    python scripts/inspect_db.py

    # 本地（不传就落到 code/backend/playerstock.db）
    python scripts/inspect_db.py

    # 顺带做业务自检（16 名选手、每人价格点数、余额）
    python scripts/inspect_db.py --check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code" / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="查看当前库的表与行数")
    parser.add_argument("--check", action="store_true", help="额外做业务自检（选手/价格点/余额）")
    args = parser.parse_args()

    from sqlalchemy import func, inspect, select

    from app.core.config import settings
    from app.core.database import Base, SessionLocal
    from app.models import Player, PriceHistory, User

    masked = settings.database_url
    if "@" in masked and "://" in masked:  # 掩掉连接串里的密码
        scheme, rest = masked.split("://", 1)
        if "@" in rest:
            cred, host = rest.split("@", 1)
            user = cred.split(":", 1)[0]
            masked = f"{scheme}://{user}:***@{host}"

    print(f"[inspect] DATABASE_URL = {masked}")
    print(
        f"[inspect] 方言 = {settings.database_url.split(':', 1)[0]}"
        f"{'（本地 SQLite）' if settings.is_sqlite else '（托管库，持久化生效）'}"
    )

    with SessionLocal() as db:
        tables = inspect(db.get_bind()).get_table_names()
        print(f"\n[inspect] 表清单（共 {len(tables)} 张）：")
        for name in sorted(tables):
            table = Base.metadata.tables.get(name)
            if table is None:  # 库里存在但不是本项目的表（例如别处手工建的）
                print(f"  - {name:<16}      -")
                continue
            count = db.execute(select(func.count()).select_from(table)).scalar()
            print(f"  - {name:<16} {count:>6} 行")

        if args.check:
            players = db.scalar(select(func.count()).select_from(Player))
            balance = db.scalar(select(User.balance).where(User.nickname == "demo"))
            print(f"\n[inspect] 业务自检：选手 {players} 名；demo 余额 {balance}")
            rows = db.execute(
                select(Player.player_id, Player.name, func.count(PriceHistory.price_id))
                .join(PriceHistory, PriceHistory.player_id == Player.player_id, isouter=True)
                .group_by(Player.player_id, Player.name)
                .order_by(Player.player_id)
            ).all()
            for player_id, name, points in rows:
                print(f"  #{player_id} {name:<7} {points:>2} 个价格点")

    return 0


if __name__ == "__main__":
    sys.exit(main())
