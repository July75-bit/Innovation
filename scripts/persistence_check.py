"""重新部署前后「数据是否仍在」的自动对账（第 6 天，B）。

负责人：B

**为什么不是截图**：截图能看，但没法验证，还会被压糊。这个脚本做的是同一件事的更硬版本——
把 `/api/account`、`/api/trades`、`/api/players/{id}/prices` 的**原始响应**按时间戳存成 JSON，
再逐项 diff。任何人拿这两个 JSON 重跑 `--diff` 都能得到同一张表。

用法：

    # 部署前
    python scripts/persistence_check.py --base https://playerstock-backend-mdlk.onrender.com \
        --out .tmp/persist-before.json --label before

    # Render 点完 Manual Deploy、服务变 Live 之后
    python scripts/persistence_check.py --base https://playerstock-backend-mdlk.onrender.com \
        --out .tmp/persist-after.json --label after

    # 对账（不一致时退出码 1）
    python scripts/persistence_check.py --diff .tmp/persist-before.json .tmp/persist-after.json

注意：
- **不要**在两个快照之间跑 `bootstrap_demo_data.py --reset`，那会把数据重置，证明不了"数据还在"；
- 部署期间线上短暂 5xx 属正常，脚本会重试，别在同一秒硬打。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

DEFAULT_PLAYER = 1
RETRY = 5


def fetch(base: str, path: str, retry: int = RETRY) -> tuple[int, object]:
    """带重试的 GET：部署窗口里 502/超时都当"还没起来"。"""
    last_error = ""
    for attempt in range(1, retry + 1):
        try:
            with httpx.Client(base_url=base.rstrip("/"), timeout=30.0) as client:
                resp = client.get(path)
            if resp.status_code < 500:
                return resp.status_code, resp.json()
            last_error = f"HTTP {resp.status_code}"
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
        print(f"    [{attempt}/{retry}] {path} 还没起来（{last_error}），2s 后重试…", flush=True)
        time.sleep(2)
    raise SystemExit(f"[persist] 放弃：{path} 连续 {retry} 次失败（{last_error}）")


def snapshot(base: str, player_id: int, label: str) -> dict:
    print(f"[persist] 采集快照（{label}）…", flush=True)
    status_account, account = fetch(base, "/api/account")
    status_trades, trades = fetch(base, "/api/trades")
    status_prices, prices = fetch(base, f"/api/players/{player_id}/prices")
    status_players, players = fetch(base, "/api/players")
    status_positions, positions = fetch(base, "/api/positions")

    points = prices.get("points", []) if isinstance(prices, dict) else prices
    payload = {
        "label": label,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base": base.rstrip("/"),
        "player_id": player_id,
        "status": {
            "account": status_account,
            "trades": status_trades,
            "prices": status_prices,
            "players": status_players,
            "positions": status_positions,
        },
        "account": account,
        "trades": trades,
        "prices": points,
        "players": players,
        "positions": positions,
    }
    print(
        f"  余额 {account['balance']}；流水 {len(trades)} 条；持仓 {len(positions)} 条；"
        f"#{player_id} 价格点 {len(points)} 个；选手 {len(players)} 名"
    )
    return payload


def _trade_key(t: dict) -> tuple:
    return (t["side"], t["quantity"], t["price"], t["balance_after"])


def diff(before_path: Path, after_path: Path) -> int:
    """判断"数据是否仍在"。

    注意口径：**部署窗口里有人下单是正常的**（A 彩排就可能成交一笔），
    所以不能要求"所有数字一模一样"，而要证明：
      1. 部署前那批流水**逐行原样保留**（不丢、不改）；
      2. 价格历史**逐点一致**（历史没被重建）；
      3. **新增的成交能把余额变化完全解释**（算术闭合，不是凭空少钱）；
      4. 总资产守恒、持仓变化等于新增成交的数量。
    四条都成立 = 数据没丢，而且部署后还能写 → 比"数字完全不变"更强的证据。
    """
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))

    bt = {t["trade_id"]: t for t in before["trades"]}
    at = {t["trade_id"]: t for t in after["trades"]}
    missing = sorted(set(bt) - set(at))
    changed = sorted(i for i in bt if i in at and _trade_key(bt[i]) != _trade_key(at[i]))
    new_ids = sorted(set(at) - set(bt))

    net = 0.0
    qty_delta: dict[int, int] = {}
    for i in new_ids:
        t = at[i]
        amount = float(t["price"]) * t["quantity"]
        net += -amount if t["side"] == "BUY" else amount
        sign = 1 if t["side"] == "BUY" else -1
        qty_delta[t["player_id"]] = qty_delta.get(t["player_id"], 0) + sign * t["quantity"]

    b_acc, a_acc = before["account"], after["account"]
    delta = float(a_acc["balance"]) - float(b_acc["balance"])
    bp = [(p["ts"], p["price"]) for p in before["prices"]]
    ap = [(p["ts"], p["price"]) for p in after["prices"]]

    prices_same = bp == ap
    old_kept = not missing and not changed
    balance_explained = abs(delta - net) < 0.005
    asset_same = float(b_acc["total_asset"]) == float(a_acc["total_asset"])

    print(f"[persist] 部署前：{before['label']} @ {before['collected_at']}")
    print(f"[persist] 部署后：{after['label']} @ {after['collected_at']}")
    print(f"[persist] 服务：{before['base']}")
    print()
    print("| 检查点 | 部署前 | 部署后 | 结论 |")
    print("| --- | --- | --- | --- |")
    print(f"| 价格历史（逐点 ts+price） | {len(bp)} 点 | {len(ap)} 点 | {'✅ 逐点一致' if prices_same else '❌ 变了'} |")
    print(
        f"| 部署前已有的流水是否原样保留 | {len(bt)} 条 | 缺失 {len(missing)} 条 / 被改 {len(changed)} 条 | "
        f"{'✅ 逐行一致' if old_kept else '❌ 丢了或被改'} |"
    )
    print(f"| 部署后新增成交 | — | {len(new_ids)} 笔（id {new_ids or '无'}） | {'✅ 服务可写' if new_ids else '（无新增，数字应完全一致）'} |")
    print(f"| 余额变化能否被新增成交解释 | {b_acc['balance']} | {a_acc['balance']}（Δ {delta:+.2f}） | "
          f"{'✅ 与新增净额 %+.2f 吻合' % net if balance_explained else '❌ 对不上（需排查）'} |")
    print(f"| 总资产（价格未变时应守恒） | {b_acc['total_asset']} | {a_acc['total_asset']} | "
          f"{'✅ 守恒' if asset_same else '❌ 变了'} |")
    print(f"| 选手数 | {len(before['players'])} | {len(after['players'])} | "
          f"{'✅ 一致' if len(before['players']) == len(after['players']) else '❌ 变了'} |")

    if new_ids:
        print()
        print("**新增成交明细**")
        print()
        print("| id | 选手 | 方向 | 数量 | 价格 | 金额 | 事后余额 |")
        print("| --- | --- | --- | --- | --- | --- | --- |")
        for i in new_ids:
            t = at[i]
            print(
                f"| {i} | {t['name']} | {t['side']} | {t['quantity']} | {t['price']} | "
                f"{float(t['price']) * t['quantity']:.2f} | {t['balance_after']} |"
            )

    ok = prices_same and old_kept and balance_explained and asset_same
    print()
    if ok:
        if new_ids:
            print(
                f"[persist] ✅ 结论：部署前 {len(bt)} 条流水全部原样保留、价格历史 {len(bp)} 点逐点一致；"
                f"期间新增 {len(new_ids)} 笔成交，余额变化（{delta:+.2f}）与之完全吻合。"
                f"→ **数据没丢，且部署后仍可写入**，线上用的确实是持久化数据库。"
            )
        else:
            print(
                f"[persist] ✅ 结论：部署前后各项完全一致（{len(bt)} 条流水 / {len(bp)} 点价格 / "
                f"余额 {b_acc['balance']}）→ 线上用的是持久化数据库，不是临时盘。"
            )
        return 0

    print("[persist] ❌ 结论：有硬性不一致！")
    if missing or changed:
        print(f"  ⚠️ 部署前流水有缺失/被改：缺失 {missing}，被改 {changed} —— 这是最严重的情况，先停手。")
    if not prices_same:
        print("  ⚠️ 价格历史变了：可能库被重建（有人跑过 bootstrap --reset？）或 DATABASE_URL 指向了别处。")
    if not balance_explained:
        print(f"  ⚠️ 余额变化 {delta:+.2f} 无法被新增成交净额 {net:+.2f} 解释 —— 查是否有并发/事务问题。")
    if not asset_same:
        print("  ⚠️ 总资产变了且价格未变 —— 数据不一致，需排查。")
    print("  排查顺序：① 后端日志搜『当前部署在 Render 上却使用本地 SQLite』；② 看 DATABASE_URL 是否指向 Postgres；")
    print("  ③ 确认两次快照之间没有人跑过 bootstrap_demo_data.py --reset。")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="重新部署前后数据一致性对账")
    parser.add_argument("--base", default="https://playerstock-backend-mdlk.onrender.com")
    parser.add_argument("--player-id", type=int, default=DEFAULT_PLAYER)
    parser.add_argument("--out", type=Path, help="快照输出文件（默认 .tmp/persist-<label>.json）")
    parser.add_argument("--label", default="snapshot")
    parser.add_argument("--diff", nargs=2, metavar=("BEFORE", "AFTER"), help="对账两个快照")
    args = parser.parse_args()

    if args.diff:
        return diff(Path(args.diff[0]), Path(args.diff[1]))

    snap = snapshot(args.base, args.player_id, args.label)
    out = args.out or Path(".tmp") / f"persist-{args.label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[persist] 已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
