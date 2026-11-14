"""只读压力测试：测线上后端在不同并发下的吞吐与延迟。

用法（在仓库根目录）：

    python tests/perf/load_test.py                      # 默认打线上 Render
    python tests/perf/load_test.py --base http://127.0.0.1:8000   # 打本地后端

设计约束（为什么这样写）：
- **只打只读接口**：不碰交易、不碰 AI（不脏数据、不烧 LLM 额度）；
- **带熔断**：错误率超过 20% 或 P95 超过 5s 立即停止后续档位，避免把免费实例打挂；
- **短时档位**：每档 10 秒，档位间冷却 5 秒，让服务缓过来；
- **客户端预热**：先单请求热身，排除冷启动影响（Render 免费实例休眠后约 30–60s 启动）。

输出：控制台表格 + `tests/perf/last_load_test.json`（原始延迟样本，供报告引用）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

#: 只读接口与权重（模拟真实页面浏览：市场页 > 详情页 > 账户）
ENDPOINTS = [
    ("/api/players", 6),
    ("/api/players/1/prices", 3),
    ("/api/account", 1),
]

#: 档位：并发数从低到高；合计约 75 秒
LEVELS = [1, 5, 10, 20, 40]
DEFAULT_DURATION_S = 10.0
COOLDOWN_S = 5.0
ABORT_ERROR_RATE = 0.20
ABORT_P95_MS = 5000.0


def pick_endpoint(seq: int) -> str:
    """按权重轮转挑接口（不随机，保证可复现）。"""
    total = sum(w for _, w in ENDPOINTS)
    pos = seq % total
    acc = 0
    for path, weight in ENDPOINTS:
        acc += weight
        if pos < acc:
            return path
    return ENDPOINTS[0][0]


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(len(ordered) * p))
    return ordered[idx]


async def run_level(client: httpx.AsyncClient, concurrency: int, duration: float) -> dict:
    """跑一个档位，返回统计。"""
    latencies: list[float] = []
    statuses: dict[int, int] = {}
    errors: list[str] = []
    deadline = time.perf_counter() + duration

    async def worker(worker_id: int) -> None:
        seq = worker_id
        while time.perf_counter() < deadline:
            path = pick_endpoint(seq)
            seq += len(ENDPOINTS)
            started = time.perf_counter()
            try:
                resp = await client.get(path)
                cost = (time.perf_counter() - started) * 1000
                latencies.append(cost)
                statuses[resp.status_code] = statuses.get(resp.status_code, 0) + 1
            except Exception as exc:  # noqa: BLE001 网络失败也算结果
                cost = (time.perf_counter() - started) * 1000
                latencies.append(cost)
                errors.append(f"{type(exc).__name__}: {exc}"[:120])

    started_at = time.perf_counter()
    await asyncio.gather(*(worker(i) for i in range(concurrency)))
    wall = time.perf_counter() - started_at

    ok = sum(v for k, v in statuses.items() if 200 <= k < 300)
    total = ok + sum(v for k, v in statuses.items() if not 200 <= k < 300) + len(errors)
    return {
        "concurrency": concurrency,
        "requests": total,
        "ok": ok,
        "rps": round(total / wall, 2) if wall else 0.0,
        "error_rate": round((total - ok) / total, 4) if total else 0.0,
        "p50_ms": round(statistics.median(latencies), 1) if latencies else 0.0,
        "p95_ms": round(pct(latencies, 0.95), 1),
        "p99_ms": round(pct(latencies, 0.99), 1),
        "max_ms": round(max(latencies), 1) if latencies else 0.0,
        "statuses": {str(k): v for k, v in sorted(statuses.items())},
        "errors": errors[:3],
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="只读压测（默认线上 Render）")
    parser.add_argument("--base", default="https://playerstock-backend-mdlk.onrender.com")
    parser.add_argument("--levels", default=",".join(map(str, LEVELS)))
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION_S)
    parser.add_argument("--out", default=str(Path(__file__).parent / "last_load_test.json"))
    args = parser.parse_args()

    DURATION_S = args.duration
    levels = [int(x) for x in args.levels.split(",")]

    limits = httpx.Limits(max_connections=max(levels) + 5, max_keepalive_connections=max(levels))
    async with httpx.AsyncClient(
        base_url=args.base, timeout=30, limits=limits, trust_env=False
    ) as client:
        # 预热：冷启动可能 30–60s
        t0 = time.perf_counter()
        warm = await client.get("/api/health")
        print(f"预热 /api/health → {warm.status_code}，{(time.perf_counter() - t0) * 1000:.0f}ms")

        results = []
        for level in levels:
            stats = await run_level(client, level, args.duration)
            results.append(stats)
            print(
                f"并发 {level:2} → {stats['rps']:6.1f} req/s | "
                f"P50 {stats['p50_ms']:6.0f}ms  P95 {stats['p95_ms']:6.0f}ms  "
                f"错误率 {stats['error_rate']:.1%} | 状态 {stats['statuses']}"
            )
            if stats["error_rate"] > ABORT_ERROR_RATE or stats["p95_ms"] > ABORT_P95_MS:
                print("⚠ 触发熔断（错误率或 P95 超阈值），停止后续档位")
                break
            await asyncio.sleep(COOLDOWN_S)

        payload = {
            "base_url": args.base,
            "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_s": DURATION_S,
            "levels": results,
        }
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n原始结果已写入 {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
