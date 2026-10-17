"""模拟比赛数据发生器。

负责人：C

用途：
1. 开发期没有真实赛事数据接口时的数据源（课程方案里"数据源抽象为适配器"的适配器之一）；
2. 现场演示要可复现 —— 必须支持固定随机种子，保证同一 seed 每次生成的比赛序列一样，
   否则答辩现场价格走势每次都不同，讲不清楚。

边界：这里只"造数据"，不改价格、不写库。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    """一场（或一局）模拟比赛的结果。"""

    player_id: int
    score: float  # 综合表现分（0-100）
    won: bool
    rating: str  # S / A / B / C
    note: str  # 人类可读说明，例如"三局两胜，场均得分最高"


def generate_match(player_id: int, *, seed: int | None = None) -> MatchResult:
    """生成一场模拟比赛结果。

    Args:
        player_id: 选手 ID。
        seed: 随机种子；演示时固定传同一个值以保证可复现。

    待实现（C）。
    """
    raise NotImplementedError("C 同学实现模拟赛数据发生器")


def generate_match_series(player_ids: list[int], rounds: int, *, seed: int | None = None) -> list[MatchResult]:
    """生成多轮比赛序列（rounds 轮 x 每个选手一场），用于铺满折线图的历史价格点。"""
    raise NotImplementedError("C 同学实现")


def to_demand_signal(net_buy_volume: float, total_volume: float) -> float:
    """把净买入量占比换算成需求信号 D(t)。

    待实现（C）：total_volume 为 0 时返回 0.0，避免除零。
    """
    raise NotImplementedError("C 同学实现")
