/**
 * 白话导读：把"这一轮谁在打比赛"翻译成选手状态，供市场页 / 详情页 / 交易面板共用。
 *
 * 为什么要单独一层：后端 `players.status` 存的是**初始/手动**状态（现在 16 人全是 trading），
 * 而"本轮停牌"是按赛程**派生**出来的（见 `core/schedule.ts`，与后端 `suspension_reason` 同一条规则）。
 * 如果每个页面各自判断，市场页显示"交易中"、详情页却禁用买入，就是两个答案打架。
 *
 * 优先级和后端完全一致：**手动 status 优先**（运维冻结），其次才看本队这一轮有没有比赛。
 * 这些函数都返回副本，绝不改写接口返回的原对象——排序/筛选/图表可能正拿着它。
 */
import { TRADING, liveRound, statusFor, suspensionReason, type SchedulePlayer } from './schedule'

/** 带 status 的最小形状：`PlayerSummary` / `PlayerDetail` 都满足 */
export interface StatusedPlayer extends SchedulePlayer {
  status: string
}

/**
 * 今天属于赛程的第几轮；**不是比赛日返回 null**（口径与后端 `core_engine.current_round` 一致：
 * 按 UTC 日期查 `played_at`）。这样"界面显示暂停"与"接口拦单"永远给同一个答案。
 */
export function currentRound(now: Date = new Date()): number | null {
  return liveRound(now)
}

/**
 * 选手在这一轮的展示状态：`trading` / `suspended`。
 * 只读派生，不改原对象；状态没变时直接返回原引用（Vue 的 computed 因此不会触发多余重渲染）。
 */
export function withRoundStatus<T extends StatusedPlayer>(
  player: T,
  round: number | null = currentRound(),
): T {
  // 今天不是比赛日 → 没有"本轮停牌"这回事，原样返回（只剩手动 status 生效）
  if (round === null) return player
  // 手动 status 优先：运维冻结的人不会因为"这轮没比赛"就被放回可交易列表
  if (player.status !== TRADING) return player
  const derived = statusFor(player, round)
  return derived === player.status ? player : { ...player, status: derived }
}

/** 名单整体派生（市场页一次 16 人） */
export function withRoundStatusAll<T extends StatusedPlayer>(
  list: readonly T[],
  round: number | null = currentRound(),
): T[] {
  return list.map((player) => withRoundStatus(player, round))
}

/**
 * 为什么不能交易；能交易返回 null。文案与后端 `suspension_reason()` 一字不差，
 * 所以界面上的解释和结算时真正生效的原因是同一句话。
 */
export function haltReason<T extends StatusedPlayer>(
  player: T,
  round: number | null = currentRound(),
): string | null {
  // 手动冻结先答（与后端 suspension_reason 同句文案）
  const stored = String(player.status ?? TRADING)
  if (stored !== TRADING) return `状态 ${stored}（手动暂停）`
  if (round === null) return null
  // 剩下才看赛程。注意要传"原始"选手：派生后的 status 已变成 suspended，
  // 再喂给 suspensionReason 会被当成手动冻结（踩过：文案变成"状态 suspended（手动暂停）"）
  return suspensionReason({ ...player, status: TRADING }, round)
}

/** 是否处于停牌（手动或赛程派生都算） */
export function isHalted<T extends StatusedPlayer>(
  player: T,
  round: number | null = currentRound(),
): boolean {
  return withRoundStatus(player, round).status !== 'trading'
}
