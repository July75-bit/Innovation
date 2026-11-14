"""生成演示赛程 `data/match_schedule.json`（8 队 / 每轮 1 场 / 28 轮）。

负责人：C（第 7 天「暂停交易改为队伍级派生」）

为什么用固定赛程而不是随机抽签：
1. **可复现**：同一天同一轮永远是同一场比赛，演示/回测/截图都对得上；
2. **均衡**：圆桌法保证「每 4 轮里 8 支队各出场 1 次」→ 每人被暂停的轮次数完全一致，
   点数可直接用公式算（`2 + 3k`），不用随机数也不用事后统计；
3. **可解释**：真实赛程本来就是确定的，随机反而更假。

赛程结构：8 队单循环共 C(8,2)=28 场；每轮 1 场 → 28 轮。
任意 `4k` 轮的前缀，每队恰好出场 k 次。

用法（仓库根目录）：

    python scripts/build_schedule.py                # 写 data/match_schedule.json
    python scripts/build_schedule.py --check        # 只校验现有文件，不写
    python scripts/build_schedule.py --featured "Vitality vs Spirit" --featured-round 12
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

SEED_FILE = ROOT / "data" / "seed_players.json"
SCHEDULE_FILE = ROOT / "data" / "match_schedule.json"
BACKEND_MIRROR = ROOT / "code" / "backend" / "app" / "core" / "demo_schedule.py"
FRONTEND_MIRROR = ROOT / "code" / "frontend" / "src" / "data" / "demoSchedule.ts"
DEFAULT_START = date(2026, 11, 1)
MATCHES_PER_ROUND = 1
ROUNDS_PER_BLOCK = 4  # 8 队 / 每轮 2 队 = 4 轮覆盖全部队伍


def write_backend_mirror(payload: dict) -> None:
    """把赛程写成后端的部署侧镜像（Render 容器里没有仓库根的 data/）。"""
    teams = "\n".join(f'    ({t["team_id"]}, "{t["name"]}"),' for t in payload["teams"])
    matches = "\n".join(
        f'    ({m["round"]}, "{m["played_at"]}", {m["team_a"]}, {m["team_b"]}),'
        for m in payload["matches"]
    )
    source = f'''"""赛程的**部署侧镜像**（与 `data/match_schedule.json` 同源）。

负责人：C ｜ **本文件由 `scripts/build_schedule.py` 自动生成，不要手改。**

为什么需要它：Render 后端的构建上下文是 `rootDir: code/backend`，容器里没有仓库根的
`data/` 目录；而 `POST /api/prices/recalc` 要在服务端判断"这一轮谁在比赛"，
所以必须把赛程打进后端包（配套的选手名单镜像是 `app/core/demo_roster.py`）。
"""

from __future__ import annotations

DEMO_SCHEDULE_SCHEMA_VERSION = {payload["schema_version"]}
DEMO_SEASON = "{payload["season"]}"
DEMO_FEATURED_ROUND = {payload["featured_round"]}

#: (team_id, 队伍名)
DEMO_TEAMS: list[tuple[int, str]] = [
{teams}
]

#: (round, played_at, team_a, team_b)
DEMO_MATCHES: list[tuple[int, str, int, int]] = [
{matches}
]

DEMO_SCHEDULE: dict = {{
    "schema_version": DEMO_SCHEDULE_SCHEMA_VERSION,
    "season": DEMO_SEASON,
    "featured_round": DEMO_FEATURED_ROUND,
    "teams": [{{"team_id": tid, "name": name}} for tid, name in DEMO_TEAMS],
    "matches": [
        {{"round": rnd, "played_at": day, "team_a": a, "team_b": b}}
        for rnd, day, a, b in DEMO_MATCHES
    ],
}}

__all__ = [
    "DEMO_FEATURED_ROUND",
    "DEMO_MATCHES",
    "DEMO_SCHEDULE",
    "DEMO_SCHEDULE_SCHEMA_VERSION",
    "DEMO_SEASON",
    "DEMO_TEAMS",
]
'''
    BACKEND_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_MIRROR.write_text(source, encoding="utf-8")


def _ts_str(value: object) -> str:
    """Python 值 → TypeScript 字面量（镜像文件里只会出现 str / int / None，够用）。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


