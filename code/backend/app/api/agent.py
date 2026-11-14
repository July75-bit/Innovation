"""智能体增强接口（第 8 轮：把 AI 从"一张卡"变成"贯穿主流程的智能体"）。

负责人：B（接口与落库） / D（AI 口径） / A（展示）

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/agent/decision/{player_id}` | **决策卡**：6 字段建议 + 仓位/止损/置信度 + trace_id |
| GET | `/api/agent/brief` | **今日智能体简报**：3 条要点（缓存 10 分钟） |
| GET | `/api/agent/traces` | **审计**：最近的智能体调用记录（只读） |
| POST | `/api/agent/decisions` | **人在环**：采纳/忽略某条建议（写 decision_logs） |
| GET | `/api/agent/decisions/stats` | 采纳率统计 |
| GET | `/api/agent/panel/{player_id}` | **多角色协作**：分析师→风控→交易员纪要 |
| GET | `/api/agent/narrative/{player_id}` | **叙事归因**：把规则 reason 扩写成因果解释 |

**边界（与既有契约一致，不让步）**：
- 全部只读业务数据；唯一的写入是**审计表**（agent_traces / decision_logs / price_narratives），
  余额、持仓、流水、价格一律不动；
- 模型不可用一律 200 + `source=rule_fallback`（沿用 §4.10 硬规则）；
- `/api/analysis/{id}` 的 6 字段**原样不动**（金标集与三处测试锁着它）。
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from typing import Any, Literal

from ai.context import build_player_context, pct_change
from ai.decision import build_plan
from ai.llm_agent import analyze
from ai.narrate import is_big_move
from ai.panel import run_panel
from ai.tools import run_tool_loop
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import AgentTrace, DecisionLog, Player, Position, PriceHistory, PriceNarrative, User

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)

CENT = 0.01
BRIEF_TTL_SECONDS = 600

#: 简报缓存（进程内；免费实例重启后自然失效，可接受）
_brief_cache: dict[str, Any] = {"at": 0.0, "payload": None}


def _now() -> datetime:
    return datetime.now(UTC)


def _write_trace(
    db: Session,
    *,
    mode: str,
    player_id: int | None,
    source: str,
    model: str,
    latency_ms: int,
    output: dict[str, Any],
    fallback_reason: str | None = None,
    input_digest: str | None = None,
) -> int:
    """写一条审计行（best-effort：失败只记日志，绝不影响主响应）。"""
    if not settings.agent_traces_enabled:
        return 0
    try:
        row = AgentTrace(
            mode=mode,
            player_id=player_id,
            source=source,
            model=model or None,
            latency_ms=int(latency_ms),
            fallback_reason=fallback_reason,
            input_digest=(input_digest or "")[:120] or None,
            output_json=json.dumps(output, ensure_ascii=False)[:4000],
        )
        db.add(row)
        db.commit()
        return int(row.trace_id)
    except Exception as exc:  # noqa: BLE001 —— 审计失败不影响业务
        logger.warning("写入 agent_trace 失败：%s: %s", type(exc).__name__, exc)
        db.rollback()
        return 0


def _account_state(db: Session, user: User, player_id: int) -> tuple[float, int]:
    balance = float(user.balance or 0)
    held = db.scalar(
        select(Position.quantity).where(
            Position.user_id == user.user_id, Position.player_id == player_id
        )
    )
    return balance, int(held or 0)


def _safe_context(player: Player, db: Session) -> dict[str, Any]:
    try:
        return build_player_context(player.player_id, db=db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("agent 上下文失败，用最小上下文：%s: %s", type(exc).__name__, exc)
        return {
            "context_source": "minimal",
            "player_id": player.player_id,
            "name": player.name,
            "team": player.team or "",
            "role": player.role or "",
            "current_price": float(player.current_price or 0),
            "change_pct": float(pct_change(float(player.prev_price or 0), float(player.current_price or 0))),
            "rating": player.rating or 0,
            "recent_prices": [],
            "recent_reasons": [],
            "position": {"quantity": 0.0, "avg_cost": 0.0},
        }


# ---------------------------------------------------------------- 决策卡
@router.get("/decision/{player_id}", summary="智能体决策卡（建议 + 仓位 + 止损 + 置信度）")
def agent_decision(
    player_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    context = _safe_context(player, db)
    started = time.perf_counter()
    advice = analyze(context)
    latency_ms = int((time.perf_counter() - started) * 1000)

    balance, held = _account_state(db, user, player_id)
    plan_input = dict(advice)
    plan_input["_rating"] = context.get("rating")
    plan_input["_change_pct"] = context.get("change_pct")
    plan = build_plan(
        plan_input,
        balance=balance,
        current_price=float(player.current_price or 0),
        held_quantity=held,
        position_limit=settings.max_position_per_player,
    )

    trace_id = _write_trace(
        db,
        mode="decision",
        player_id=player_id,
        source=str(advice.get("source")),
        model=settings.llm_model,
        latency_ms=latency_ms,
        output={"advice": advice, "plan": plan},
        input_digest=f"player={player_id} price={player.current_price} held={held} balance={balance:.2f}",
    )

    return {
        "advice": advice,
        "plan": plan,
        "trace_id": trace_id,
        "snapshot": {
            "balance": round(balance, 2),
            "held_quantity": held,
            "current_price": float(player.current_price or 0),
            "change_pct": context.get("change_pct"),
            "rating": context.get("rating"),
        },
        "latency_ms": latency_ms,
        "disclaimer": "计划为启发式估算，下单必须由你本人确认；AI 不持有任何交易权限",
    }


# ---------------------------------------------------------------- 今日简报
def _round_halt_detail(players: list[Player], round_no: int | None) -> str:
    """本轮"停牌"说明：**由赛程派生**，不是看 `players.status`。

    两个概念的差别（2026-11-14 修，原先这里用错了字段）：
    - `players.status`：**手动冻结**（运维把某人长期停牌），现在是 16 人全 trading；
    - **本轮停牌**：赛程里这一轮有 2 支队伍在比赛 → 这 2 队共 4 人本轮不能交易，
      由 `core_engine.schedule.status_for()` 派生，每轮变化，不写库。

    所以简报若只看 `status`，就永远显示"无选手停牌"——与实际（每轮 4 人停牌）矛盾。
    """
    manual = [p.name for p in players if p.status != "trading"]
    manual_note = f"（另有手动冻结：{'、'.join(manual)}）" if manual else ""

    if round_no is None:
        return "今天不是比赛日，没有本轮停牌" + manual_note

    from core_engine.schedule import playing_teams, resolve_team_id, team_names

    from app.core.demo_schedule import DEMO_SCHEDULE

    try:
        team_ids = playing_teams(DEMO_SCHEDULE, round_no)
        names = team_names(DEMO_SCHEDULE)
        halted = [
            p.name for p in players if resolve_team_id(p.team or "", DEMO_SCHEDULE) in team_ids
        ]
        matchup = " vs ".join(names.get(t, f"#{t}") for t in sorted(team_ids))
    except Exception:  # noqa: BLE001 —— 赛程镜像异常不该影响简报
        return "赛程数据不可用，无法判断本轮停牌" + manual_note

    if not halted:
        return f"第 {round_no} 轮 {matchup} 比赛中，但没有选手匹配到这两支队伍" + manual_note
    return f"第 {round_no} 轮 {matchup} 比赛中，{len(halted)} 人停牌：{'、'.join(halted)}" + manual_note


def _clean_brief_summary(raw: str | None) -> str:
    """把模型输出清洗成「一句中文总述」（简报是给人看的，绝不能透出 JSON/字段名）。

    模型偶尔不听话，返回的是 `{"action": "HOLD", "reason": "..."}` 这类 JSON
    （甚至被截断成半个 JSON）。这里统一兜底：
    1. 去掉 markdown 代码围栏；
    2. 若是 JSON：优先取 reason / summary / text 字段（截断的 JSON 也能救）；
    3. 取不到就当纯文本，剥掉花括号、引号与常见字段名；
    4. 合并空白并限长 80 字（前端一行放得下），保留句末标点。
    """
    text = (raw or "").strip()
    if not text:
        return ""

    # 1) markdown 代码围栏（```json ... ```）
    text = re.sub(r"^```\w*\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    # 2) 模型返回 JSON：优先取人话字段
    if text.startswith("{"):
        match = re.search(r'"(?:reason|summary|text)"\s*:\s*"((?:[^"\\]|\\.)*)', text)
        if match:
            text = match.group(1).replace('\\"', '"').replace("\\n", " ")
        else:
            text = re.sub(r'[{}"]', "", text)
            text = re.sub(r"\b(action|risk_level|reason|summary|text)\s*[:：]\s*", "", text)

    # 3) 合并空白（保留句末标点，只去首尾空格）
    text = re.sub(r"\s+", " ", text).strip()
    return text[:80]


def _brief_items(db: Session) -> list[dict[str, Any]]:
    players = list(db.scalars(select(Player).order_by(Player.player_id)).all())
    if not players:
        return []
    changes = [(p, float(pct_change(float(p.prev_price or 0), float(p.current_price or 0)))) for p in players]
    hottest = max(changes, key=lambda x: abs(x[1]))
    cheapest = min(players, key=lambda p: float(p.current_price or 0))

    from core_engine.schedule import current_round

    from app.core.demo_schedule import DEMO_SCHEDULE

    round_no = current_round(DEMO_SCHEDULE)

    items = [
        {
            "title": "今日最该看一眼",
            "detail": f"{hottest[0].name}（{hottest[0].team}）变动 {hottest[1]:+.2f}%，现价 {float(hottest[0].current_price):.2f}",
            "player_id": hottest[0].player_id,
        },
        {
            "title": "低价区标的",
            "detail": f"{cheapest.name} 现价 {float(cheapest.current_price):.2f}，评分 {cheapest.rating}",
            "player_id": cheapest.player_id,
        },
        {
            # 标题点明口径：这是"本轮赛程停牌"，不是"手动冻结"
            "title": f"本轮停牌（第 {round_no} 轮）" if round_no else "本轮停牌",
            "detail": _round_halt_detail(players, round_no),
            "player_id": None,
        },
    ]
    return items


@router.get("/brief", summary="今日智能体简报（3 条要点，缓存 10 分钟）")
def agent_brief(
    db: Session = Depends(get_db), refresh: bool = Query(default=False, description="强制刷新缓存")
) -> dict:
    now = time.time()
    if not refresh and _brief_cache["payload"] and now - _brief_cache["at"] < BRIEF_TTL_SECONDS:
        return {**_brief_cache["payload"], "cached": True}

    items = _brief_items(db)
    started = time.perf_counter()
    summary, source = "", "rule_fallback"
    try:  # 让模型写一句总述；失败不影响三条要点
        from ai.llm_agent import _default_chat

        digest = "\n".join(f"- {i['title']}：{i['detail']}" for i in items)
        summary = _clean_brief_summary(
            _default_chat(
                "你是市场简报编辑。根据下面三条要点写一句不超过 40 字的中文总述，"
                "只输出这一句话本身（不要 JSON、不要字段名、不要代码块），"
                f"不要给投资建议、不要编造数据。\n{digest}",
                settings=settings,
            )
        )
        source = "llm" if summary else "rule_fallback"
    except Exception as exc:  # noqa: BLE001
        logger.info("简报总述回落规则版：%s: %s", type(exc).__name__, exc)
        summary = "今日行情由比赛表现驱动，请关注停牌与大幅波动标的。"
    latency_ms = int((time.perf_counter() - started) * 1000)

    payload = {
        "generated_at": _now().isoformat(timespec="seconds"),
        "ttl_seconds": BRIEF_TTL_SECONDS,
        "items": items,
        "summary": summary,
        "source": source,
        "latency_ms": latency_ms,
        "cached": False,
    }
    _brief_cache.update({"at": now, "payload": payload})
    _write_trace(
        db, mode="brief", player_id=None, source=source, model=settings.llm_model,
        latency_ms=latency_ms, output={"items": items, "summary": summary},
    )
    return payload


# ---------------------------------------------------------------- 审计查询
@router.get("/traces", summary="最近的智能体调用审计（只读）")
def agent_traces(
    db: Session = Depends(get_db), limit: int = Query(default=20, ge=1, le=100)
) -> dict:
    rows = list(
        db.scalars(select(AgentTrace).order_by(AgentTrace.created_at.desc()).limit(limit)).all()
    )
    return {
        "count": len(rows),
        "items": [
            {
                "trace_id": r.trace_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "mode": r.mode,
                "player_id": r.player_id,
                "source": r.source,
                "model": r.model,
                "latency_ms": r.latency_ms,
                "fallback_reason": r.fallback_reason,
            }
            for r in rows
        ],
        "提示": "只读审计；不含账户与连接串数据",
    }


# ---------------------------------------------------------------- 人在环
class DecisionRequest(BaseModel):
    player_id: int
    advice_action: Literal["BUY", "SELL", "HOLD"]
    advice_source: Literal["llm", "rule_fallback"]
    decision: Literal["accept", "ignore"]
    trace_id: int | None = None
    note: str | None = Field(default=None, max_length=200)


@router.post("/decisions", summary="记录对建议的采纳/忽略（人在环）")
def record_decision(
    body: DecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if db.get(Player, body.player_id) is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")
    row = DecisionLog(
        user_id=user.user_id,
        player_id=body.player_id,
        advice_action=body.advice_action,
        advice_source=body.advice_source,
        decision=body.decision,
        trace_id=body.trace_id,
        note=body.note,
    )
    db.add(row)
    db.commit()
    return {"success": True, "decision_id": row.decision_id, "message": "已记录你的选择"}


@router.get("/decisions/stats", summary="建议采纳率统计")
def decision_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    total = int(
        db.scalar(select(func.count()).select_from(DecisionLog).where(DecisionLog.user_id == user.user_id)) or 0
    )
    accepted = int(
        db.scalar(
            select(func.count())
            .select_from(DecisionLog)
            .where(DecisionLog.user_id == user.user_id, DecisionLog.decision == "accept")
        )
        or 0
    )
    return {
        "user_id": user.user_id,
        "total": total,
        "accepted": accepted,
        "accept_rate": round(accepted / total, 3) if total else None,
        "note": "采纳率只统计你本人；AI 从不自动下单，accept 仍需要你自己点买卖",
    }


# ---------------------------------------------------------------- 多角色协作
@router.get("/panel/{player_id}", summary="多角色协作纪要（分析师→风控→交易员）")
def agent_panel(player_id: int, db: Session = Depends(get_db)) -> dict:
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    context = _safe_context(player, db)
    started = time.perf_counter()
    result = run_panel(context, settings=settings)
    latency_ms = int((time.perf_counter() - started) * 1000)
    trace_id = _write_trace(
        db, mode="panel", player_id=player_id, source=result["source"],
        model=settings.llm_model, latency_ms=latency_ms,
        output={"final": result["final"], "minutes": result["minutes"]},
        fallback_reason=None if result["source"] == "llm" else "多角色协作不可用，整份回落规则版",
    )
    return {"player_id": player_id, "trace_id": trace_id, "latency_ms": latency_ms, **result}


# ---------------------------------------------------------------- 叙事归因
@router.get("/narrative/{player_id}", summary="价格变动的叙事归因（LLM，按点缓存）")
def agent_narrative(
    player_id: int,
    db: Session = Depends(get_db),
    refresh: bool = Query(default=False, description="忽略缓存重新生成"),
) -> dict:
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    rows = list(
        db.scalars(
            select(PriceHistory)
            .where(PriceHistory.player_id == player_id)
            .order_by(PriceHistory.ts.desc())
            .limit(4)
        ).all()
    )
    if not rows:
        return {"player_id": player_id, "narrative": "暂无价格历史", "source": "rule_fallback", "cached": False}

    latest = rows[0]
    prev_price = float(rows[1].price) if len(rows) > 1 else float(latest.price)
    change_pct = pct_change(prev_price, float(latest.price))

    cached = db.scalar(
        select(PriceNarrative).where(
            PriceNarrative.player_id == player_id, PriceNarrative.ts == latest.ts
        )
    )
    if cached and not refresh:
        return {
            "player_id": player_id,
            "ts": latest.ts.isoformat(),
            "narrative": cached.narrative,
            "source": cached.source,
            "change_pct": round(change_pct, 2),
            "big_move": is_big_move(change_pct),
            "cached": True,
        }

    from ai.narrate import generate_narrative

    points = [
        {"ts": r.ts.isoformat(), "price": float(r.price), "reason": r.reason}
        for r in reversed(rows)
    ]
    started = time.perf_counter()
    narrative, source, model = generate_narrative(
        name=player.name, team=player.team or "", points=points, settings=settings
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    try:
        if cached:
            cached.narrative, cached.source, cached.model = narrative, source, model
        else:
            db.add(
                PriceNarrative(
                    player_id=player_id, ts=latest.ts, narrative=narrative, source=source, model=model
                )
            )
        db.commit()
    except Exception as exc:  # noqa: BLE001 —— 缓存写失败不影响返回
        logger.warning("叙事缓存写入失败：%s: %s", type(exc).__name__, exc)
        db.rollback()

    _write_trace(
        db, mode="narrative", player_id=player_id, source=source, model=model,
        latency_ms=latency_ms, output={"narrative": narrative},
    )
    return {
        "player_id": player_id,
        "ts": latest.ts.isoformat(),
        "narrative": narrative,
        "source": source,
        "model": model,
        "change_pct": round(change_pct, 2),
        "big_move": is_big_move(change_pct),
        "cached": False,
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------- 工具调用演示
@router.get("/tools/{player_id}", summary="工具调用演示（模型自己决定查什么）")
def agent_tools(player_id: int, db: Session = Depends(get_db)) -> dict:
    """让模型通过三个只读工具自己取数；工具协议不支持时回落单次问答。"""
    player = db.get(Player, player_id)
    if player is None:
        raise ApiError("选手不存在", status_code=404, code="PLAYER_NOT_FOUND")

    def get_price_history(args: dict[str, Any]) -> Any:
        limit = min(int(args.get("limit") or 6), 12)
        rows = list(
            db.scalars(
                select(PriceHistory)
                .where(PriceHistory.player_id == int(args.get("player_id") or player_id))
                .order_by(PriceHistory.ts.desc())
                .limit(limit)
            ).all()
        )
        return [{"ts": r.ts.isoformat(), "price": float(r.price), "reason": r.reason} for r in reversed(rows)]

    def get_account_snapshot(args: dict[str, Any]) -> Any:
        demo = db.scalar(select(User).where(User.nickname == "demo"))
        balance, held = _account_state(db, demo, int(args.get("player_id") or player_id)) if demo else (0.0, 0)
        return {"balance": round(balance, 2), "held_quantity": held}

    def calc_position_size(args: dict[str, Any]) -> Any:
        risk = str(args.get("risk_level") or "MEDIUM").upper()
        ratio = {"LOW": 0.10, "MEDIUM": 0.06, "HIGH": 0.03}.get(risk, 0.06)
        balance = float(args.get("balance") or 0)
        price = float(args.get("price") or 0)
        if price <= 0:
            return {"error": "price 必须 > 0"}
        room = max(0, settings.max_position_per_player - int(args.get("held_quantity") or 0))
        qty = max(0, min(int(balance * ratio // price), room))
        return {"suggested_quantity": qty, "risk_level": risk, "budget_ratio": ratio}

    executors = {
        "get_price_history": get_price_history,
        "get_account_snapshot": get_account_snapshot,
        "calc_position_size": calc_position_size,
    }
    context = _safe_context(player, db)
    started = time.perf_counter()
    try:
        result = run_tool_loop(
            "你是只读分析助手。先用工具取数，再给出一句动作建议（BUY/SELL/HOLD），不要下单。",
            f"选手 {player.name}（{player.team}）现价 {player.current_price}，请自行调用工具核对后再回答。",
            executors,
            settings=settings,
        )
        source = "llm"
        latency_ms = int((time.perf_counter() - started) * 1000)
        payload = {
            "player_id": player_id,
            "answer": result["content"],
            "tool_calls": result["tool_calls"],
            "rounds": result["rounds"],
            "source": source,
            "latency_ms": latency_ms,
        }
    except Exception as exc:  # noqa: BLE001
        advice = analyze(context)
        payload = {
            "player_id": player_id,
            "answer": advice.get("reason"),
            "tool_calls": [],
            "rounds": 0,
            "source": "rule_fallback",
            "fallback_reason": f"{type(exc).__name__}: {exc}",
        }
        source = "rule_fallback"
    trace_id = _write_trace(
        db, mode="tools", player_id=player_id, source=source, model=settings.llm_model,
        latency_ms=int((time.perf_counter() - started) * 1000), output=payload,
    )
    return {**payload, "trace_id": trace_id}
