"""价格更新算法。

负责人：C

默认方案 A：滚动窗口加权（完全可解释，每条价格变动可拆解归因）

    P(t+1) = max(P_floor, P(t) * (1 + alpha * S(t) + beta * D(t)))

其中：
- P(t)          当前价格
- S(t)          标准化后的表现信号（最近 N 局的得分/胜负/评级变化，一般落在 [-1, 1]）
- D(t)          需求信号：该选手净买入量占比（初版可令 beta=0，纯表现驱动）
- alpha         表现权重，可调（默认取 settings.pricing_alpha）
- beta          需求权重（默认 settings.pricing_beta = 0，后续迭代再启用）
- P_floor       价格下限（settings.pricing_floor），防止价格归零或变负

如果时间允许可以升级到方案 B（表现项 + 市场项 + 交互项 gamma）或方案 C（LMSR），
但方案 A 必须先跑通，因为它是"保底可交付"的那一档。
"""

from dataclasses import dataclass

import math
from dataclasses import dataclass
from functools import lru_cache

# ---------------------------------------------------------------- 默认参数
# 优先级：调用方显式传参 > app.core.config.settings > 下面的常量
DEFAULT_ALPHA = 0.15
DEFAULT_BETA = 0.0
DEFAULT_FLOOR = 1.0
#: 单次涨幅上限（第 1 天定稿：+20%），写死，不对外暴露。
#: 只封顶上涨、不封顶下跌 —— 下跌由 floor 兜底；否则 α 调大时价格永远跌不到
#: floor（例如 P=2、S=-1、α=5 会被截成 1.60，而不是 1.00），与定价用例冲突。
MAX_STEP_PCT = 0.20
#: 多少倍标准差记"满格信号"（S=±1）。
#: 不直接用 clamp(z, -1, 1)：那样 1σ 就满格，实测首轮 8/8 名选手全部 ±15%，
#: 价格几乎呈二值跳动；改成 3σ 满格后，1σ → S≈0.33 → 约 5%，曲线才有层次。
Z_FULL_SCALE = 3.0
#: 价格与涨跌幅保留的小数位
PRICE_DECIMALS = 2

@dataclass(frozen=True)
class PriceUpdate:
    """一次价格更新的结果，直接对应 price_history 表要存的内容。"""

    new_price: float
    change_pct: float
    reason: str  # 例："模拟比赛表现提升（S=+0.42）"
    old_price: float = 0.0
    signal: float = 0.0        # 实际生效的 S(t)
    step_pct: float = 0.0      # 实际生效的变动（已 clamp），百分数
    capped: bool = False       # 是否被 ±20% 上限截断
    floored: bool = False      # 是否触及价格下限

@lru_cache(maxsize=1)
def _settings():
    """尝试读取 B 的后端配置；独立运行/单元测试时允许不存在。"""
    try:
        from app.core.config import settings  # type: ignore
        return settings
    except Exception:  # noqa: BLE001 - 配置缺失不应让定价不可用
        return None
def _resolve(override: float | None, attr: str, fallback: float) -> float:
    """按"显式传参 > settings > 常量"的优先级解析参数。"""
    if override is not None:
        return float(override)
    settings = _settings()
    if settings is not None:
        value = getattr(settings, attr, None)
        if value is not None:
            return float(value)
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
        reason += f"，单次涨幅超过 +{MAX_STEP_PCT * 100:.0f}% 上限，已按上限执行"
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
        score_delta: 标准化表现信号 S(t)，建议先 clamp 到 [-1, 1]，
            否则一场比赛打出极端数据会把价格一次性拉爆。
        demand_signal: 需求信号 D(t)，初版传 0.0。
        alpha / beta / floor: 不传则用 settings 里的默认值。

    Returns:
        PriceUpdate(new_price, change_pct, reason)，四舍五入到 2 位小数。

    Raises:
        ValueError: current_price <= 0 或参数非法。

    待实现（C）：
    - 参数默认值从 `from app.core.config import settings` 读取；
    - reason 必须是给用户看的自然语言，答辩时要用它拆解"哪部分来自比赛表现"；
    - 单次变化幅度过大时要在文档里说明并给出 clamp 策略。
    """
    # ---------------- 入参校验 ----------------
    if current_price is None or not math.isfinite(float(current_price)) or current_price <= 0:
        raise ValueError(f"current_price 必须为正数，收到 {current_price!r}")
    if score_delta is None or not math.isfinite(float(score_delta)):
        raise ValueError(f"score_delta 必须是有限数值，收到 {score_delta!r}")
    if demand_signal is None or not math.isfinite(float(demand_signal)):
        raise ValueError(f"demand_signal 必须是有限数值，收到 {demand_signal!r}")
    alpha_value = _resolve(alpha, "pricing_alpha", DEFAULT_ALPHA)
    beta_value = _resolve(beta, "pricing_beta", DEFAULT_BETA)
    floor_value = _resolve(floor, "pricing_floor", DEFAULT_FLOOR)
    if alpha_value < 0 or beta_value < 0:
        raise ValueError(f"alpha / beta 不能为负，收到 alpha={alpha_value}, beta={beta_value}")
    if floor_value <= 0:
        raise ValueError(f"floor 必须为正数，收到 {floor_value}")
    # ---------------- 信号与变动幅度 ----------------
    signal = _clip(float(score_delta), -1.0, 1.0)
    demand = _clip(float(demand_signal), -1.0, 1.0)
    raw_step = alpha_value * signal + beta_value * demand
    capped = raw_step > MAX_STEP_PCT
    step = min(raw_step, MAX_STEP_PCT)  # 只封顶上涨，下跌交给 floor 兜底
    # ---------------- 价格与下限 ----------------
    new_price = round(float(current_price) * (1 + step), PRICE_DECIMALS)
    floored = new_price < floor_value
    if floored:
        new_price = round(floor_value, PRICE_DECIMALS)
    # 涨跌幅由"取整后的价格"反算，保证「价格 × (1+涨跌幅)」与展示自洽
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

def standardize_score(raw_score: float, history: list[float], window: int = 5) -> float:
    """把原始比赛得分转成标准化表现信号 S(t)。

    做法：用最近 window 局的均值和（总体）标准差做 z-score，
    除以 Z_FULL_SCALE（默认 3，即 3σ 记满格），再 clamp 到 [-1, 1]。
    - 历史不足 window 局时用已有数据（不去补 0，也不假装样本充足）；
    - 空历史返回 0.0（第 1 场比赛不产生价格变化，这是刻意的）；
    - 标准差为 0 时返回 0.0（避免除零，也避免"历史完全一样"时把信号放大）。
    Args:
        raw_score: 本场原始得分（0-100）。
        history: 历史得分序列（不含本场），按时间先后排列。
        window: 回看局数，默认 5。
    Returns:
        落在 [-1, 1] 的标准化信号。
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