FRONTEND_HEADER = '''/**
 * 白话导读：赛程数据的**前端构建期镜像**（与 `data/match_schedule.json` 同源）。
 *
 * ⚠️ 本文件由 `scripts/build_schedule.py` 自动生成，不要手改：
 *    要改赛程就改生成脚本（圆桌法在 `round_robin()`），然后重跑
 *    `python scripts/build_schedule.py`（它会同时刷新后端镜像）。
 *
 * 为什么需要它：`/schedule`（赛程）页要现场演示"派生状态"这套算法
 * （`src/core/schedule.ts` 是 `code/core_engine/schedule.py` 的逐函数移植）。
 * 静态站部署后浏览器读不到仓库根的 `data/`，而后端没启动时赛程页也必须能演示，
 * 所以把赛程打进前端包里——与后端 `app/core/demo_schedule.py` 同一思路的第三份镜像。
 */

'''


def write_frontend_mirror(payload: dict) -> None:
    """把赛程写成前端镜像 `src/data/demoSchedule.ts`。

    输出刻意按 Prettier 口径排（单引号、对象键不加引号、一行一项），
    这样 `npm run format` 之后文件仍然和重新生成的一致，不会出现"生成→格式化"来回打架的 diff。
    """
    rules = "\n".join(f"    {key}: {_ts_str(value)}," for key, value in payload["rules"].items())
    appearances: dict[int, int] = {}
    for match in payload["matches"]:
        for team_id in (match["team_a"], match["team_b"]):
            appearances[team_id] = appearances.get(team_id, 0) + 1
    teams = "\n".join(
        f"    {{ team_id: {team['team_id']}, name: {_ts_str(team['name'])} }}, // 全季 {appearances[team['team_id']]} 场"
        for team in payload["teams"]
    )
    matches = "\n".join(
        f"    {{ round: {match['round']}, played_at: {_ts_str(match['played_at'])}, "
        f"team_a: {match['team_a']}, team_b: {match['team_b']} }},"
        for match in payload["matches"]
    )
    body = (
        "export const DEMO_SCHEDULE = {\n"
        f"  schema_version: {payload['schema_version']},\n"
        f"  season: {_ts_str(payload['season'])},\n"
        f"  generated_by: {_ts_str(payload['generated_by'])},\n"
        f"  rules: {{\n{rules}\n  }},\n"
        f"  teams: [\n{teams}\n  ],\n"
        f"  featured_round: {payload['featured_round'] if payload['featured_round'] is not None else 'null'},\n"
        f"  matches: [\n{matches}\n  ],\n"
        "}\n"
    )
    FRONTEND_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_MIRROR.write_text(FRONTEND_HEADER + body, encoding="utf-8", newline="\n")  # 头注释自带一个空行


def load_roster() -> tuple[list[dict], int]:
    """读队伍与「每队人数」；每队人数用于算「每轮暂停多少人」。"""
    payload = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    teams = payload.get("teams")
    players = payload.get("players") or []
    if not teams:
        raise SystemExit("种子文件缺少 teams[]：先升级 data/seed_players.json 到 schema v5")
    if len(teams) % 2:
        raise SystemExit(f"队伍数必须是偶数，当前 {len(teams)}")
    per_team = len(players) // len(teams) if players else 2
    return sorted(teams, key=lambda t: t["team_id"]), per_team


