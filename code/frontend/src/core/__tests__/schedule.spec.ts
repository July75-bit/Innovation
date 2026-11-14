/**
 * 赛程算法（src/core/schedule.ts）的回归测试——断言与 `tests/unit/test_schedule.py` 同口径，
 * 目的很直白：**前端移植不能和后端算出两个答案**。
 *
 * 守住六件事：
 * 1. 赛程结构：28 轮单循环、每轮 2 支不同队伍、每对只打一次；
 * 2. 均衡性：任意 4 轮一组覆盖全部 8 队 → 每人点数 = 2（种子点）+ 3k；
 * 3. 派生：队伍在比赛 → suspended，否则 trading；16 人里 4 暂停 / 12 可交易；
 * 4. 循环：第 29 轮等同第 1 轮；
 * 5. 生成：圆桌法在浏览器里重算一遍，必须与 checked-in 的赛程逐轮一致；
 * 6. 校验器：坏赛程能被 validate() 抓出来（含"自己打自己"与漏队）。
 */
import { describe, expect, it } from 'vitest'
import {
  DEFAULT_BLOCK,
  SEED_POINTS,
  SUSPENDED,
  TRADING,
  addDays,
  blockCoversAllTeams,
  blockIndexOf,
  blocksOf,
  buildSchedule,
  effectiveRound,
  expectedPoints,
  injectSelfMatch,
  matchLabel,
  matchOfTeam,
  matchesOfTeam,
  phaseOf,
  playingTeams,
  roundMatch,
  roundOfDate,
  roundRobin,
  rounds,
  schedule,
  statusFor,
  suspendedPlayers,
  suspensionReason,
  teamNames,
  teamPlaying,
  tradablePlayers,
  validate,
  weekdayCn,
  type SchedulePlayer,
} from '../schedule'

const names = teamNames()

/** 与 data/seed_players.json（schema v5）同形状：8 队 × 2 人，每人都有 team_id */
const roster: SchedulePlayer[] = [...names.entries()].flatMap(([id, name]) => [
  { player_id: id * 10 + 1, name: `${name} A`, team: name, team_id: id, status: TRADING },
  { player_id: id * 10 + 2, name: `${name} B`, team: name, team_id: id, status: TRADING },
])

describe('赛程结构', () => {
  it('28 轮，每轮两支不同的已知队伍', () => {
    expect(rounds()).toBe(28)
    for (const match of schedule.matches) {
      const sides = new Set([match.team_a, match.team_b])
      expect(sides.size).toBe(2)
      expect(names.has(Number(match.team_a))).toBe(true)
      expect(names.has(Number(match.team_b))).toBe(true)
    }
  })

  it('8 队单循环：28 场且对局不重复', () => {
    const pairs = schedule.matches.map((m) => [m.team_a, m.team_b].sort((x, y) => x - y).join('-'))
    expect(pairs).toHaveLength(28)
    expect(new Set(pairs).size).toBe(28)
  })

  it(`每 ${DEFAULT_BLOCK} 轮一组，组内覆盖全部 8 队`, () => {
    const groups = blocksOf(DEFAULT_BLOCK)
    expect(groups).toHaveLength(7)
    for (const group of groups) {
      expect(group).toHaveLength(DEFAULT_BLOCK)
      expect(blockCoversAllTeams(group)).toBe(true)
    }
  })

  it('比赛日按天推进，星期与日期对得上', () => {
    expect(schedule.matches[0]?.played_at).toBe('2026-11-01')
    expect(schedule.matches[27]?.played_at).toBe('2026-11-28')
    expect(addDays('2026-11-01', 27)).toBe('2026-11-28')
    expect(weekdayCn('2026-11-01')).toBe('周日')
    expect(blockIndexOf(12)).toBe(3)
  })

  it('焦点局固定在第 12 轮：Vitality vs Spirit', () => {
    expect(schedule.featured_round).toBe(12)
    expect([...playingTeams(12)].sort((a, b) => a - b)).toEqual([1, 2])
    expect(matchLabel(roundMatch(12))).toBe('Vitality vs Spirit')
  })
})

