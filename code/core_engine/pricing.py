"""价格更新算法（方案 A：滚动窗口加权）。

负责人：C

公式::

    P(t+1) = max( P_floor , P(t) × (1 + α·S(t) + β·D(t)) )

其中：
- P(t)     当前价格（> 0）
- S(t)     标准化表现信号 ∈ [-1, +1]
- D(t)     需求信号（净买入量 / 总成交量；初版 β=0 不启用）
- α        表现权重，默认 0.15（满格信号 → ±15%）
- β        需求权重，默认 0.0
- P_floor  价格下限，默认 1.0

信号定义::

    z(t) = (score - mean(最近 N 场)) / std(最近 N 场)     # std=0 → 0
    S(t) = clamp(z(t) / 3, -1, +1)                        # 3σ 记满格

三条护栏：

1. **单次变动上限** `MAX_STEP_PCT = ±20%`（对称 clamp）：无论涨跌，单次最多 20%；
2. **价格下限** `floor`：clamp 之后若仍低于 floor（α 被调大、价格已经很低），
   就停在 floor，并在 reason 里说明；
3. **信号截断**：`|S| ≤ 1`，入参再 clamp 一次，防调用方传超范围值把价格拉爆。
   `Z_FULL_SCALE` 可调：设为 1.0 即"z 值直接 clamp 到 [-1,1]"的字面口径。

参数优先级：**显式传参 > `app.core.config.settings` > 环境变量 > 模块常量**。
`settings` 用 try/except 可选导入：在 backend 里跑时用 B 的配置，
在脚本 / 单测 / 离线回测里没有 `app` 包也能正常工作。
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

# ---------------------------------------------------------------- 默认参数
DEFAULT_ALPHA = 0.15
DEFAULT_BETA = 0.0
DEFAULT_FLOOR = 1.0

#: 单次变动上限（±20%，第 1 天定稿，写死，不通过配置暴露）
MAX_STEP_PCT = 0.20

#: 多少倍标准差记"满格信号"（S = ±1）
Z_FULL_SCALE = 3.0

#: 价格与涨跌幅保留的小数位
PRICE_DECIMALS = 2

_ENV_ALPHA = "PRICING_ALPHA"
_ENV_BETA = "PRICING_BETA"
_ENV_FLOOR = "PRICING_FLOOR"


@dataclass(frozen=True)
class PriceUpdate:
    """一次价格更新的结果，直接对应 price_history 要写的内容。"""

    new_price: float
    change_pct: float
    reason: str  # 例："本场表现提升（S=+0.78），价格上涨 11.66%"
    old_price: float = 0.0
    signal: float = 0.0     # 实际生效的 S(t)
    step_pct: float = 0.0   # 实际生效的变动（已应用护栏），百分数
    capped: bool = False    # 是否触发 ±20% 单次变动上限
    floored: bool = False   # 是否触及价格下限


@lru_cache(maxsize=1)
def _settings():
    """可选读取 B 的后端配置；没有 app 包时返回 None（脚本 / 单测场景）。"""
    try:
        from app.core.config import settings  # type: ignore

        return settings
    except Exception:  # noqa: BLE001 - 配置缺失不应让定价不可用
        return None


def _env_float(name: str) -> float | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _resolve(override: float | None, attr: str, env_name: str, fallback: float) -> float:
    """显式传参 > settings > 环境变量 > 模块常量。"""
    if override is not None:
        return float(override)
    settings = _settings()
    if settings is not None:
        value = getattr(settings, attr, None)
        if value is not None:
            return float(value)
    from_env = _env_float(env_name)
    if from_env is not None:
        return from_env
    return float(fallback)


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _build_reason(
    *,
    signal: float,
    demand_signal: float,
    beta: float,
    change_pct: float,
    capped: bool,
    floored: bool,
) -> str:
    """生成给用户看的中文原因，必须能对应到公式里的某一项。"""
    if signal > 0.3:
        reason = f"本场表现提升（S={signal:+.2f}）"
    elif signal < -0.3:
        reason = f"本场表现下滑（S={signal:+.2f}）"
    else:
        reason = f"表现与近期均值接近（S={signal:+.2f}）"

    if beta > 0 and abs(demand_signal) > 0.3:
        side = "买盘集中" if demand_signal > 0 else "卖盘集中"
        reason += f"，{side}，净买入占比 {demand_signal * 100:.0f}%"

    if capped:
        reason += f"，单次变动超过 ±{MAX_STEP_PCT * 100:.0f}% 上限，已按上限执行"
    if floored:
        reason += "，已触及价格下限，停止下跌"

    if abs(change_pct) < 0.005:
        reason += "，价格维持不变"
    else:
        word = "上涨" if change_pct > 0 else "下跌"
        reason += f"，价格{word} {abs(change_pct):.2f}%"
    return reason


def update_price(
    current_price: float,
    score_delta: float,
    demand_signal: float = 0.0,
    *,
    alpha: float | None = None,
    beta: float | None = None,
    floor: float | None = None,
) -> PriceUpdate:
    """按方案 A 计算新价格。

    Args:
        current_price: 当前价格，必须 > 0。
        score_delta: 标准化表现信号 S(t)，建议先用 ``standardize_score()`` 算好。
        demand_signal: 需求信号 D(t)，初版传 0.0。
        alpha / beta / floor: 不传则按 settings → 环境变量 → 默认值解析。

    Returns:
        PriceUpdate，价格与涨跌幅保留 2 位小数。

    Raises:
        ValueError: 价格非正、数值非法、alpha/beta 为负、floor 非正。
    """
    # ---------------- 入参校验 ----------------
    if current_price is None or not math.isfinite(float(current_price)) or current_price <= 0:
        raise ValueError(f"current_price 必须为正数，收到 {current_price!r}")
    if score_delta is None or not math.isfinite(float(score_delta)):
        raise ValueError(f"score_delta 必须是有限数值，收到 {score_delta!r}")
    if demand_signal is None or not math.isfinite(float(demand_signal)):
        raise ValueError(f"demand_signal 必须是有限数值，收到 {demand_signal!r}")

    alpha_value = _resolve(alpha, "pricing_alpha", _ENV_ALPHA, DEFAULT_ALPHA)
    beta_value = _resolve(beta, "pricing_beta", _ENV_BETA, DEFAULT_BETA)
    floor_value = _resolve(floor, "pricing_floor", _ENV_FLOOR, DEFAULT_FLOOR)

    if alpha_value < 0 or beta_value < 0:
        raise ValueError(f"alpha / beta 不能为负，收到 alpha={alpha_value}, beta={beta_value}")
    if floor_value <= 0:
        raise ValueError(f"floor 必须为正数，收到 {floor_value}")

    # ---------------- 信号与变动 ----------------
    signal = _clip(float(score_delta), -1.0, 1.0)
    demand = _clip(float(demand_signal), -1.0, 1.0)

    raw_step = alpha_value * signal + beta_value * demand
    capped = abs(raw_step) > MAX_STEP_PCT
    step = _clip(raw_step, -MAX_STEP_PCT, MAX_STEP_PCT)  # 对称 clamp：涨跌都封顶 ±20%

    # ---------------- 价格与护栏 ----------------
    new_price = round(float(current_price) * (1 + step), PRICE_DECIMALS)
    floored = new_price < floor_value
    if floored:
        new_price = round(floor_value, PRICE_DECIMALS)

    # 涨跌幅由"取整后的价格"反算，保证「价格 × (1+涨跌幅)」自洽
    change_pct = round((new_price / float(current_price) - 1) * 100, 2)

    reason = _build_reason(
        signal=signal,
        demand_signal=demand,
        beta=beta_value,
        change_pct=change_pct,
        capped=capped,
        floored=floored,
    )

    return PriceUpdate(
        new_price=new_price,
        change_pct=change_pct,
        reason=reason,
        old_price=round(float(current_price), PRICE_DECIMALS),
        signal=round(signal, 4),
        step_pct=round(step * 100, 2),
        capped=capped,
        floored=floored,
    )


def standardize_score(raw_score: float, history: Sequence[float], window: int = 5) -> float:
    """把原始比赛得分转成标准化表现信号 S(t)。

    - 用最近 ``window`` 场的均值和（总体）标准差做 z-score，再除以 3、clamp 到 [-1, 1]；
    - 历史不足 window 场时用已有数据，不补 0；
    - 空历史返回 0.0（第 1 场比赛价格不变，这是刻意的）；
    - 标准差为 0 时返回 0.0（历史完全一致时不放大信号）。

    Args:
        raw_score: 本场原始得分（0-100）。
        history: 历史得分序列（不含本场），按时间先后排列。
        window: 回看场次，默认 5。

    Returns:
        落在 [-1, 1] 的信号值。
    """
    if window < 1:
        raise ValueError(f"window 必须 >= 1，收到 {window}")
    if raw_score is None or not math.isfinite(float(raw_score)):
        raise ValueError(f"raw_score 必须是有限数值，收到 {raw_score!r}")

    recent = [
        float(value)
        for value in (history or [])
        if value is not None and math.isfinite(float(value))
    ][-window:]

    if not recent:
        return 0.0

    mean = sum(recent) / len(recent)
    variance = sum((value - mean) ** 2 for value in recent) / len(recent)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0

    z_score = (float(raw_score) - mean) / std
    return _clip(z_score / Z_FULL_SCALE, -1.0, 1.0)