def round_robin(team_ids: list[int]) -> list[list[tuple[int, int]]]:
    """圆桌法：返回 n-1 组，每组 n/2 场，任意两组之间不重复、且每组覆盖全部队伍。"""
    ids = list(team_ids)
    n = len(ids)
    fixed, rest = ids[0], ids[1:]
    blocks: list[list[tuple[int, int]]] = []
    for _ in range(n - 1):
        pairs = [(fixed, rest[-1])] + [
            (rest[i], rest[-2 - i]) for i in range(n // 2 - 1)
        ]
        blocks.append([tuple(sorted(pair)) for pair in pairs])
        rest = [rest[-1]] + rest[:-1]
    return blocks


def order_blocks(
    blocks: list[list[tuple[int, int]]], featured: tuple[int, int] | None, featured_round: int
) -> list[list[tuple[int, int]]]:
    """把「焦点对局」所在的整组挪到 featured_round 所属的组，并让该对局落在最后一轮。

    整组挪动 + 组内换序都不破坏「每组覆盖全部队伍」的性质。
    """
    if featured is None:
        return blocks
    target_block = (featured_round - 1) // (len(blocks[0]))
    found = None
    for index, block in enumerate(blocks):
        if featured in block:
            found = index
            break
    if found is None:
        raise SystemExit(f"赛程里不存在这场比赛：{featured}")
    blocks = list(blocks)
    block = blocks.pop(found)
    block = [pair for pair in block if pair != featured] + [featured]
    blocks.insert(min(target_block, len(blocks)), block)
    return blocks


def build(
    teams: list[dict],
    start: date,
    featured: tuple[int, int] | None,
    featured_round: int,
    players_per_team: int = 2,
) -> dict:
    ids = [t["team_id"] for t in teams]
    blocks = order_blocks(round_robin(ids), featured, featured_round)
    matches = []
    round_no = 1
    for block in blocks:
        for team_a, team_b in block:
            matches.append(
                {
                    "round": round_no,
                    "played_at": (start + timedelta(days=round_no - 1)).isoformat(),
                    "team_a": team_a,
                    "team_b": team_b,
                }
            )
            round_no += 1
    return {
        "schema_version": 1,
        "season": "demo-2026",
        "generated_by": "scripts/build_schedule.py",
        "rules": {
            "rounds": len(matches),
            "matches_per_round": MATCHES_PER_ROUND,
            "teams_per_match": 2,
            "suspended_players_per_round": 2 * players_per_team,
            "note": (
                "每轮 1 场：参赛两队（每队 2 人）在该轮暂停交易，其余选手正常定价；"
                "圆桌法保证每 4 轮 8 队各出场 1 次，因此每人点数 = 2（种子点）+ 3k（k=轮数/4）"
            ),
        },
        "teams": [{"team_id": t["team_id"], "name": t["name"]} for t in teams],
        "featured_round": featured_round if featured else None,
        "matches": matches,
    }


def check(payload: dict) -> list[str]:
    """结构校验：轮次连续、每轮 2 支不同队伍、每 4 轮覆盖全部队伍、全场不重复。"""
    from core_engine.schedule import validate

    return validate(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成/校验演示赛程（8 队单循环）")
    parser.add_argument("--start", type=str, default=DEFAULT_START.isoformat(), help="首轮日期")
    parser.add_argument("--featured", type=str, default="Vitality vs Spirit", help="焦点对局（默认 Vitality vs Spirit），传空串则不指定")
    parser.add_argument("--featured-round", type=int, default=12, help="焦点对局落在第几轮（默认 12）")
    parser.add_argument("--check", action="store_true", help="只校验现有文件，不写")
    args = parser.parse_args()

    if args.check:
        payload = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        problems = check(payload)
        print("[check] 轮次:", payload["rules"]["rounds"])
        print("[check] ✅ 校验通过" if not problems else "\n".join("  - " + p for p in problems))
        return 1 if problems else 0

    teams, players_per_team = load_roster()
    name_to_id = {t["name"]: t["team_id"] for t in teams}
    featured = None
    if args.featured:
        left, _, right = args.featured.partition(" vs ")
        try:
            featured = tuple(sorted((name_to_id[left.strip()], name_to_id[right.strip()])))
        except KeyError as exc:
            raise SystemExit(f"焦点对局里有不认识的队伍：{exc}")

    payload = build(
        teams, date.fromisoformat(args.start), featured, args.featured_round, players_per_team
    )
    problems = check(payload)
    if problems:
        print("❌ 生成结果未通过校验：")
        for problem in problems:
            print("  -", problem)
        return 1

    SCHEDULE_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_backend_mirror(payload)
    write_frontend_mirror(payload)
    print(
        f"[build] 同步后端镜像 {BACKEND_MIRROR.relative_to(ROOT)}"
        f" + 前端镜像 {FRONTEND_MIRROR.relative_to(ROOT)}"
        f"（{len(payload['matches'])} 场）",
        flush=True,
    )

    rounds = payload["rules"]["rounds"]
    print(f"[build] 写入 {SCHEDULE_FILE.relative_to(ROOT)}：{rounds} 轮 / {len(teams)} 队")
    ids = {t["team_id"]: t["name"] for t in teams}
    counts = {t["name"]: 0 for t in teams}
    for match in payload["matches"][:12]:
        counts[ids[match["team_a"]]] += 1
        counts[ids[match["team_b"]]] += 1
    print("[build] 前 12 轮各队出场次数：", counts)
    if payload["featured_round"]:
        match = next(m for m in payload["matches"] if m["round"] == payload["featured_round"])
        print(
            f"[build] 第 {payload['featured_round']} 轮焦点局："
            f"{ids[match['team_a']]} vs {ids[match['team_b']]}（{match['played_at']}）"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
