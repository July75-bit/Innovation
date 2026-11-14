/**
 * 白话导读：赛程算法的前端镜像——把 `code/core_engine/schedule.py` 逐函数移植成 TypeScript，
 * 让"这一轮谁在比赛 / 谁暂停交易 / 该有多少点数"在浏览器里也算得出来，而不是只存在于后端。
 *
 * 三条核心设计（与原 Python 注释同口径）：
 * 1. **状态是派生值，不是存储值**：第 N 轮能不能交易由 `statusFor(player, N, schedule)` 现算。
 *    不需要每轮改数据库，页面也不用等后端推状态。
 * 2. **每轮一场比赛**：参赛两队（每队 2 人）在该轮整队暂停交易，其余选手正常定价。
 * 3. **超长轮次循环**：`roundNo` 超出赛程长度时按 `(roundNo - 1) % 轮数` 回到开头，
 *    回测跑到 30/32 轮也有确定对手，不会"没人比赛"。
 *
 * 数据来源：`src/data/demoSchedule.ts`（`scripts/build_schedule.py` 生成的前端镜像），
 * 与 `data/match_schedule.json`、后端 `app/core/demo_schedule.py` 同源——
 * 所以 `/schedule` 页看到的暂停结论，和后端 `POST /api/prices/recalc` 真正生效的规则是同一套。
 *
 * 对应关系：`rounds` / `teamNames` / `roundMatch` / `playingTeams` / `statusFor` /
 * `tradablePlayers` / `suspendedPlayers` / `matchOfTeam` / `teamPlaying` / `suspensionReason` /
 * `matchesOfTeam` / `expectedPoints` / `validate` 一一对应 Python 同名函数；
 * `roundRobin` / `orderBlocks` / `buildSchedule` 对应 `scripts/build_schedule.py`（圆桌法）。
 */

import { DEMO_SCHEDULE } from '../data/demoSchedule'

/** 赛程里的一支队伍（`teams[]` 的一项） */
export interface ScheduleTeam {
  team_id: number
  name: string
}

/** 一轮的比赛（每轮 1 场） */
export interface ScheduleMatch {
  round: number
  /** ISO 日期，如 2026-11-01 */
  played_at: string
  team_a: number
  team_b: number
}

/** `data/match_schedule.json` 的形状（schema v1） */
export interface Schedule {
  schema_version: number
  season?: string
  generated_by?: string
  rules?: Record<string, number | string>
  featured_round: number | null
  teams: ScheduleTeam[]
  matches: ScheduleMatch[]
}

/**
 * 判定只需的最小选手形状：后端 `PlayerSummary` 天然满足（有 team / status）。
 * `team_id` 可选——老数据只有队伍名，走 `teamIdOf()` 的名字反查兜底（与 Python `_team_id` 一致）。
 */
export interface SchedulePlayer {
  player_id?: number
  name?: string
  display_name?: string | null
  team?: string | null
  team_id?: number | null
  status?: string | null
}

/** 一对队伍（已按 team_id 升序），圆桌法的最小单位 */
export type Pair = [number, number]

export const SUSPENDED = 'suspended'
export const TRADING = 'trading'

/** 每 4 轮 = 一个"全部队伍各出场一次"的组（8 队 / 每轮 2 队） */
export const DEFAULT_BLOCK = 4
/** 种子点：初始价格 + 行情初始化各计 1 点 */
export const SEED_POINTS = 2

/** 演示赛程（构建期常量，页面所有结论都从它派生） */
export const schedule: Schedule = DEMO_SCHEDULE

/* ---------------------------------------------------------------- 小工具 */

/**
 * 越界就抛错而不是返回 undefined：`noUncheckedIndexedAccess` 开着，
 * 赛程是"必须完整"的数据，缺项属于脏数据，静默兜底会把 bug 变成错答案。
 */
function at<T>(items: readonly T[], index: number, what = '赛程项'): T {
  const value = items[index]
  if (value === undefined) {
    throw new RangeError(`${what}越界：索引 ${index}，长度 ${items.length}`)
  }
  return value
}

/* ---------------------------------------------------------------- 基础查询 */

/** 赛程总轮数 */
export function rounds(sched: Schedule = schedule): number {
  return sched.matches.length
}

/** team_id → 队伍名 */
export function teamNames(sched: Schedule = schedule): Map<number, string> {
  const map = new Map<number, string>()
  for (const team of sched.teams) map.set(Number(team.team_id), team.name)
  return map
}

/** 队伍名 → team_id（兼容只有 `team` 字符串的旧数据） */
export function teamIdsByName(sched: Schedule = schedule): Map<string, number> {
  const map = new Map<string, number>()
  for (const [id, name] of teamNames(sched)) map.set(name, id)
  return map
}

