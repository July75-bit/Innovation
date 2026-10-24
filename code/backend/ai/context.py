"""组装 AI 分析所需的行情上下文。

负责人：D

两条数据路径，优先级从高到低：

1. **真实路径** `db_context()`：从 B 的数据库读 `players / positions / price_history`。
   SQL 按 [docs/software/database_design.md] 已冻结的表结构编写（只读 SELECT，不碰 ORM 类名，
   这样 B 怎么给 ORM 命名都不影响本模块）。表不存在 / 无数据 / 依赖未安装时抛异常。
2. **mock 路径** `mock_context()`：直接读 `data/seed_players.json` + 固定演示持仓。

`build_player_context()` 会自动尝试真实路径，失败即回落到 mock —— 目的是
**B 还没实现 models 时 D 也能独立演示**；B 一完成，无需改本文件即可自动切到真实数据。

字段口径见 `docs/algorithm/ai_agent_prompt.md` §2；**不含** `hltv_rating` / `kast` / `adr`（已删除）。
本模块只读：不写库、不改余额/持仓。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

# code/backend/ai/context.py -> parents[3] == 仓库根
ROOT = Path(__file__).resolve().parents[3]
SEED_FILE = ROOT / "data" / "seed_players.json"

logger = logging.getLogger(__name__)

# 演示用假持仓：只给 1 号选手，方便规则版/LLM 版都能给出"有持仓"的建议
DEMO_POSITIONS: dict[int, dict[str, float]] = {
    1: {"quantity": 10, "avg_cost": 120.0},
}
DEMO_POSITION_DEFAULT = {"quantity": 0.0, "avg_cost": 0.0}


# ---------------------------------------------------------------- 工具函数

def pct_change(prev_price: float, current_price: float) -> float:
    """涨跌幅（%，未四舍五入）。

    context 的两条路径与接口层的「最小上下文」共用这一份实现，避免 `_pct` 重复；
    调用方按需自行 `round(..., 2)`。
    """
    if not prev_price:
        return 0.0
    return (current_price - prev_price) / prev_price * 100.0


def _fmt_ts(value: Any) -> str:
    """把 datetime / 字符串统一成 ISO 8601 字符串（前端 `new Date()` 可解析）。"""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


# ---------------------------------------------------------------- mock 路径

def load_seed_players() -> list[dict[str, Any]]:
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return list(data["players"])


def _seed_player(player_id: int) -> dict[str, Any]:
    for player in load_seed_players():
        if player.get("player_id") == player_id:
            return player
    raise LookupError(f"选手 {player_id} 不存在（seed 数据共 {len(load_seed_players())} 名）")


def mock_context(player_id: int) -> dict[str, Any]:
    """从种子数据拼上下文（不需要数据库、不需要网络）。"""
    player = _seed_player(player_id)
    initial = float(player["initial_price"])
    prev = float(player["prev_price"])
    current = float(player["current_price"])
    position = DEMO_POSITIONS.get(player_id, DEMO_POSITION_DEFAULT)

    return {
        "context_source": "mock",
        "player_id": player["player_id"],
        "name": player["name"],
        "display_name": player.get("display_name", ""),
        "team": player.get("team", ""),
        "role": player.get("role", ""),
        "current_price": current,
        "change_pct": round(pct_change(prev, current), 2),
        "rating": player.get("rating", 50),
        "recent_prices": [
            {"ts": "初始价格", "price": initial},
            {"ts": "上一价格", "price": prev},
            {"ts": "当前价格", "price": current},
        ],
        "recent_reasons": [player.get("note") or "演示数据：价格与评分为项目模拟值"],
        "position": dict(position),
    }


# ---------------------------------------------------------------- 真实路径

_SQL_PLAYER = """
SELECT player_id, name, display_name, team, role,
       current_price, prev_price, rating, status
