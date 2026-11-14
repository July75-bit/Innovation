/**
 * 白话导读：`core/tradingStatus.ts` 的用例——市场页/详情页显示的"暂停交易"就是从这儿来的。
 *
 * 守住的口径（和后端 `suspension_reason` 完全一致）：
 * 1. 本轮有比赛的队 → 整队显示停牌；没比赛 → 交易中；
 * 2. **手动 status 优先**：运维冻结的人不会因为"这轮没比赛"就被界面放回可交易；
 * 3. 只返回副本，绝不改接口给的原对象；
 * 4. 文案原样复用后端那句"X vs Y 比赛中，暂停交易"。
 */
import { describe, expect, it } from 'vitest'
import { roundMatch } from '../schedule'
import {
  currentRound,
  haltReason,
  isHalted,
  withRoundStatus,
  withRoundStatusAll,
} from '../tradingStatus'

const player = (name: string, team: string, status = 'trading') => ({ name, team, status })

describe('tradingStatus', () => {
  it('第 12 轮打比赛的 Vitality / Spirit 显示停牌，其余照常', () => {
    expect(withRoundStatus(player('ZywOo', 'Vitality'), 12).status).toBe('suspended')
    expect(withRoundStatus(player('donk', 'Spirit'), 12).status).toBe('suspended')
    expect(withRoundStatus(player('m0NESY', 'G2'), 12).status).toBe('trading')
    expect(isHalted(player('m0NESY', 'G2'), 12)).toBe(false)
  })

  it('手动冻结优先：本轮没比赛也仍然是停牌', () => {
    const frozen = player('sh1ro', 'NAVI', 'halted')
    expect(withRoundStatus(frozen, 12).status).toBe('halted')
    expect(haltReason(frozen, 12)).toBe('状态 halted（手动暂停）')
    expect(isHalted(frozen, 12)).toBe(true)
  })

  it('停牌文案与后端同源', () => {
    expect(haltReason(player('ZywOo', 'Vitality'), 12)).toBe('Vitality vs Spirit 比赛中，暂停交易')
    expect(haltReason(player('NiKo', 'Falcons'), 12)).toBeNull()
  })

  it('不改原对象，只返回副本', () => {
    const original = player('ZywOo', 'Vitality')
    const derived = withRoundStatus(original, 12)
    expect(derived).not.toBe(original)
    expect(original.status).toBe('trading')
    // 状态没变时保持原引用，避免 computed 白白重渲染
    const same = player('NiKo', 'Falcons')
    expect(withRoundStatus(same, 12)).toBe(same)
  })

  it('整份名单派生后仍是 16 人，本轮停 4 人', () => {
    const teams = [
      'Vitality',
      'Spirit',
      'Falcons',
      'FaZe Clan',
      'G2',
      'NAVI',
      'Astralis',
      'The MongolZ',
    ]
    const roster = teams.flatMap((team) => [player(`${team}-1`, team), player(`${team}-2`, team)])
    const listed = withRoundStatusAll(roster, 12)
    expect(listed).toHaveLength(16)
    expect(listed.filter((p) => p.status === 'suspended')).toHaveLength(4)
  })

  it('今天落在赛程第几轮，就按那一轮派生', () => {
    const round = currentRound('2026-11-14')
    expect(round).toBe(14)
    const match = roundMatch(round)
    const a = player('A', 'G2')
    const b = player('B', 'Vitality')
    expect(isHalted(a, round)).toBe(withRoundStatusAll([a], round)[0]!.status === 'suspended')
    expect(withRoundStatusAll([b], round)[0]!.status).toBe(
      match.team_a === 1 || match.team_b === 1 ? 'suspended' : 'trading',
    )
  })

  it('赛程里没有的队（本地 mock 名单）不会被误判成停牌', () => {
    expect(withRoundStatus(player('Ghost', 'NotExist'), 12).status).toBe('trading')
  })
})
