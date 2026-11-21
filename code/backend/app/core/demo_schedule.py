"""赛程的**部署侧镜像**（与 `data/match_schedule.json` 同源）。

负责人：C ｜ **本文件由 `scripts/build_schedule.py` 自动生成，不要手改。**

为什么需要它：Render 后端的构建上下文是 `rootDir: code/backend`，容器里没有仓库根的
`data/` 目录；而 `POST /api/prices/recalc` 要在服务端判断"这一轮谁在比赛"，
所以必须把赛程打进后端包（配套的选手名单镜像是 `app/core/demo_roster.py`）。
"""

from __future__ import annotations

DEMO_SCHEDULE_SCHEMA_VERSION = 1
DEMO_SEASON = "demo-2026"
DEMO_FEATURED_ROUND = 12

#: (team_id, 队伍名)
DEMO_TEAMS: list[tuple[int, str]] = [
    (1, "Vitality"),
    (2, "Spirit"),
    (3, "Falcons"),
    (4, "FaZe Clan"),
    (5, "G2"),
    (6, "NAVI"),
    (7, "Astralis"),
    (8, "The MongolZ"),
]

#: (round, played_at, team_a, team_b)
DEMO_MATCHES: list[tuple[int, str, int, int]] = [
    (1, "2026-11-01", 1, 8),
    (2, "2026-11-02", 2, 7),
    (3, "2026-11-03", 3, 6),
    (4, "2026-11-04", 4, 5),
    (5, "2026-11-05", 1, 7),
    (6, "2026-11-06", 6, 8),
    (7, "2026-11-07", 2, 5),
    (8, "2026-11-08", 3, 4),
    (9, "2026-11-09", 3, 8),
    (10, "2026-11-10", 4, 7),
    (11, "2026-11-11", 5, 6),
    (12, "2026-11-12", 1, 2),
    (13, "2026-11-13", 1, 6),
    (14, "2026-11-14", 5, 7),
    (15, "2026-11-15", 4, 8),
    (16, "2026-11-16", 2, 3),
    (17, "2026-11-17", 1, 5),
    (18, "2026-11-18", 4, 6),
    (19, "2026-11-19", 3, 7),
    (20, "2026-11-20", 2, 8),
    (21, "2026-11-21", 1, 4),
    (22, "2026-11-22", 3, 5),
    (23, "2026-11-23", 2, 6),
    (24, "2026-11-24", 7, 8),
    (25, "2026-11-25", 1, 3),
    (26, "2026-11-26", 2, 4),
    (27, "2026-11-27", 5, 8),
    (28, "2026-11-28", 6, 7),
]

DEMO_SCHEDULE: dict = {
    "schema_version": DEMO_SCHEDULE_SCHEMA_VERSION,
    "season": DEMO_SEASON,
    "featured_round": DEMO_FEATURED_ROUND,
    "teams": [{"team_id": tid, "name": name} for tid, name in DEMO_TEAMS],
    "matches": [
        {"round": rnd, "played_at": day, "team_a": a, "team_b": b}
        for rnd, day, a, b in DEMO_MATCHES
    ],
}

__all__ = [
    "DEMO_FEATURED_ROUND",
    "DEMO_MATCHES",
    "DEMO_SCHEDULE",
    "DEMO_SCHEDULE_SCHEMA_VERSION",
    "DEMO_SEASON",
    "DEMO_TEAMS",
]
