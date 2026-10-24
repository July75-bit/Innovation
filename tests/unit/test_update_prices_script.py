"""价格更新脚本（`scripts/update_prices.py`）的测试。

负责人：B

C 的 `update_price` / `simulator` 已经落地，所以这里测的是**真实引擎接通后的行为**，
不再有临时规则：

1. 用 C 的模拟比赛 + 定价引擎算出变动，暂停交易（`suspended`）的选手跳过；
2. 同一 seed 完全可复现（现场演示必须能重跑出同一组数）；
3. 落库后 `/prices` 多一个点，`reason` 带 S 值与"本轮模拟得分"（可追溯）；
4. 也支持吃 C 的 `--json` 导出（C 调模型、B 落库，两条线不互相等）。
"""

from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import update_prices  # noqa: E402  （脚本目录不在默认 pythonpath 里）

from app.core.price_update import apply_updates  # noqa: E402
from app.models import Player  # noqa: E402

SEED_ZYWOO = 1
SEED_SH1RO = 7  # status = suspended

ZH = re.compile(r"[\u4e00-\u9fff]")


def _players(session) -> list[Player]:
    return list(session.scalars(select(Player).order_by(Player.player_id)).all())


def test_suspended_players_are_skipped(session_factory) -> None:
    """比赛中的选手不定价（与暂停交易规则一致）。"""
    with session_factory() as db:
        planned, skipped = update_prices.plan_from_engine(_players(db), seed=42)

    assert [p.player_id for p in skipped] == [SEED_SH1RO]
    assert SEED_SH1RO not in [p.player_id for p in planned]
    assert len(planned) == 3


def test_reason_carries_signal_and_score(session_factory) -> None:
    """reason 必须能追溯到"哪场表现"：带 S 值 + 本轮得分，且是中文。"""
    with session_factory() as db:
        planned, _ = update_prices.plan_from_engine(_players(db), seed=42)

    for item in planned:
        assert item.new_price > 0
        assert ZH.search(item.reason), f"reason 不是中文：{item.reason}"
        assert "本轮模拟得分" in item.reason, f"reason 缺得分：{item.reason}"
        assert "S=" in item.reason, f"reason 缺 S 值：{item.reason}"


def test_same_seed_is_reproducible(session_factory) -> None:
    """同 seed 两次算出的（价格, 涨跌幅, reason）必须完全一致。"""
    with session_factory() as db:
        players = _players(db)

    first, _ = update_prices.plan_from_engine(players, seed=42)
    second, _ = update_prices.plan_from_engine(players, seed=42)

    signature = lambda items: [  # noqa: E731
        (i.player_id, str(i.new_price), i.change_pct, i.reason) for i in items
    ]
    assert signature(first) == signature(second)

    different, _ = update_prices.plan_from_engine(players, seed=7)
    assert signature(different) != signature(first), "换 seed 应该算出不同结果"


def test_engine_result_writes_history_and_keeps_money(session_factory, client) -> None:
    """落库：`/prices` 多一个点，余额与持仓股数不受影响。"""
    before = client.get(f"/api/players/{SEED_ZYWOO}/prices").json()["points"]
    assert len(before) == 2

    with session_factory() as db:
        planned, _ = update_prices.plan_from_engine(_players(db), seed=42)
        apply_updates(db, planned)

    after = client.get(f"/api/players/{SEED_ZYWOO}/prices").json()["points"]
    assert len(after) == 3
    assert after[-1]["reason"].startswith("本场表现") or "S=" in after[-1]["reason"]
    assert after[-1]["reason"].endswith("）")
    assert "本轮模拟得分" in after[-1]["reason"]
    # 契约要的是"时间升序"，价格本身当然可以涨也可以跌（这次 ZywOo 是 -15%）
    timestamps = [p["ts"] for p in after]
    assert timestamps == sorted(timestamps)
    assert after[-1]["price"] == pytest.approx(107.10)

    account = client.get("/api/account").json()
    assert account["balance"] == pytest.approx(5000.00), "价格更新不许动余额"
    assert client.get("/api/positions").json() == [], "价格更新不许动持仓"


def test_reason_is_truncated_to_column_limit() -> None:
    """`price_history.reason` 是 VARCHAR(200)，超长必须截断而不是写库失败。"""
    text = update_prices.with_score_in_reason("涨" * 500, 88.5)
    assert len(text) <= 200
    assert text.endswith("…")


def test_plan_from_json_reads_c_export(tmp_path) -> None:
    """吃 C 的 `--json` 导出：补上 name、保留比赛日期 ts、reason 追加得分。"""
    payload = {
        "seed": 42,
        "updates": [
            {
                "player_id": 1,
                "round_no": 1,
                "ts": "2026-11-01",
                "score": 88.5,
                "signal": 0.5,
                "old_price": 126.0,
                "new_price": 135.45,
                "change_pct": 7.5,
                "reason": "本场表现提升（S=+0.50），价格上涨 7.50%",
            }
        ],
    }
    path = tmp_path / "updates.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    planned = update_prices.plan_from_json(path, {1: "ZywOo"})
    assert len(planned) == 1
    item = planned[0]
    assert item.name == "ZywOo"
    assert item.new_price == Decimal("135.45")
    assert item.ts is not None and item.ts.year == 2026 and item.ts.month == 11
    assert item.reason.endswith("（本轮模拟得分 88.5）")


def test_plan_from_json_rejects_empty_updates(tmp_path) -> None:
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"updates": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="没有 updates"):
        update_prices.plan_from_json(path)
