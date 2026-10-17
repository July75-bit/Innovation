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


@dataclass(frozen=True)
class PriceUpdate:
    """一次价格更新的结果，直接对应 price_history 表要存的内容。"""

    new_price: float
    change_pct: float
    reason: str  # 例："模拟比赛表现提升（S=+0.42）"


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
    raise NotImplementedError("C 同学按 docs/algorithm/pricing_model.md 实现")


def standardize_score(raw_score: float, history: list[float], window: int = 5) -> float:
    """把原始比赛得分转成标准化表现信号 S(t)。

    待实现（C）：建议用最近 window 局的均值和标准差做 z-score，再 clamp 到 [-1, 1]；
    历史不足 window 局时用已有数据的均值，空历史返回 0.0。
    """
    raise NotImplementedError("C 同学实现标准化逻辑")
