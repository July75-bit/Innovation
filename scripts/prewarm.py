"""演示前预热：把 Render 免费实例叫醒，并确认关键接口真的可用。

负责人：B｜第 5 天上线收尾

**为什么需要**：Render 免费 Web Service 空闲约 15 分钟会休眠，下一个请求要等容器冷启动
（实测约 1 分钟）。答辩/验收如果直接打开前端，很可能看到一个转圈的白页，看起来像"服务挂了"。
所以演示前 10–15 分钟先跑这个脚本，把后端叫醒并确认数据在。

用法：

    # 默认打线上后端
    python scripts/prewarm.py --base https://playerstock-backend-mdlk.onrender.com

    # 本地联调也可以用
    python scripts/prewarm.py --base http://127.0.0.1:8000

    # 顺便核一下行情数据（8 人、价格点 ≥10）
    python scripts/prewarm.py --base https://... --min-points 10

退出码：0 = 已就绪；1 = 超时仍不可用（此时不要演示，先看 Render 控制台/日志）。
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def wait_healthy(base: str, timeout_s: float, interval_s: float) -> float | None:
    """轮询 /api/health 直到成功，返回耗时（秒）；超时返回 None。"""
    deadline = time.monotonic() + timeout_s
    attempt = 0
    started = time.monotonic()

    while time.monotonic() < deadline:
        attempt += 1
        try:
            with httpx.Client(base_url=base, timeout=15.0) as client:
                resp = client.get("/api/health")
            if resp.status_code == 200:
                elapsed = time.monotonic() - started
                print(f"  [{attempt}] 200 {resp.json()}  耗时 {elapsed:.1f}s", flush=True)
                return elapsed
            print(f"  [{attempt}] {resp.status_code}，继续等…", flush=True)
        except Exception as exc:  # noqa: BLE001 - 冷启动期间连接被拒/超时都属正常
            print(f"  [{attempt}] 还没起来（{type(exc).__name__}），继续等…", flush=True)
        time.sleep(interval_s)

    return None


def check_data(base: str, min_points: int) -> bool:
    """确认行情与价格历史都读得出来（冷启动后第一次查库可能慢一点）。"""
    with httpx.Client(base_url=base, timeout=30.0) as client:
        players = client.get("/api/players").json()
        account = client.get("/api/account").json()

    print(f"  选手 {len(players)} 名；账户余额 {account['balance']}", flush=True)
    if not players:
        print("  ⚠️ 市场是空的，先跑 scripts/bootstrap_demo_data.py 灌数据", flush=True)
        return False

    if min_points <= 0:
        return True

    ok = True
    with httpx.Client(base_url=base, timeout=30.0) as client:
        for player in players:
            if player.get("status") != "trading":
                continue
            points = client.get(f"/api/players/{player['player_id']}/prices").json()["points"]
            flag = "OK" if len(points) >= min_points else "!!"
            if len(points) < min_points:
                ok = False
            print(f"  {flag} #{player['player_id']} {player['name']}: {len(points)} 个价格点", flush=True)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="演示前预热 Render 免费实例并核数据")
    parser.add_argument("--base", required=True, help="后端根地址，如 https://xxx.onrender.com")
    parser.add_argument("--timeout", type=float, default=180.0, help="最长等待秒数（默认 180）")
    parser.add_argument("--interval", type=float, default=3.0, help="轮询间隔秒数（默认 3）")
    parser.add_argument(
        "--min-points", type=int, default=0, help="要求每名可交易选手至少几个价格点（0=不查）"
    )
    args = parser.parse_args()

    base = args.base.rstrip("/")
    print(f"[prewarm] 目标：{base}", flush=True)
    print("[prewarm] 等待 /api/health …", flush=True)

    elapsed = wait_healthy(base, args.timeout, args.interval)
    if elapsed is None:
        print(f"\n[prewarm] ❌ {args.timeout:.0f}s 内没起来。", flush=True)
        print("  处理：Render 控制台看服务是否 Live、日志有没有启动报错；再不行重新部署一次。", flush=True)
        return 1

    if elapsed > 10:
        print(f"\n[prewarm] 冷启动约 {elapsed:.0f}s（免费实例休眠后的正常现象）", flush=True)
    else:
        print("\n[prewarm] 实例本来就是醒的（响应很快）", flush=True)

    print("\n[prewarm] 核对数据 …", flush=True)
    if not check_data(base, args.min_points):
        return 1

    print("\n[prewarm] ✅ 已就绪，可以开始演示", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