describe('状态派生（不入库，现算）', () => {
  it('第 12 轮：16 人里 4 人暂停、12 人可交易', () => {
    const suspended = suspendedPlayers(roster, 12)
    const tradable = tradablePlayers(roster, 12)
    expect(suspended).toHaveLength(4)
    expect(tradable).toHaveLength(12)
    expect(new Set(suspended.map((p) => p.team))).toEqual(new Set(['Vitality', 'Spirit']))

    for (const player of roster) {
      const expected = playingTeams(12).has(Number(player.team_id)) ? SUSPENDED : TRADING
      expect(statusFor(player, 12)).toBe(expected)
    }
  })

  it('暂停原因文案与后端同口径：「X vs Y 比赛中，暂停交易」', () => {
    const halted = suspendedPlayers(roster, 12)[0]
    expect(halted).toBeDefined()
    expect(suspensionReason(halted as SchedulePlayer, 12)).toBe(
      'Vitality vs Spirit 比赛中，暂停交易',
    )
    expect(suspensionReason(roster[10] as SchedulePlayer, 12)).toBeNull()
  })

  it('手动 status 优先于赛程（运维临时冻结仍然有效）', () => {
    const frozen: SchedulePlayer = { name: 'Frozen', team: 'NAVI', status: 'halted' }
    expect(suspensionReason(frozen, 12)).toBe('状态 halted（手动暂停）')
    // NAVI 第 12 轮没比赛，本该可交易；但手动冻结优先
    expect(statusFor(frozen, 12)).toBe(TRADING)
    expect(teamPlaying('NAVI', 12)).toBe(false)
    expect(teamPlaying('NAVI', 11)).toBe(true)
    expect(matchOfTeam('NAVI', 11)?.round).toBe(11)
    expect(matchOfTeam('NAVI', 12)).toBeNull()
  })

  it('只有队伍名也能反查 team_id；赛程外的队伍不会让整页崩掉', () => {
    expect(statusFor({ name: 'NoId', team: 'Spirit' }, 12)).toBe(SUSPENDED)
    expect(statusFor({ name: 'Unknown', team: 'NotExist' }, 12)).toBe(TRADING)
  })

  it('第 29 轮循环回落到第 1 轮', () => {
    expect(roundMatch(29)).toEqual(roundMatch(1))
    expect(effectiveRound(29)).toBe(1)
    expect([...playingTeams(29)]).toEqual([...playingTeams(1)])
    expect(effectiveRound(57)).toBe(1)
  })

  it('脏轮次直接报错，不静默算错', () => {
    expect(() => roundMatch(0)).toThrow(RangeError)
    expect(() => roundMatch(1.5)).toThrow(RangeError)
    expect(() => effectiveRound(-3)).toThrow(RangeError)
    expect(() => matchesOfTeam(1, -1)).toThrow(RangeError)
  })

  it('默认选中"今天所在的轮次"，阶段判定按比赛日比较', () => {
    expect(roundOfDate('2026-11-14')).toBe(14)
    expect(roundOfDate('2026-10-01')).toBe(1) // 开赛前 → 第 1 轮
    expect(roundOfDate('2026-12-01')).toBe(1) // 打完了 → 循环回落
    expect(phaseOf(roundMatch(14), '2026-11-14')).toBe('today')
    expect(phaseOf(roundMatch(13), '2026-11-14')).toBe('played')
    expect(phaseOf(roundMatch(15), '2026-11-14')).toBe('upcoming')
  })
})

describe('点数公式（均衡性直接决定可算性）', () => {
  it('第 12 轮：每队出场 3 次 → 2 + 3×3 = 11 点', () => {
    for (const id of names.keys()) {
      expect(matchesOfTeam(id, 12)).toBe(3)
      expect(expectedPoints(id, 12)).toBe(SEED_POINTS + 9)
    }
  })

  it('第 28 轮：每队出场 7 次 → 2 + 3×7 = 23 点', () => {
    for (const id of names.keys()) {
      expect(matchesOfTeam(id, 28)).toBe(7)
      expect(expectedPoints(id, 28)).toBe(SEED_POINTS + 21)
    }
    expect(expectedPoints(1, 28)).toBe(23)
  })

  it('非整组轮次也不出现"某队被多停一轮"', () => {
    for (let round = 1; round <= 28; round += 1) {
      const counts = [...names.keys()].map((id) => matchesOfTeam(id, round))
      expect(Math.max(...counts) - Math.min(...counts)).toBeLessThanOrEqual(1)
      // 每轮恰好 2 支队伍出场
      expect(counts.reduce((sum, value) => sum + value, 0)).toBe(round * 2)
    }
  })
})

