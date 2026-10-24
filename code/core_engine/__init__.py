"""core_engine：纯计算层（定价 + 模拟比赛数据）。

负责人：C

**为什么放在 `code/core_engine/` 而不是 `code/backend/`**
- 这一层只做"算"：输入比赛数据 → 输出新价格与原因，不依赖 FastAPI / SQLAlchemy，
  也不 import 任何 `app.*`（定价参数用 try/except 可选读 settings），
  所以后端、脚本、pytest、离线回测可以共用同一份代码；
- 反向依赖会出问题：若 core_engine 硬依赖 `app.core.config`，脚本与单测都会炸。

**怎么被引入**
- 后端：`code/backend/app/core/config.py` 已把 `<repo>/code` 插入 `sys.path`，
  所以 `from core_engine import update_price` 直接可用；
- 独立安装（可选）：`code/core_engine/pyproject.toml` 支持
  `pip install -e code/core_engine`，装完在任何地方都能 import。

**边界（必须守住）**
- 不写数据库：`price_history` 与 `players.current_price` 由 B 的 `app/api/prices.py` 落库；
- 不改余额/持仓：完全不碰 `users.balance` / `positions` / `trades`；
- 不调大模型：AI 建议属于 D 的 `app/ai`。

对外 API::

    from core_engine import update_price, standardize_score, generate_match_series

    s = standardize_score(92.0, [70.0, 72.0, 74.0])
    result = update_price(126.00, s)
    print(result.new_price, result.change_pct, result.reason)
"""

from .pricing import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    DEFAULT_FLOOR,
    MAX_STEP_PCT,
    Z_FULL_SCALE,
    PriceUpdate,
    standardize_score,
    update_price,
)
from .simulator import (
    MatchResult,
    generate_match,
    generate_match_series,
    to_demand_signal,
)

__all__ = [
    "update_price",
    "standardize_score",
    "PriceUpdate",
    "MAX_STEP_PCT",
    "Z_FULL_SCALE",
    "DEFAULT_ALPHA",
    "DEFAULT_BETA",
    "DEFAULT_FLOOR",
    "generate_match",
    "generate_match_series",
    "to_demand_signal",
    "MatchResult",
]
