"""接口冒烟/联调自测：对着**任意**已起来的后端跑一遍交易闭环与错误分支，输出 markdown 表格。

负责人：B

两个用途：
1. 本地联调时当"B 作为被测方"的自查（错误码 / 并发 / 成交价语义）；
2. 第 5 天线上验收时把 `API_BASE` 换成公网地址，直接产出一份可贴进报告的记录。

它会**真实下单**（买 2 股 → 卖 1 股 → 并发卖 1），所以只对演示库/演示环境跑。

用法：
    # 本地
    python scripts/smoke_test_api.py --base http://127.0.0.1:8000

    # 线上（第 5 天验收）
    python scripts/smoke_test_api.py --base https://playerstock-backend.onrender.com

    # 只读模式（不产生交易，只看能不能读出来）
    python scripts/smoke_test_api.py --base https://xxx.onrender.com --read-only
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

ROWS: list[str] = []


def note(*cells: str) -> None:
    ROWS.append("| " + " | ".join(cells) + " |")


def brief(resp: httpx.Response) -> str:
    """把响应压成一行：优先展示契约里的 code / message。"""
    try:
        body = resp.json()
    except Exception:  # noqa: BLE001
        return (resp.text or "")[:80]
    if isinstance(body, dict):
        if "code" in body and "message" in body:
            return f"{body.get('code')} / {body.get('message')}"
        return ", ".join(f"{k}={v}" for k, v in list(body.items())[:6])
    if isinstance(body, list):
        return f"{len(body)} 条"
    return str(body)[:80]


class Api:
    def __init__(self, base: str) -> None:
        self.client = httpx.Client(base_url=base.rstrip("/"), timeout=15.0)

    def get(self, path: str) -> httpx.Response:
        return self.client.get(path)

    def trade(self, player_id: int, quantity: float, side: str) -> httpx.Response:
        return self.client.post(f"/api/trades/{side}", json={"player_id": player_id, "quantity": quantity})

    def account(self) -> dict:
        return self.client.get("/api/account").json()

    def positions(self) -> list:
        return self.client.get("/api/positions").json()


def main() -> int:
    parser = argparse.ArgumentParser(description="后端接口冒烟/联调自测")
    parser.add_argument("--base", default="http://127.0.0.1:8000", help="后端根地址")
    parser.add_argument("--player-id", type=int, default=1, help="用于买卖的选手 ID")
    parser.add_argument("--read-only", action="store_true", help="只跑读接口，不下单")
    args = parser.parse_args()

    api = Api(args.base)
    pid = args.player_id

    health = api.get("/api/health")
    note("健康检查", "`GET /api/health`", f"{health.status_code} `{brief(health)}`")

    players = api.get("/api/players").json()
    head = ", ".join(f"#{p['player_id']} {p['name']} {p['current_price']}" for p in players[:3])
    note("市场列表", "`GET /api/players`", f"{len(players)} 名；前三：{head}")

    detail = api.get(f"/api/players/{pid}").json()
    note(
        "选手详情",
        f"`GET /api/players/{pid}`",
        f"{detail['name']} 现价 {detail['current_price']}，涨跌 {detail.get('change_pct')}%，"
        f"状态 {detail.get('status')}",
    )

    points = api.get(f"/api/players/{pid}/prices").json()["points"]
    ts = [p["ts"] for p in points]
    note(
        "价格历史",
        f"`GET /api/players/{pid}/prices`",
        f"**{len(points)} 点**，升序={ts == sorted(ts)}，末点 {points[-1]['price']}",
    )

    acc = api.account()
    note("账户", "`GET /api/account`", f"余额 {acc['balance']}，总资产 {acc['total_asset']}")

    if args.read_only:
        print("| 环节 | 请求 | 实际结果 |")
        print("| --- | --- | --- |")
        for row in ROWS:
            print(row)
        return 0

    # —— 一买一卖 ——
    price_now = api.get(f"/api/players/{pid}").json()["current_price"]
    buy = api.trade(pid, 2, "buy")
    body = buy.json() if buy.status_code == 200 else {}
    expected_amount = round(float(body.get("price", 0)) * 2, 2)
    note(
        "买入 2 股",
        "`POST /api/trades/buy`",
        f"{buy.status_code}，成交价 **{body.get('price')}**（= 当时最新价 {price_now}），"
        f"金额 {expected_amount}，余额 {body.get('balance')}",
    )

    pos = api.positions()
    if pos:
        first = pos[0]
        note(
            "买入后持仓",
            "`GET /api/positions`",
            f"{len(pos)} 条：{first['name']} × {first['quantity']}，均价 {first['avg_cost']}，浮盈 {first['profit']}",
        )

    sell = api.trade(pid, 1, "sell")
    sbody = sell.json() if sell.status_code == 200 else {}
    note(
        "卖出 1 股",
        "`POST /api/trades/sell`",
        f"{sell.status_code}，成交价 {sbody.get('price')}，余额 {sbody.get('balance')}",
    )

    trades = api.get("/api/trades").json()
    note("交易流水", "`GET /api/trades`", f"{len(trades)} 条")

    # —— 错误分支：错误码必须与契约 §5 一致 ——
    # 注意契约 §4.7 的顺序是"余额先于持仓上限"，所以两条用例要挑不同的选手：
    #   · 余额不足 → 挑**最贵的可交易**选手（×50 一定买不起）
    #   · 超上限   → 挑**最便宜的可交易**选手（×51 买得起，才轮到上限拦）
    trading = [p for p in players if p.get("status") == "trading" and p["player_id"] != pid]
    suspended = next((p for p in players if p.get("status") != "trading"), None)

    if trading:
        rich = max(trading, key=lambda p: float(p["current_price"]))
        err = api.trade(rich["player_id"], 50, "buy")
        note("余额不足", f"买 #{rich['player_id']} × 50", f"{err.status_code} `{brief(err)}`")

        cheapest = min(trading, key=lambda p: float(p["current_price"]))
        err = api.trade(cheapest["player_id"], 51, "buy")
        note("超持仓上限", f"买 #{cheapest['player_id']} × 51", f"{err.status_code} `{brief(err)}`")

    for qty in (0, -1, 1.5):
        err = api.trade(pid, qty, "buy")
        note(f"非法数量 {qty}", f"买 #{pid} × {qty}", f"{err.status_code} `{brief(err)}`")

    err = api.trade(99999, 1, "buy")
    note("选手不存在", "买 #99999", f"{err.status_code} `{brief(err)}`")

    if suspended:
        err = api.trade(suspended["player_id"], 1, "buy")
        note(
            "暂停交易",
            f"买 #{suspended['player_id']}（{suspended['status']}）",
            f"{err.status_code} `{brief(err)}`",
        )

    err = api.trade(pid, 5, "sell")
    note("持仓不足", f"卖 #{pid} × 5", f"{err.status_code} `{brief(err)}`")

    # —— 并发：只持 1 股时两个请求同时卖 1，必须只成功一次 ——
    with ThreadPoolExecutor(max_workers=2) as pool:
        both = list(pool.map(lambda _: api.trade(pid, 1, "sell"), range(2)))
    codes = sorted(r.status_code for r in both)
    rest = ", ".join(f"{p['name']}×{p['quantity']}" for p in api.positions()) or "无"
    note(
        "**并发卖出**",
        "同时发 2 个「卖 1」",
        f"状态码 {codes}；剩余持仓 {rest}；余额 {api.account()['balance']}",
    )

    print("| 环节 | 请求 | 实际结果 |")
    print("| --- | --- | --- |")
    for row in ROWS:
        print(row)

    final = api.account()
    print()
    print(f"最终余额 = {final['balance']}，持仓 = {api.positions()}，流水 = {len(api.get('/api/trades').json())} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