/** 第几组（每组 DEFAULT_BLOCK 轮，组内 8 队各出场 1 次），从 1 开始 */
export function blockIndexOf(roundNo: number, block: number = DEFAULT_BLOCK): number {
  return Math.floor((roundNo - 1) / block) + 1
}

/**
 * 第 roundNo 轮的那场比赛；超过赛程长度时循环。
 * `roundNo` 必须是 >= 1 的整数，否则抛错（把脏数据挡在门口，而不是静默算错）。
 */
export function roundMatch(roundNo: number, sched: Schedule = schedule): ScheduleMatch {
  return at(sched.matches, validIndex(roundNo, sched), '比赛')
}

/** 校验轮次并返回数组下标（0 基） */
function validIndex(roundNo: number, sched: Schedule): number {
  if (!Number.isInteger(roundNo) || roundNo < 1) {
    throw new RangeError(`roundNo 必须是 >= 1 的整数，收到 ${String(roundNo)}`)
  }
  if (!sched.matches.length) throw new RangeError('赛程里没有比赛')
  return (roundNo - 1) % sched.matches.length
}

/** 循环回落到赛程内的第几轮（UI 用它标注"第 29 轮 = 第 1 轮"） */
export function effectiveRound(roundNo: number, sched: Schedule = schedule): number {
  return validIndex(roundNo, sched) + 1
}

/** 这一轮正在比赛的两支队伍（它们整队暂停交易） */
export function playingTeams(roundNo: number, sched: Schedule = schedule): Set<number> {
  const match = roundMatch(roundNo, sched)
  return new Set([Number(match.team_a), Number(match.team_b)])
}

/** 选手 → team_id：优先用 team_id，没有就按队伍名反查 */
export function teamIdOf(player: SchedulePlayer, sched: Schedule = schedule): number {
  if (player.team_id !== null && player.team_id !== undefined) return Number(player.team_id)
  const team = player.team
  if (team === null || team === undefined) {
    throw new RangeError(`选手 ${player.name ?? '?'} 没有队伍信息`)
  }
  const id = teamIdsByName(sched).get(team)
  if (id === undefined) {
    throw new RangeError(`选手 ${player.name ?? '?'} 的队伍 ${team} 不在赛程里`)
  }
  return id
}

/* ---------------------------------------------------------------- 状态派生 */

/** 第 roundNo 轮这名选手的状态：队伍在比赛 → suspended，否则 trading */
export function statusFor(
  player: SchedulePlayer,
  roundNo: number,
  sched: Schedule = schedule,
): typeof SUSPENDED | typeof TRADING {
  let id: number
  try {
    id = teamIdOf(player, sched)
  } catch {
    // 认不出队伍（例如本地 mock 名单里有赛程外的队）时不打断整页渲染，按可交易处理
    return TRADING
  }
  return playingTeams(roundNo, sched).has(id) ? SUSPENDED : TRADING
}

/** 当轮可交易的选手 */
export function tradablePlayers(
  players: readonly SchedulePlayer[],
  roundNo: number,
  sched: Schedule = schedule,
): SchedulePlayer[] {
  return players.filter((player) => statusFor(player, roundNo, sched) === TRADING)
}

/** 当轮被暂停的选手 */
export function suspendedPlayers(
  players: readonly SchedulePlayer[],
  roundNo: number,
  sched: Schedule = schedule,
): SchedulePlayer[] {
  return players.filter((player) => statusFor(player, roundNo, sched) === SUSPENDED)
}

/** 队伍编号或队伍名 → team_id（`resolve_team_id`） */
export function resolveTeamId(team: number | string, sched: Schedule = schedule): number {
  if (typeof team === 'number') return team
  if (team !== '' && /^\d+$/.test(team)) return Number(team)
  const id = teamIdsByName(sched).get(team)
  if (id === undefined) throw new RangeError(`队伍 ${team} 不在赛程里`)
  return id
}

/** 这名选手所在队伍这一轮的比赛（不比赛返回 null） */
export function matchOfTeam(
  team: number | string,
  roundNo: number,
  sched: Schedule = schedule,
): ScheduleMatch | null {
  const id = resolveTeamId(team, sched)
  const match = roundMatch(roundNo, sched)
  return id === Number(match.team_a) || id === Number(match.team_b) ? match : null
}

/** 队伍这一轮是否在比赛（= 整队暂停交易） */
export function teamPlaying(
  team: number | string,
  roundNo: number,
  sched: Schedule = schedule,
): boolean {
  return matchOfTeam(team, roundNo, sched) !== null
}

