"""检查 LLM 配置能否真的打通（第 6 天 7.3 可选任务，B）。

负责人：B

**什么时候用**：想验证"线上 AI 从 rule_fallback 切到真模型"是否配对了。
代码里三个变量必须**一起**配（见 `docs/mgmt/day6.md` §7.3）：

| 变量 | 说明 |
| --- | --- |
| `LLM_API_KEY` | 只在部署平台填（`sync: false`），不进仓库 |
| `LLM_BASE_URL` | 要**完整 URL**（`.../chat/completions`），不是 base 路径 |
| `LLM_MODEL` | 必须是该服务真实存在的模型名 |

用法：

    # 1) 本地直接问模型（不经过 FastAPI，最快定位 key/URL/模型名的问题）
    set LLM_API_KEY=...   ; 不要写进任何文件
    python scripts/check_llm.py --direct

    # 2) 查线上接口最终走了哪条路（看 source 是 llm 还是 rule_fallback）
    python scripts/check_llm.py --base https://playerstock-backend-mdlk.onrender.com

    # 3) 两个都查
    python scripts/check_llm.py --direct --base https://playerstock-backend-mdlk.onrender.com

退出码：0 = 直接调用成功；1 = 直接调用失败（看下面提示）。`--base` 那条只报告事实，不改判定。
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code" / "backend"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

# 必须与 `code/backend/ai/llm_agent.py` 的请求头保持一致：
# opencode.ai 前置的 Cloudflare 会按客户端指纹屏蔽 urllib 默认 UA（"Python-urllib/3.x"），
# 表现为 HTTP 403 + `error code: 1010`；换任意非默认 UA 即放行（实测 models 接口 403 → 200）。
USER_AGENT = "playerstock-backend/1.0 (+course project; urllib)"


def mask(value: str) -> str:
    if not value:
        return "（空）"
    return f"{value[:6]}…{value[-4:]}" if len(value) > 12 else "已设置"


def show_env() -> dict[str, str]:
    """读环境变量并**清理**（去首尾空白/成对引号），打印清理后的值。

    Windows `set X="v"` 会把引号并进值里，带引号的 URL 直接 `unknown url type`，
    带引号的 key 则 401——这里提前清掉，避免"看起来配对了其实没配对"。
    """
    from ai.llm_agent import _api_key, _base_url, _model

    key = _api_key(None)
    base = _base_url()
    model = _model(None)
    print("[llm] 当前环境：")
    print(f"  LLM_API_KEY  = {mask(key)}")
    print(f"  LLM_BASE_URL = {base}（已归一化：补齐 /chat/completions、去引号与空格）")
    print(f"  LLM_MODEL    = {model}")
    return {"key": key, "base": base, "model": model}


def _probe(url: str, key: str, model: str, timeout: float = 25.0) -> tuple[int, str]:
    """POST 一次 chat/completions，返回 (HTTP 码, 摘要)。200 表示该模型可用。"""
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [{"role": "user", "content": "只回四个字：连接成功"}],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        return 200, str(content or "(空回复)")[:120]
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        try:
            err = json.loads(detail).get("error", {})
            msg = f"{err.get('type', '')}: {err.get('message', '')}"
        except (ValueError, AttributeError):
            msg = detail[:160]
        return exc.code, msg[:160]
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


# 免费档模型（额度可能按账号/模型分别计，逐个试比猜快）。最后一个为付费档，仅账号有余额时可用。
SCAN_CANDIDATES = (
    "deepseek-v4.1-flash-free",
    "glm-5.3-flash-free",
    "mimo-v2.6-flash-free",
    "flint-40b-free",
    "nemotron-3.5-lightning-free",
    "big-pickle",
    "deepseek-v4.1-flash",
)


def scan_models() -> int:
    """逐个试候选模型，打印每个的 HTTP 状态，最后给出建议。"""
    env = show_env()
    if not env["key"]:
        print("\n[llm] ❌ 没设 LLM_API_KEY，无法扫描。")
        return 1

    print(f"\n[llm] 逐个试模型（URL = {env['base']}）")
    working: list[str] = []
    for model in SCAN_CANDIDATES:
        code, msg = _probe(env["base"], env["key"], model)
        label = "✅ 200 可用" if code == 200 else f"HTTP {code}"
        print(f"  {model:<30} {label:<12} {msg[:90]}")
        if code == 200:
            working.append(model)

    if working:
        print(f"\n[llm] ✅ 可用：{working}")
        print(f"[llm] 把 Render 的 `LLM_MODEL` 改成 `{working[0]}` 即可（其余两个变量别动）。")
        return 0

    print("\n[llm] ❌ 候选全部不可用（多半是 429 免费额度用尽）。三个选择：")
    print("  ① 等额度恢复（免费档按周期重置）；② OpenCode Go 订阅后用付费档 deepseek-v4.1-flash；")
    print("  ③ 保持 rule_fallback —— 这是**设计好的降级**，接口仍 200、演示不受影响。")
    return 1


def check_direct() -> int:
    """绕过 FastAPI 直接打一次 chat/completions，错误信息最具体。"""
    env = show_env()
    if not env["key"]:
        print("\n[llm] ❌ 没设 LLM_API_KEY，跳过直接调用。")
        print("  提示：线上不配 key 是**设计好的降级**（rule_fallback），不是故障；")
        print("  要切真模型，按 day6.md §7.3 在 Render 控制台填三个变量。")
        return 1

    # 三个值都取自 show_env() 的清理结果（key/model/url 均已去引号、去空格、URL 已补齐）
    url = env["base"]
    model = env["model"]
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [{"role": "user", "content": "只回四个字：连接成功"}],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env['key']}",
            # 必须带非默认 UA：opencode.ai 前置的 Cloudflare 会按客户端指纹屏蔽
            # urllib 默认的 "Python-urllib/3.x"（实测 HTTP 403 + error code: 1010）；
            # 换任意非默认 UA 即放行——与 `ai/llm_agent.py` 的修复保持一致。
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="POST",
    )

    print(f"\n[llm] POST {url}")
    print(f"[llm] model = {model}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = (
            body.get("choices", [{}])[0].get("message", {}).get("content", "")
            if isinstance(body, dict)
            else ""
        )
        print(f"[llm] ✅ 200，模型回复：{content!r}")
        print("[llm] 说明 key / URL / 模型名三者都通，可以回 Render 填环境变量了。")
        return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        print(f"[llm] ❌ HTTP {exc.code}")
        print(f"  {detail}")
        if exc.code == 403 and "1010" in detail:
            print("  >>> 这是 Cloudflare 的客户端指纹拦截，**不是 key 错**：请求没带非默认 UA。")
            print("      本脚本已带 UA（USER_AGENT 常量），若仍 403/1010，请升级到最新脚本或检查代理。")
        elif exc.code == 429:
            print("  >>> 免费额度用尽（FreeUsageLimitError）。换另一个免费模型试试：")
            print("      `mimo-v2.6-flash-free` / `glm-5.3-flash-free`；或付费档 `deepseek-v4.1-flash`。")
        elif exc.code == 401:
            print("  >>> key 无效：重抄，两端不留空格、不加引号（`oc_sk_` 开头）。")
        else:
            print("  常见原因：① URL 少写 `/chat/completions`；② 模型名不存在（换 flash/free 档）；")
            print("  ③ 模型不支持 `temperature`（如 kimi-k3 会 400）或未开放 chat-completions 协议。")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[llm] ❌ 调用失败：{type(exc).__name__}: {exc}")
        print("  常见原因：网络不通 / URL 写错主机名 / 超时（本脚本 20s）。")
        return 1


def check_endpoint(base: str) -> int:
    """问线上接口：最终给的是 llm 还是 rule_fallback。"""
    url = base.rstrip("/") + "/api/analysis/1"
    print(f"\n[llm] 查询线上接口 {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[llm] ❌ 请求失败：{type(exc).__name__}: {exc}")
        return 1

    source = body.get("source")
    print(f"  source = {source}")
    print(f"  action = {body.get('action')} ｜ risk = {body.get('risk_level')}")
    print(f"  reason = {(body.get('reason') or '')[:80]}")
    if source == "llm":
        print("[llm] ✅ 线上已走真模型（说明三个变量都配对了）。")
        return 0
    print("[llm] ℹ️ 线上仍是 rule_fallback：要么没配 key（设计降级），要么配了但调用失败（会自动回落，不报错）。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 LLM 配置 / 线上 AI 是否走真模型")
    parser.add_argument("--direct", action="store_true", help="用当前环境变量直接调模型")
    parser.add_argument("--scan", action="store_true", help="逐个试候选免费模型，挑还能用的那个")
    parser.add_argument("--base", default="", help="后端根地址，查 /api/analysis/1 的 source")
    args = parser.parse_args()

    if not args.direct and not args.scan and not args.base:
        parser.error("至少给一个：--direct / --scan / --base")

    code = 0
    if args.scan:
        code = scan_models()
    if args.direct:
        code = code or check_direct()
    if args.base:
        ep = check_endpoint(args.base)
        code = code or ep
    return code


if __name__ == "__main__":
    sys.exit(main())
