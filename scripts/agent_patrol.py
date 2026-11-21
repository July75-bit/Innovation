"""智能体巡检（Render Cron 每小时跑一次，也可本地手动跑）。

负责人：B

**为什么需要**：前面所有智能体能力都是"用户点了才发生"（被动）。巡检让智能体**自己按时上班**：
- 拉一次行情，算"最需要关注"的标的（波动最大 / 停牌 / 创新高）；
- 触发一次今日简报刷新（`GET /api/agent/brief?refresh=true`），保证用户一进首页看到的是新鲜的；
- 把结果写进日志（`/api/debug/logs` 可查），异常时打印醒目的一行。

**纪律**：只调用**只读**接口 + 简报刷新（简报只写审计表），不下单、不碰余额。

环境变量：
- `BACKEND_BASE_URL`：后端地址（Render cron 里配 `https://playerstock-backend-mdlk.onrender.com`）
- 可选 `PATROL_STALE_PCT`：波动阈值（默认 8.0，超过就标"需要关注"）
- 可选 `PATROL_BRIEF_MAX_AGE_SECONDS`：简报多久算"过期、需要刷新"（默认 1800 秒）。

**保活**：cron 每 10 分钟一次，本身就是对后端的 HTTP 请求；Render 免费实例闲置 15 分钟休眠，
这条巡检让它在工作时间保持热态，用户打开页面不用等 30 秒冷启动。
所以这里**不再每次都 `?refresh=true`**：先看简报是否过期，过期才刷新（省 LLM 调用与费用）。

退出码：0 正常；1 有接口失败（Render 会把它标成 failed，便于发现线上挂了）。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

DEFAULT_BASE = "https://playerstock-backend-mdlk.onrender.com"
STALE_PCT = float(os.getenv("PATROL_STALE_PCT", "8.0"))
TIMEOUT = float(os.getenv("PATROL_TIMEOUT_SECONDS", "90"))  # 冷启动可能要 30s+，超时要放宽
BRIEF_MAX_AGE = float(os.getenv("PATROL_BRIEF_MAX_AGE_SECONDS", "1800"))


def get(base: str, path: str) -> object:
    req = urllib.request.Request(
        base.rstrip("/") + path,
        headers={"User-Agent": "playerstock-patrol/1.0 (+course project)"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _brief_age_seconds(brief: dict) -> float | None:
    """简报生成时间到现在的秒数；解析失败返回 None（按过期处理，宁可多刷一次）。"""
    from datetime import datetime, timezone

    raw = brief.get("generated_at")
    if not raw:
        return None
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    base = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE)
    print(f"[patrol] 目标后端：{base}")
    failures = 0

    try:
        players = get(base, "/api/players")
    except Exception as exc:  # noqa: BLE001
        print(f"[patrol] ✗ 拉取行情失败：{type(exc).__name__}: {exc}")
        return 1

    rows = []
    for p in players:
        change = float(p.get("change_pct") or 0)
        rows.append((abs(change), change, p))
    rows.sort(reverse=True, key=lambda item: item[0])

    print(f"[patrol] 选手 {len(players)} 名；波动榜前三：")
    for _, change, p in rows[:3]:
        flag = "⚠️ 需要关注" if abs(change) >= STALE_PCT else ""
        print(f"          {p['name']:<10} {change:+.2f}%  现价 {p['current_price']} {flag}")

    suspended = [p["name"] for p in players if p.get("status") != "trading"]
    print(f"[patrol] 停牌中：{'、'.join(suspended) if suspended else '无'}")

    # 保活 + 简报：先取当前简报，只有过期才触发刷新（避免每 10 分钟都打一次 LLM）
    try:
        brief = get(base, "/api/agent/brief")
        age = _brief_age_seconds(brief)
        if age is None or age > BRIEF_MAX_AGE:
            brief = get(base, "/api/agent/brief?refresh=true")
            print(f"[patrol] 简报已过期（{age if age is not None else '无法解析'}），已刷新（{brief.get('source')}）")
        else:
            print(f"[patrol] 简报仍新鲜（{age:.0f}s ≤ {BRIEF_MAX_AGE:.0f}s），跳过刷新")
        items = brief.get("items") or []
        print(f"[patrol] 简报（{brief.get('source')}）：{brief.get('summary')}")
        for i, item in enumerate(items, 1):
            print(f"          {i}. {item.get('title')}：{item.get('detail')}")
    except urllib.error.HTTPError as exc:
        failures += 1
        print(f"[patrol] ✗ 简报刷新失败 HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001
        failures += 1
        print(f"[patrol] ✗ 简报刷新失败：{type(exc).__name__}: {exc}")

    alerts = [p["name"] for _, change, p in rows if abs(change) >= STALE_PCT]
    if alerts:
        print(f"[patrol] ⚠️ 达到 {STALE_PCT}% 阈值的标的：{'、'.join(alerts)}")
    else:
        print(f"[patrol] 全市场波动均在 {STALE_PCT}% 以内，无需特别提示")

    print(f"[patrol] 完成（失败接口 {failures} 个）")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
