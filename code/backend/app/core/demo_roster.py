"""第 6 天演示选手名单（16 名 / 8 队 / 每队 2 人）的**进程内副本**。

为什么复制一份而不直接读 `data/seed_players.json`：
Render 的构建上下文是 `rootDir: code/backend`（见 render.yaml），线上容器里**没有**
仓库根的 `data/` 目录；而重灌逻辑必须跑在容器内（它能走内网连 Postgres，公网直连
5432 常被校园/运营商网络掐断 TLS）。

**同步规则**：真正的数据源仍是 `data/seed_players.json`（schema_version 4，2026-11-07）；
本文件只是它的部署侧镜像。**任何选手名单/价格/星级改动，两个文件必须同一次提交同步改**，
并在 `data/seed_players.json` 的 `data_sources.说明` 里记录。
供 `app/api/debug.py` 的 `POST /api/debug/reseed` 使用（运维按钮，见其 docstring）。
"""

from __future__ import annotations

DEMO_SCHEMA_VERSION = 4

DEMO_DESCRIPTION = (
    "PlayerStock 固定演示数据（部署侧镜像）。选手身份为公开可查的真实 CS2 职业选手；"
    "价格与综合表现评分为本项目设定的模拟数据，不构成任何官方统计或投资建议。"
    "2026-11-07：扩至 16 名选手 / 8 队（每队 2 人），m0NESY 由 G2 转会 Falcons。"
)

DEMO_ROSTER: list[dict[str, str | int]] = [
    {
        "player_id": 1,
        "name": "ZywOo",
        "display_name": "ZywOo",
        "team": "Vitality",
        "role": "AWPer",
        "initial_price": "120.00",
        "current_price": "126.00",
        "rating": 88,
        "status": "trading",
    },
    {
        "player_id": 2,
        "name": "donk",
        "display_name": "donk",
        "team": "Spirit",
        "role": "Rifler",
        "initial_price": "140.00",
        "current_price": "143.50",
        "rating": 90,
        "status": "trading",
    },
    {
        "player_id": 3,
        "name": "m0NESY",
        "display_name": "m0NESY",
        "team": "Falcons",  # 2026-11-07 转会标注：G2 → Falcons
        "role": "AWPer",
        "initial_price": "96.00",
        "current_price": "91.20",
        "rating": 86,
        "status": "trading",
    },
    {
        "player_id": 4,
        "name": "NiKo",
        "display_name": "NiKo",
        "team": "Falcons",
        "role": "Rifler",
        "initial_price": "80.00",
        "current_price": "74.40",
        "rating": 80,
        "status": "trading",
    },
    {
        "player_id": 5,
        "name": "ropz",
        "display_name": "ropz",
        "team": "FaZe Clan",
        "role": "Lurker",
        "initial_price": "105.00",
        "current_price": "105.00",
        "rating": 78,
        "status": "trading",
    },
    {
        "player_id": 6,
        "name": "jL",
        "display_name": "jL",
        "team": "NAVI",
        "role": "Rifler",
        "initial_price": "88.00",
        "current_price": "90.20",
        "rating": 74,
        "status": "trading",
    },
    {
        "player_id": 7,
        "name": "sh1ro",
        "display_name": "sh1ro",
        "team": "Spirit",
        "role": "AWPer",
        "initial_price": "130.00",
        "current_price": "136.50",
        "rating": 85,
        "status": "suspended",  # 模拟比赛进行中，用于演示暂停交易规则
    },
    {
        "player_id": 8,
        "name": "flameZ",
        "display_name": "flameZ",
        "team": "Vitality",
        "role": "Rifler",
        "initial_price": "70.00",
        "current_price": "63.00",
        "rating": 66,
        "status": "trading",
    },
    {
        "player_id": 9,
        "name": "broky",
        "display_name": "broky",
        "team": "FaZe Clan",
        "role": "AWPer",
        "initial_price": "98.00",
        "current_price": "96.40",
        "rating": 79,
        "status": "trading",
    },
    {
        "player_id": 10,
        "name": "w0nderful",
        "display_name": "w0nderful",
        "team": "NAVI",
        "role": "AWPer",
        "initial_price": "92.00",
        "current_price": "88.30",
        "rating": 72,
        "status": "trading",
    },
    {
        "player_id": 11,
        "name": "huNter-",
        "display_name": "huNter-",
        "team": "G2",
        "role": "Rifler",
        "initial_price": "84.00",
        "current_price": "87.40",
        "rating": 71,
        "status": "trading",
    },
    {
        "player_id": 12,
        "name": "Snax",
        "display_name": "Snax",
        "team": "G2",
        "role": "Support",
        "initial_price": "65.00",
        "current_price": "61.80",
        "rating": 62,
        "status": "trading",
    },
    {
        "player_id": 13,
        "name": "device",
        "display_name": "device",
        "team": "Astralis",
        "role": "AWPer",
        "initial_price": "110.00",
        "current_price": "106.70",
        "rating": 82,
        "status": "trading",
    },
    {
        "player_id": 14,
        "name": "stavn",
        "display_name": "stavn",
        "team": "Astralis",
        "role": "Rifler",
        "initial_price": "82.00",
        "current_price": "79.60",
        "rating": 69,
        "status": "trading",
    },
    {
        "player_id": 15,
        "name": "910",
        "display_name": "910",
        "team": "The MongolZ",
        "role": "AWPer",
        "initial_price": "78.00",
        "current_price": "82.90",
        "rating": 77,
        "status": "trading",
    },
    {
        "player_id": 16,
        "name": "bLitz",
        "display_name": "bLitz",
        "team": "The MongolZ",
        "role": "IGL",
        "initial_price": "60.00",
        "current_price": "57.60",
        "rating": 64,
        "status": "trading",
    },
]
