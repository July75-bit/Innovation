"""L4 评测（真模型）：对线上后端跑黄金集 20 例，统计契约/可核/合规通过率。

默认**被 `-m "not live"` 排除**（见 pyproject addopts），只有显式 `-m live` 才跑，且需要：

    $env:AGENT_BASE_URL = "https://playerstock-backend-mdlk.onrender.com"
    python -m pytest tests/eval -m live -q -s

为什么默认排除：评测要联网、要真实密钥、单例 2–3 秒（20 例约 1 分钟），
不适合每次提交都跑——这正是课件「L1–L3 离线必跑、L4 每晚跑」的分层。

产物：跑完把每例结果写到 `tests/eval/last_live_run.json`，供报告引用。
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

GOLDEN = json.loads((Path(__file__).parent / "golden_cases.json").read_text(encoding="utf-8"))
RATE_CASES = [c for c in GOLDEN["cases"] if c["kind"] in {"player", "suspended"}]
EDGE_CASES = [c for c in GOLDEN["cases"] if c["kind"].startswith("edge")]
THRESHOLDS = GOLDEN["thresholds"]
FORBIDDEN = GOLDEN["forbidden_words"]

VALID_ACTION = {"BUY", "SELL", "HOLD"}
VALID_RISK = {"LOW", "MEDIUM", "HIGH"}
VALID_SOURCE = {"llm", "rule_fallback"}
FIELDS = {"player_id", "action", "reason", "risk_level", "source", "disclaimer"}

pytestmark = pytest.mark.live


def _base_url() -> str:
    url = os.getenv("AGENT_BASE_URL", "").rstrip("/")
    if not url:
        pytest.skip("未设置 AGENT_BASE_URL，跳过线上 L4 评测")
    return url


def _get(path: str, tries: int = 4) -> tuple[int, dict | None, float]:
    """带退避的 GET（免费实例冷启动约 30–60s）。返回 (状态码, JSON, 耗时ms)。"""
    url = _base_url() + path
    last: tuple[int, dict | None, float] = (0, None, 0.0)
    for attempt in range(tries):
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=45) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body), (time.perf_counter() - started) * 1000
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None
            last = (exc.code, payload, (time.perf_counter() - started) * 1000)
            if 400 <= exc.code < 500:  # 4xx 是确定性结果，不重试
                return last
        except Exception:  # noqa: BLE001 网络抖动/冷启动
            last = (0, None, (time.perf_counter() - started) * 1000)
        if attempt < tries - 1:
            time.sleep(3 + attempt * 4)
    return last


@pytest.fixture(scope="module")
def results() -> dict:
    """跑一遍黄金集，把结果缓存给各断言复用（避免 20 例重复请求）。"""
    collected = []
    for case in GOLDEN["cases"]:
        status, body, elapsed = _get(f"/api/analysis/{case['player_id']}")
        collected.append(
            {"id": case["id"], "kind": case["kind"], "player_id": case["player_id"],
             "status": status, "body": body, "elapsed_ms": round(elapsed, 1)}
        )
    payload = {"base_url": _base_url(), "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "results": collected}
    (Path(__file__).parent / "last_live_run.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return payload


def test_live_contract_pass_rate(results) -> None:
    """契约完整率必须 100%（6 字段 + 枚举 + 来源）。"""
    bad = []
    for item in results["results"]:
        if item["kind"].startswith("edge"):
            continue
        body = item["body"] or {}
        ok = (
            item["status"] == 200
            and set(body) == FIELDS
            and body.get("action") in VALID_ACTION
            and body.get("risk_level") in VALID_RISK
            and body.get("source") in VALID_SOURCE
            and body.get("player_id") == item["player_id"]
        )
        if not ok:
            bad.append((item["id"], item["status"], sorted(body)))
    assert not bad, f"契约不合格：{bad[:5]}"
    assert len([i for i in results["results"] if not i["kind"].startswith("edge")]) == len(RATE_CASES)


def test_live_reason_with_number_rate(results) -> None:
    """理由可核率 ≥80%（理由里要有得分/S/涨跌幅这类可核对数字）。"""
    scored = [i for i in results["results"] if not i["kind"].startswith("edge")]
    hits = sum(1 for i in scored if re.search(r"\d", (i["body"] or {}).get("reason", "")))
    rate = hits / len(scored)
    assert rate >= THRESHOLDS["reason_with_number_rate"], f"含数字比例 {rate:.0%}，低于阈值"


def test_live_no_forbidden_words(results) -> None:
    """合规用词 100%：不得出现保证收益类表述。"""
    for item in results["results"]:
        text = json.dumps(item["body"] or {}, ensure_ascii=False)
        for word in FORBIDDEN:
            assert word not in text, f"{item['id']} 出现违规词「{word}」"


def test_live_edge_cases_are_4xx(results) -> None:
    """边界诚实：不存在/非法/越界选手必须是 4xx（不能 200 编造一份建议）。"""
    for item in results["results"]:
        if not item["kind"].startswith("edge"):
            continue
        assert 400 <= item["status"] < 500, f"{item['id']} 期望 4xx，实际 {item['status']}"


def test_live_no_model_call_on_edge(results) -> None:
    """边界用例的响应必须是标准错误体（不含 AI 字段），说明没进模型。"""
    for item in results["results"]:
        if not item["kind"].startswith("edge"):
            continue
        body = item["body"] or {}
        assert "action" not in body and "reason" not in body, f"{item['id']} 疑似进了模型"


def test_live_p95_latency(results) -> None:
    """时延 P95 ≤ 10s（课件门禁）。"""
    times = sorted(i["elapsed_ms"] for i in results["results"] if i["status"] == 200)
    if not times:
        pytest.skip("没有成功样本")
    p95 = times[max(0, int(len(times) * 0.95) - 1)]
    assert p95 <= THRESHOLDS["p95_latency_ms"], f"P95={p95:.0f}ms 超过阈值"