/**
 * 这一轮为什么不能交易；可交易返回 null。两类来源，**手动 status 优先**（运维临时冻结仍然有效）：
 * 1. `player.status !== 'trading'` → "状态 X（手动暂停）"；
 * 2. 队伍这一轮有比赛 → "Vitality vs Spirit 比赛中，暂停交易"。
 * 文案与后端 `suspension_reason()` 一字不差，页面上看到的原因就是结算时真正生效的原因。
 */
export function suspensionReason(
  player: SchedulePlayer,
  roundNo: number,
  sched: Schedule = schedule,
): string | null {
  const status = String(player.status ?? TRADING)
  if (status !== TRADING) return `状态 ${status}（手动暂停）`

  const team = player.team_id ?? player.team
  if (team === null || team === undefined) return null

  let match: ScheduleMatch | null
  try {
    match = matchOfTeam(team, roundNo, sched)
  } catch {
    return null
  }
  if (match === null) return null

  const names = teamNames(sched)
  const id = resolveTeamId(team, sched)
  const opponent = Number(match.team_a) === id ? Number(match.team_b) : Number(match.team_a)
  return `${names.get(id) ?? id} vs ${names.get(opponent) ?? opponent} 比赛中，暂停交易`
}

/* ---------------------------------------------------------- 轮次统计与点数 */

/** 这支队伍在前 totalRounds 轮里打了几场（= 被暂停几轮） */
export function matchesOfTeam(
  teamId: number,
  totalRounds: number,
  sched: Schedule = schedule,
): number {
  if (!Number.isInteger(totalRounds) || totalRounds < 0) {
    throw new RangeError(`totalRounds 不能为负，收到 ${String(totalRounds)}`)
  }
  let count = 0
  for (let round = 1; round <= totalRounds; round += 1) {
    if (playingTeams(round, sched).has(teamId)) count += 1
  }
  return count
}

/**
 * 这支队伍的选手在 totalRounds 轮后应有的价格点数 = 种子点（默认 2）+ 可交易轮次数。
 * 因为圆桌法保证"每 4 轮各队恰好出场 1 次"，所以 4k 轮时它等于 `2 + 3k`，可以直接口算验收。
 */
export function expectedPoints(
  teamId: number,
  totalRounds: number,
  opts: { seedPoints?: number; sched?: Schedule } = {},
): number {
  const seedPoints = opts.seedPoints ?? SEED_POINTS
  const sched = opts.sched ?? schedule
  return seedPoints + totalRounds - matchesOfTeam(teamId, totalRounds, sched)
}

/** 按 block（默认 4 轮）把赛程切成组，UI 用它画"每 4 轮覆盖全部队伍"的块 */
export function blocksOf(
  block: number = DEFAULT_BLOCK,
  sched: Schedule = schedule,
): ScheduleMatch[][] {
  const groups: ScheduleMatch[][] = []
  for (let start = 0; start < sched.matches.length; start += block) {
    groups.push(sched.matches.slice(start, start + block))
  }
  return groups
}

/** 某一组里各队伍的出场人次（用来验证"每组每队恰好 1 次"） */
export function appearancesInBlock(matches: readonly ScheduleMatch[]): Map<number, number> {
  const counts = new Map<number, number>()
  for (const match of matches) {
    counts.set(Number(match.team_a), (counts.get(Number(match.team_a)) ?? 0) + 1)
    counts.set(Number(match.team_b), (counts.get(Number(match.team_b)) ?? 0) + 1)
  }
  return counts
}

/** 这一组是否覆盖了全部队伍（UI 用来给每组打勾） */
export function blockCoversAllTeams(
  matches: readonly ScheduleMatch[],
  sched: Schedule = schedule,
): boolean {
  const known = teamNames(sched)
  if (!known.size) return false
  for (const id of known.keys()) {
    if (!appearancesInBlock(matches).has(id)) return false
  }
  return true
}

/* ---------------------------------------------------------------- 结构校验 */

function pairKey(a: number, b: number): string {
  return a <= b ? `${a}-${b}` : `${b}-${a}`
}

