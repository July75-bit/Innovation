"""价格历史 reason 可追溯性验收测试（TC-110）。

负责人：D

背景（方案 A，2026-10-24 决策）：`standardize_score` 需要"历史得分序列"，但
`price_history` 只存价格。为避免改表（选项 B），把 `S(t)` 与本轮模拟得分写进
`reason`：重启后仍能从 `/api/players/{id}/prices` 回答"这条价格是哪场比赛、什么
得分算出来的"。

当前实现（见 `docs/software/database_design.md` §3.2「分工待办」）：
- C 的 `update_price` reason 带 `S=±x.xx`；
- B 在落库层临时拼 `（本轮模拟得分 X.X）`（`update_prices.with_score_in_reason`），
  约定 C 接管后由 C 直接拼好、B 只透传。
本测试固定"最终写进 `price_history.reason` 的口径"，两边谁拼都算通过。

数据用 `tests/conftest.py` 的临时库（4 名选手），不读写仓库里的 playerstock.db。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.core.price_update import apply_updates

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

PLAYER_ID = 1
CURRENT_PRICE = 126.0
NEW_PRICE = 132.3
CHANGE_PCT = 5.0
MATCH_SCORE = 88.5
SIGNAL = 0.42
C_REASON = "本场表现提升（S=+0.42）"


def _c_export(tmp_path: Path) -> Path:
    """模拟 C 的 `python scripts/simulate_match.py --json` 导出（字段与真实导出一致）。"""
    payload = {
        "generated_at": "2026-10-24T02:00:00",
        "seed": 42,
        "rounds": 1,
        "window": 5,
        "updates": [
            {
                "player_id": PLAYER_ID,
                "round_no": 1,
                "score": MATCH_SCORE,
                "signal": SIGNAL,
                "old_price": CURRENT_PRICE,
                "new_price": NEW_PRICE,
                "change_pct": CHANGE_PCT,
                "prev_price": 120.0,
                "reason": C_REASON,
            }
        ],
    }
    path = tmp_path / "price_updates.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_plan_from_json_reason_carries_signal_and_score(tmp_path: Path) -> None:
    """C 的导出经 B 的落库计划后，reason 同时带 S 与得分（可追溯）。"""
    from update_prices import plan_from_json

    planned = plan_from_json(_c_export(tmp_path))

    assert len(planned) == 1
    item = planned[0]
    assert item.player_id == PLAYER_ID
    assert float(item.new_price) == NEW_PRICE
    assert "S=+0.42" in item.reason
    assert "本轮模拟得分 88.5" in item.reason


def test_plan_from_engine_reason_carries_signal_and_score(session_factory) -> None:
    """不传 JSON、进程内直调 C 引擎时，reason 同样带 S 与得分。"""
    from app.models import Player
    from update_prices import plan_from_engine

    with session_factory() as db:
        player = db.get(Player, PLAYER_ID)

    planned, skipped = plan_from_engine([player], seed=42)

    assert not skipped
    assert len(planned) == 1
    assert "S=" in planned[0].reason
    # C 已接管文案（`update_price(..., score=...)` → "本轮得分 76.6，S=-1.00"），
    # 这里只断言"带得分"这一语义，不钉死具体用词，免得两边切换措辞就误报。
    assert "得分" in planned[0].reason


def test_db_and_prices_api_keep_traceable_reason(session_factory, client, tmp_path: Path) -> None:
    """落库后换会话也能从 /prices 读到可追溯的 reason（读路径；进程级重启由 T3-05 覆盖）。"""
    from update_prices import plan_from_json

    planned = plan_from_json(_c_export(tmp_path))
    with session_factory() as db:
        apply_updates(db, planned)

    points = client.get(f"/api/players/{PLAYER_ID}/prices").json()["points"]
    assert len(points) == 3  # conftest 的 2 个点 + 本次 1 个点
    latest = points[-1]
    assert latest["price"] == NEW_PRICE
    assert "S=+0.42" in latest["reason"]
    assert "本轮模拟得分 88.5" in latest["reason"]

    # 价格与顺序：升序且最新价同步到选手详情
    prices = [point["price"] for point in points]
    assert prices == sorted(prices)
    detail = client.get(f"/api/players/{PLAYER_ID}").json()
    assert detail["current_price"] == NEW_PRICE


def test_reason_truncated_to_db_limit() -> None:
    """reason 超过 price_history.reason 的 200 字上限时安全截断，不能写库失败。"""
    from update_prices import with_score_in_reason

    text = with_score_in_reason("很长的原因" * 50, MATCH_SCORE)

    assert len(text) <= 200
    assert text.endswith("…")
