"""AI 分析接口（B 提供路由外壳，业务逻辑在 code/backend/ai/）。

负责人：B（路由/错误处理） + D（业务接线） + A（展示）

实现（第 3 天由 D 接入，路由外壳/错误格式仍归 B，改动见 commit 说明）：
- `GET /api/analysis/{player_id}` → `ai.context.build_player_context()` 组装上下文，
  `ai.llm_agent.analyze()` 出建议；无密钥/超时/脏输出由 analyze 内部回落规则版。

输出契约（docs/software/api_contract.md §4.10，固定 6 字段，前端按这个渲染）：
    {
      "player_id": 1,
      "action": "BUY",              # 只能是 BUY / SELL / HOLD
      "reason": "近 3 场表现评分持续上升，且价格尚未完全反映",
      "risk_level": "MEDIUM",       # LOW / MEDIUM / HIGH
      "source": "llm",              # llm / rule_fallback
      "disclaimer": "仅为分析建议，不构成投资建议；AI 不会自动交易"
    }

- **不输出 `suggested_price_band`**：契约里该字段可缺省，LLM 版与规则版字段集合保持一致，
  规则版不编造价格区间（2026-10-23 决策）。
- 成功时返回**裸对象**（无 `success` 字段）；失败时是 §2 统一错误体。

硬约束（三份材料都强调）：
1. API 密钥只在后端读取（settings.llm_api_key），绝不下发前端；
2. AI 只提供建议，**不直接修改余额或执行交易**：本路由只做 SELECT，
   不得 commit、不得 INSERT/UPDATE/DELETE，也不注入交易服务；
3. 模型超时 / 返回非法 JSON / 无密钥时，必须回落到 `ai/fallback.py` 的规则版，
   返回合法结构（source="rule_fallback"），**一律 200**，交易、定价、行情不受影响；
4. 单次调用有超时（settings.llm_timeout_seconds，由 analyze 使用），不能让前端挂死；
5. 只有「选手不存在」→ 404 `PLAYER_NOT_FOUND` 与「非 AI 故障」→ 500 才用非 200；
   AI 相关故障永远不得用 4xx/5xx 表达（契约 §4.10 硬规则）。
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.context import build_player_context
from ai.llm_agent import analyze
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Player

router = APIRouter(prefix="/analysis", tags=["ai"])


class AnalysisAdvice(BaseModel):
    """契约 §4.10 的固定 6 字段（`suggested_price_band` 本期不输出）。"""

    player_id: int
    action: Literal["BUY", "SELL", "HOLD"]
    reason: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    source: Literal["llm", "rule_fallback"]
    disclaimer: str


def _pct(prev_price: float, current_price: float) -> float:
    if not prev_price:
        return 0.0
    return round((current_price - prev_price) / prev_price * 100.0, 2)


def _minimal_context(player: Player) -> dict:
    """上下文组装彻底失败（连 seed 都读不到）时的最小上下文。

    规则版对缺字段有防御（`fallback.rule_based_advice`），所以这里只要给够
    能算出一条建议的字段即可，**仍然 200**，不把 AI 故障升级成 5xx。
    """
    prev_price = float(player.prev_price or 0)
    current_price = float(player.current_price or 0)
    return {
        "context_source": "minimal",
        "player_id": player.player_id,
        "name": player.name,
        "display_name": player.display_name or "",
        "team": player.team or "",
        "role": player.role or "",
        "current_price": current_price,
        "change_pct": _pct(prev_price, current_price),
        "rating": player.rating or 0,
        "recent_prices": [],
        "recent_reasons": [],
        "position": {"quantity": 0.0, "avg_cost": 0.0},
    }


@router.get(
    "/{player_id}",
    response_model=AnalysisAdvice,
    summary="AI 分析建议（模型不可用时自动降级为规则版）",
)
def get_analysis(player_id: int, db: Session = Depends(get_db)) -> AnalysisAdvice:
    """返回某位选手的 AI 建议；AI 故障一律 200 + `source=rule_fallback`。

    只读：查选手 → 拼上下文 → `analyze()`（内部若调模型也带 20s 超时）→ 返回。
    全程不做任何数据库写入，调用前后余额/持仓必须完全不变（契约 TC-205）。
    """
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    try:
        # 传入同一个只读会话：不另开连接，测试里的 get_db 依赖覆盖也能生效
        context = build_player_context(player_id, db=db)
    except Exception:  # 上下文组装失败属于 AI 侧故障 → 用最小上下文继续走规则版
        context = _minimal_context(player)

    advice = analyze(context)
    advice["player_id"] = player_id  # 以请求路径为准，防止上下文/模型回填错 id
    return AnalysisAdvice(**advice)
