/**
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

export const DEMO_SCHEDULE = {
  schema_version: 1,
  season: 'demo-2026',
  generated_by: 'scripts/build_schedule.py',
  rules: {
    rounds: 28,
    matches_per_round: 1,
    teams_per_match: 2,
    suspended_players_per_round: 4,
    note: '每轮 1 场：参赛两队（每队 2 人）在该轮暂停交易，其余选手正常定价；圆桌法保证每 4 轮 8 队各出场 1 次，因此每人点数 = 2（种子点）+ 3k（k=轮数/4）',
  },
  teams: [
    { team_id: 1, name: 'Vitality' }, // 全季 7 场
    { team_id: 2, name: 'Spirit' }, // 全季 7 场
    { team_id: 3, name: 'Falcons' }, // 全季 7 场
    { team_id: 4, name: 'FaZe Clan' }, // 全季 7 场
    { team_id: 5, name: 'G2' }, // 全季 7 场
    { team_id: 6, name: 'NAVI' }, // 全季 7 场
    { team_id: 7, name: 'Astralis' }, // 全季 7 场
    { team_id: 8, name: 'The MongolZ' }, // 全季 7 场
  ],
  featured_round: 12,
  matches: [
    { round: 1, played_at: '2026-11-01', team_a: 1, team_b: 8 },
    { round: 2, played_at: '2026-11-02', team_a: 2, team_b: 7 },
    { round: 3, played_at: '2026-11-03', team_a: 3, team_b: 6 },
    { round: 4, played_at: '2026-11-04', team_a: 4, team_b: 5 },
    { round: 5, played_at: '2026-11-05', team_a: 1, team_b: 7 },
    { round: 6, played_at: '2026-11-06', team_a: 6, team_b: 8 },
    { round: 7, played_at: '2026-11-07', team_a: 2, team_b: 5 },
    { round: 8, played_at: '2026-11-08', team_a: 3, team_b: 4 },
    { round: 9, played_at: '2026-11-09', team_a: 3, team_b: 8 },
    { round: 10, played_at: '2026-11-10', team_a: 4, team_b: 7 },
    { round: 11, played_at: '2026-11-11', team_a: 5, team_b: 6 },
    { round: 12, played_at: '2026-11-12', team_a: 1, team_b: 2 },
    { round: 13, played_at: '2026-11-13', team_a: 1, team_b: 6 },
    { round: 14, played_at: '2026-11-14', team_a: 5, team_b: 7 },
    { round: 15, played_at: '2026-11-15', team_a: 4, team_b: 8 },
    { round: 16, played_at: '2026-11-16', team_a: 2, team_b: 3 },
    { round: 17, played_at: '2026-11-17', team_a: 1, team_b: 5 },
    { round: 18, played_at: '2026-11-18', team_a: 4, team_b: 6 },
    { round: 19, played_at: '2026-11-19', team_a: 3, team_b: 7 },
    { round: 20, played_at: '2026-11-20', team_a: 2, team_b: 8 },
    { round: 21, played_at: '2026-11-21', team_a: 1, team_b: 4 },
    { round: 22, played_at: '2026-11-22', team_a: 3, team_b: 5 },
    { round: 23, played_at: '2026-11-23', team_a: 2, team_b: 6 },
    { round: 24, played_at: '2026-11-24', team_a: 7, team_b: 8 },
    { round: 25, played_at: '2026-11-25', team_a: 1, team_b: 3 },
    { round: 26, played_at: '2026-11-26', team_a: 2, team_b: 4 },
    { round: 27, played_at: '2026-11-27', team_a: 5, team_b: 8 },
    { round: 28, played_at: '2026-11-28', team_a: 6, team_b: 7 },
  ],
}