describe('圆桌法：生成侧与 checked-in 赛程同源', () => {
  it('roundRobin(8 队) = 7 组 × 4 场，每组覆盖全部队伍', () => {
    const blocks = roundRobin([...names.keys()])
    expect(blocks).toHaveLength(7)
    for (const block of blocks) {
      expect(block).toHaveLength(DEFAULT_BLOCK)
      const ids = new Set(block.flatMap((pair) => pair as number[]))
      expect(ids.size).toBe(8)
    }
    const all = blocks.flat().map((pair) => pair.join('-'))
    expect(new Set(all).size).toBe(28)
  })

  it('浏览器里重算一遍，与仓库赛程逐轮一致（可复现）', () => {
    const built = buildSchedule(schedule.teams, {
      start: schedule.matches[0]?.played_at ?? '2026-11-01',
      featured: [1, 2],
      featuredRound: 12,
      playersPerTeam: 2,
    })
    expect(built.matches).toEqual(schedule.matches)
    expect(validate(built)).toEqual([])
  })

  it('焦点局被挪到第 3 组的最后一轮，且不破坏覆盖性', () => {
    const built = buildSchedule(schedule.teams, { featured: [1, 2], featuredRound: 12 })
    expect(built.matches[11]?.team_a).toBe(1)
    expect(built.matches[11]?.team_b).toBe(2)
    expect(blocksOf(DEFAULT_BLOCK, built).every((group) => blockCoversAllTeams(group, built))).toBe(
      true,
    )
  })

  it('不指定焦点局时 featured_round 为 null，且能被校验', () => {
    const plain = buildSchedule(schedule.teams)
    expect(plain.featured_round).toBeNull()
    expect(plain.matches).toHaveLength(28)
    expect(validate(plain)).toEqual([])
  })

  it('奇数队伍数直接报错（圆桌法要求偶数）', () => {
    expect(() => roundRobin([1, 2, 3])).toThrow(RangeError)
  })
})

describe('validate()：坏赛程必须被抓出来', () => {
  it('当前赛程零问题', () => {
    expect(validate()).toEqual([])
  })

  it('注入"自己打自己"后能检出', () => {
    const problems = validate(injectSelfMatch())
    expect(problems.some((p) => p.includes('打自己'))).toBe(true)
    // 原对象不被污染
    expect(validate()).toEqual([])
  })

  it('轮次不连续 / 对局重复 / 自己打自己 / 焦点局越界都能检出', () => {
    const broken = structuredClone(schedule)
    const second = broken.matches[1]
    if (second) second.round = 9
    expect(validate(broken).some((p) => p.includes('round 字段不连续'))).toBe(true)

    const dup = structuredClone(schedule)
    const first = dup.matches[0]
    const third = dup.matches[2]
    if (first && third) dup.matches[2] = { ...first }
    expect(validate(dup).some((p) => p.includes('重复对局'))).toBe(true)

    const gap = structuredClone(schedule)
    const head = gap.matches[0]
    if (head) head.team_b = head.team_a
    expect(validate(gap).some((p) => p.includes('打自己'))).toBe(true)

    const unknown = structuredClone(schedule)
    unknown.featured_round = 99
    expect(validate(unknown)).toContain('featured_round=99 超出 1–28')

    expect(validate({ ...schedule, matches: [] })).toEqual(['matches 为空'])
  })

  it('队数与组容量不匹配时报错（只剩 6 队，但每 4 轮要 8 个出场名额）', () => {
    const thin = { ...schedule, teams: schedule.teams.slice(0, 6) }
    expect(validate(thin).some((problem) => problem.includes('出场名额'))).toBe(true)
  })
})