/** 逐轮检查：轮次连续、两队不相同、队伍已知、对局不重复 */
export function checkRounds(matches: readonly ScheduleMatch[], known: Set<number>): string[] {
  const problems: string[] = []
  const seen = new Set<string>()
  matches.forEach((match, index) => {
    const round = index + 1
    if (Number(match.round) !== round) {
      problems.push(`第 ${round} 条的 round 字段不连续：${String(match.round)}`)
    }
    const home = Number(match.team_a)
    const away = Number(match.team_b)
    if (home === away) {
      problems.push(`第 ${round} 轮同一支队打自己：${home}, ${away}`)
    } else if (known.size && !(known.has(home) && known.has(away))) {
      problems.push(`第 ${round} 轮出现未知队伍：${home}, ${away}`)
    }
    const key = pairKey(home, away)
    if (seen.has(key)) problems.push(`重复对局：${key}`)
    seen.add(key)
  })
  return problems
}

/** 每 block 轮应覆盖全部队伍一次（不足一组的部分不检查） */
export function checkBlocks(
  matches: readonly ScheduleMatch[],
  known: Set<number>,
  block: number = DEFAULT_BLOCK,
): string[] {
  const total = matches.length
  if (!known.size || total % block !== 0) return []
  if (2 * block !== known.size) {
    return [`每 ${block} 轮只有 ${2 * block} 个出场名额，与 ${known.size} 支队不匹配`]
  }

  const problems: string[] = []
  for (let start = 0; start < total; start += block) {
    const appeared = new Set<number>()
    for (const match of matches.slice(start, start + block)) {
      appeared.add(Number(match.team_a))
      appeared.add(Number(match.team_b))
    }
    const missing = [...known].filter((id) => !appeared.has(id)).sort((a, b) => a - b)
    if (missing.length) {
      problems.push(`第 ${start + 1}–${start + block} 轮没有覆盖全部队伍：缺 ${missing.join(', ')}`)
    }
  }
  return problems
}

/** 结构校验；返回问题列表（空数组表示通过）。默认校验演示赛程。 */
export function validate(sched: Schedule = schedule, block: number = DEFAULT_BLOCK): string[] {
  const matches = sched.matches
  if (!matches.length) return ['matches 为空']

  const known = new Set(teamNames(sched).keys())
  const problems: string[] = known.size ? [] : ['缺少 teams[]，无法校验队伍编号']
  problems.push(...checkRounds(matches, known))
  problems.push(...checkBlocks(matches, known, block))

  const featured = sched.featured_round
  if (featured !== null && featured !== undefined) {
    if (!(Number(featured) >= 1 && Number(featured) <= matches.length)) {
      problems.push(`featured_round=${String(featured)} 超出 1–${matches.length}`)
    }
  }
  return problems
}

/**
 * 校验器的"错误注入"演示：在**副本**上把第 1 轮的客队改成同一支队（自己打自己）。
 * 用来在界面上证明 validate() 真的会报错，而绝不污染页面正在用的赛程。
 */
export function injectSelfMatch(sched: Schedule = schedule): Schedule {
  const copy: Schedule = structuredClone(sched)
  const first = copy.matches[0]
  if (first) first.team_b = first.team_a
  return copy
}

/* ---------------------------------------------- 生成侧：圆桌法（build_schedule.py） */

/**
 * 圆桌法：返回 n-1 组，每组 n/2 场，任意两组之间不重复、且每组覆盖全部队伍。
 * 逐行对应 Python 实现：1 号位固定，其余每轮顺时针轮转一位（`rest = [rest[-1], *rest[:-1]]`）。
 */
export function roundRobin(teamIds: readonly number[]): Pair[][] {
  const n = teamIds.length
  if (n === 0 || n % 2 !== 0) {
    throw new RangeError(`队伍数必须是偶数，当前 ${n}`)
  }
  const fixed = at(teamIds, 0, '队伍编号')
  let rest = teamIds.slice(1)
  const blocks: Pair[][] = []
  for (let round = 0; round < n - 1; round += 1) {
    const last = rest.length - 1
    const pairs: Pair[] = [[fixed, at(rest, last, '轮转位')]]
    for (let k = 0; k < Math.floor(n / 2) - 1; k += 1) {
      pairs.push([at(rest, k, '轮转位'), at(rest, last - 1 - k, '轮转位')])
    }
    blocks.push(pairs.map(([a, b]) => (a <= b ? [a, b] : [b, a])))
    rest = [at(rest, last, '轮转位'), ...rest.slice(0, last)]
  }
  return blocks
}

/**
 * 把「焦点对局」所在的整组挪到 featuredRound 所属的组，并让该对局落在这一组的最后一轮。
 * 整组挪动 + 组内换序都不破坏"每组覆盖全部队伍"的性质。
 */