FROM players
WHERE player_id = :player_id
"""

_SQL_HISTORY = """
SELECT price, reason, ts
FROM price_history
WHERE player_id = :player_id
ORDER BY ts
"""

_SQL_POSITION = """
SELECT quantity, avg_cost
FROM positions
WHERE player_id = :player_id
"""


def _read_context(db: Any, player_id: int) -> dict[str, Any]:
    """在给定会话上执行 3 条只读 SELECT 并组装上下文（不 commit、不写库）。"""
    from sqlalchemy import text  # 延迟导入：本地无依赖时也能 import 本模块

    player = db.execute(text(_SQL_PLAYER), {"player_id": player_id}).mappings().first()
    if player is None:
        raise LookupError(f"数据库里没有选手 {player_id}")

    history = db.execute(text(_SQL_HISTORY), {"player_id": player_id}).mappings().all()
    position = db.execute(text(_SQL_POSITION), {"player_id": player_id}).mappings().first()

    recent_prices = [
        {"ts": _fmt_ts(row["ts"]), "price": float(row["price"])} for row in history
    ]
    if not recent_prices:  # 历史为空时至少给出"上一价 → 当前价"两点
        recent_prices = [
            {"ts": "上一价格", "price": float(player["prev_price"])},
            {"ts": "当前价格", "price": float(player["current_price"])},
        ]

    reasons = [row["reason"] for row in history if row.get("reason")]
    return {
        "context_source": "db",
        "player_id": player["player_id"],
        "name": player["name"],
        "display_name": player.get("display_name") or "",
        "team": player.get("team") or "",
        "role": player.get("role") or "",
        "current_price": float(player["current_price"]),
        "change_pct": round(pct_change(float(player["prev_price"]), float(player["current_price"])), 2),
        "rating": player.get("rating") or 50,
        "recent_prices": recent_prices,
        "recent_reasons": reasons[-5:],
        "position": {
            "quantity": float(position["quantity"]) if position else 0.0,
            "avg_cost": float(position["avg_cost"]) if position else 0.0,
        },
    }


def db_context(player_id: int, *, db: Any = None) -> dict[str, Any]:
    """按 database_design.md 的表结构只读取数；任何一步失败都抛异常交给上层回落。

    Args:
        player_id: 选手 ID。
        db: 可选的 SQLAlchemy 会话。接口层把 FastAPI 依赖注入的**同一个只读会话**传进来，
            这样测试里 `get_db` 的依赖覆盖也生效（不会另开一个连到开发库的会话）。
            默认（None）自己开一个会话，供命令行/独立调用使用。
    """
    if db is not None:
        return _read_context(db, player_id)

    from app.core.database import SessionLocal

    with SessionLocal() as own_session:
        return _read_context(own_session, player_id)


# ---------------------------------------------------------------- 对外入口

def build_player_context(
    player_id: int, *, prefer_db: bool = True, db: Any = None
) -> dict[str, Any]:
    """组装上下文：优先真实数据库，失败自动回落 mock（并把回落原因带出来便于排查）。

    `db` 传入接口层的只读会话时，真实路径就在该会话上跑；其余行为不变。
    """
    if prefer_db:
        try:
            return db_context(player_id, db=db)
        except Exception as exc:  # noqa: BLE001 —— 兜底链路：查库失败必须回落 mock，不能把 AI 故障升级成 5xx
            logger.warning("AI 上下文查库失败，回落 seed 数据：player_id=%s %s: %s", player_id, type(exc).__name__, exc)
            context = mock_context(player_id)
            context["context_fallback_reason"] = f"{type(exc).__name__}: {exc}"
            return context
    return mock_context(player_id)


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="打印某位选手的 AI 分析输入上下文（JSON）")
    parser.add_argument("player_id", nargs="?", type=int, default=1, help="选手 ID，默认 1")
    parser.add_argument("--mock", action="store_true", help="强制使用种子数据（不查数据库）")
    args = parser.parse_args(argv)

    context = build_player_context(args.player_id, prefer_db=not args.mock)
    print(json.dumps(context, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
