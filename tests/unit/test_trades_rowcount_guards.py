"""交易接口的"UPDATE 影响行数异常"兜底分支测试（补覆盖率，不改产品代码）。

`trades.py` 里三处 `if update.rowcount != 1:` 是**并发/异常兜底**：
正常情况下永远为 1，只有"读到的行在更新前被别人改掉"才会出现 0。
它们决定"钱和持仓不一致时是 500 还是继续写入错误数据"——所以必须验证：

1. 余额扣减行数为 0 → 回滚 + 500 `INTERNAL_ERROR`，**余额不变**；
2. 加仓行数为 0 → 回滚 + 500，**持仓不变**；
3. 清仓（DELETE）行数为 0 → 回滚 + 500，**持仓与余额都不变**。

做法：只拦 `Update/DELETE` 语句的 `rowcount`（select 正常走），用 `fail_after` 控制
"前几次真实执行、第几次开始返回 0"，从而精确定位到目标分支。
"""

from __future__ import annotations

import sqlalchemy.orm
from sqlalchemy.sql.dml import Delete, Update

SEED = 1


class _ZeroRow:
    """假的执行结果：rowcount = 0（模拟"这行没被更新到"）。"""

    rowcount = 0


def _patch_update_rowcount(monkeypatch, fail_after: int) -> dict[str, int]:
    """让第 fail_after+1 次写语句开始返回 rowcount=0；之前的照常执行。"""
    real_execute = sqlalchemy.orm.Session.execute
    state = {"writes": 0}

    def fake_execute(self, statement, *args, **kwargs):  # noqa: ANN001
        if isinstance(statement, (Update, Delete)):
            state["writes"] += 1
            if state["writes"] > fail_after:
                return _ZeroRow()
        return real_execute(self, statement, *args, **kwargs)

    monkeypatch.setattr(sqlalchemy.orm.Session, "execute", fake_execute)
    return state


def _account(client) -> tuple:
    return (
        client.get("/api/account").json(),
        client.get("/api/positions").json(),
        client.get("/api/trades").json(),
    )


def test_buy_balance_update_missed_rolls_back(client, monkeypatch) -> None:
    """余额扣减影响 0 行 → 回滚并 500，钱与流水都不动。"""
    before = _account(client)
    _patch_update_rowcount(monkeypatch, fail_after=0)

    resp = client.post("/api/trades/buy", json={"player_id": SEED, "quantity": 1})

    assert resp.status_code == 500
    assert resp.json()["code"] == "INTERNAL_ERROR"
    monkeypatch.undo()
    assert _account(client) == before, "回滚后余额/持仓/流水必须与请求前一致"


def test_buy_position_update_missed_rolls_back(client, monkeypatch) -> None:
    """加仓影响 0 行 → 回滚并 500（余额扣减已发生也必须一起回滚）。"""
    client.post("/api/trades/buy", json={"player_id": SEED, "quantity": 1})
    before = _account(client)

    _patch_update_rowcount(monkeypatch, fail_after=1)  # 第 1 次（余额）真实，第 2 次（持仓）返回 0
    resp = client.post("/api/trades/buy", json={"player_id": SEED, "quantity": 1})

    assert resp.status_code == 500
    assert resp.json()["code"] == "INTERNAL_ERROR"
    monkeypatch.undo()
    assert _account(client) == before


def test_sell_clear_position_missed_rolls_back(client, monkeypatch) -> None:
    """清仓 DELETE 影响 0 行 → 回滚并 500（不能出现"钱到账但持股还在"）。"""
    client.post("/api/trades/buy", json={"player_id": SEED, "quantity": 1})
    before = _account(client)

    _patch_update_rowcount(monkeypatch, fail_after=1)  # 第 1 次（余额入账）真实，第 2 次（清仓）返回 0
    resp = client.post("/api/trades/sell", json={"player_id": SEED, "quantity": 1})

    assert resp.status_code == 500
    assert resp.json()["code"] == "INTERNAL_ERROR"
    monkeypatch.undo()
    assert _account(client) == before