export function orderBlocks(
  blocks: readonly Pair[][],
  featured: Pair | null,
  featuredRound: number,
): Pair[][] {
  const next = blocks.map((block) => [...block])
  if (!featured) return next

  const perBlock = blocks[0]?.length ?? 0
  const targetBlock = Math.floor((featuredRound - 1) / Math.max(perBlock, 1))
  const found = next.findIndex((block) =>
    block.some((pair) => pair[0] === featured[0] && pair[1] === featured[1]),
  )
  if (found === -1) {
    throw new RangeError(`赛程里不存在这场比赛：${featured.join(' vs ')}`)
  }

  const block = at(next.splice(found, 1), 0, '焦点局所在组')
  const rest = block.filter((pair) => !(pair[0] === featured[0] && pair[1] === featured[1]))
  next.splice(Math.min(targetBlock, next.length), 0, [...rest, featured])
  return next
}

/**
 * 生成完整赛程（`build_schedule.py::build()` 的移植）：
 * 每组内按顺序展开成连续轮次，日期 = 首轮日期 + (轮次 − 1) 天。
 * 页面用它现算一份赛程，再与 checked-in 的赛程逐轮比对，证明"固定赛程是可复现的"。
 */
export function buildSchedule(
  teams: readonly ScheduleTeam[],
  opts: {
    start?: string
    featured?: Pair | null
    featuredRound?: number
    playersPerTeam?: number
  } = {},
): Schedule {
  const start = opts.start ?? '2026-11-01'
  const featuredRound = opts.featuredRound ?? 12
  const playersPerTeam = opts.playersPerTeam ?? 2
  const featured = opts.featured ?? null
  const blocks = orderBlocks(
    roundRobin(teams.map((team) => Number(team.team_id))),
    featured,
    featuredRound,
  )

  const matches: ScheduleMatch[] = []
  let roundNo = 1
  for (const block of blocks) {
    for (const [teamA, teamB] of block) {
      matches.push({
        round: roundNo,
        played_at: addDays(start, roundNo - 1),
        team_a: teamA,
        team_b: teamB,
      })
      roundNo += 1
    }
  }
  return {
    schema_version: 1,
    season: schedule.season ?? 'demo-2026',
    generated_by: 'src/core/schedule.ts（build_schedule.py 的前端移植）',
    rules: {
      rounds: matches.length,
      matches_per_round: 1,
      teams_per_match: 2,
      suspended_players_per_round: 2 * playersPerTeam,
    },
    teams: teams.map((team) => ({ team_id: Number(team.team_id), name: team.name })),
    featured_round: featured ? featuredRound : null,
    matches,
  }
}

/* ---------------------------------------------------------------- 日期工具 */

const EPOCH_WEEKDAYS = ['周四', '周五', '周六', '周日', '周一', '周二', '周三']

/** ISO 日期加减天数（按 UTC 整天算，避免本地时区把日期算错一天） */
export function addDays(isoDate: string, days: number): string {
  const base = Date.parse(`${isoDate}T00:00:00Z`)
  if (Number.isNaN(base)) throw new RangeError(`不是合法的 ISO 日期：${isoDate}`)
  return new Date(base + days * 86_400_000).toISOString().slice(0, 10)
}

/** 今天的 ISO 日期（本地时区，与界面显示保持一致） */
export function todayIso(now: Date = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

/** ISO 日期的中文星期（赛程按天推进，标星期比标 ISO 日期好读） */
export function weekdayCn(isoDate: string): string {
  const days = Date.parse(`${isoDate}T00:00:00Z`) / 86_400_000
  return at(EPOCH_WEEKDAYS, Math.round(days) % 7, '星期表')
}

export type RoundPhase = 'played' | 'today' | 'upcoming'

/** 某一轮相对"今天"处于哪个阶段：已结束 / 今天开打 / 还没打 */
export function phaseOf(match: ScheduleMatch, today: string = todayIso()): RoundPhase {
  if (match.played_at === today) return 'today'
  return match.played_at < today ? 'played' : 'upcoming'
}

/**
 * 比赛日 → 第几轮：开赛前回到第 1 轮，超过赛程长度就按循环回落。
 * UI 用它决定"默认选中哪一轮"，不用人从第 1 轮翻起。
 */
export function roundOfDate(isoDate: string, sched: Schedule = schedule): number {
  const index = sched.matches.findIndex((match) => match.played_at >= isoDate)
  if (index === -1) return effectiveRound(sched.matches.length + 1, sched)
  return index + 1
}

/** 对阵的可读文案："Vitality vs Spirit" */
export function matchLabel(match: ScheduleMatch, sched: Schedule = schedule): string {
  const names = teamNames(sched)
  const a = names.get(Number(match.team_a)) ?? String(match.team_a)
  const b = names.get(Number(match.team_b)) ?? String(match.team_b)
  return `${a} vs ${b}`
}
