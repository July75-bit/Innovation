/**
 * 白话导读：详情页的"本轮停牌"回归测试。
 *
 * 为什么单独一个文件：停牌是**按赛程派生**的（后端 status 全是 trading），
 * 一旦详情页只认后端字段，就会出现"徽章说能买、其实这一轮他正在打比赛"的矛盾。
 * 断言不写死轮次：先算出本轮正在比赛的两队，再把选手挂到其中一队，换日子也不会红。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const h = vi.hoisted(() => ({
  // oxlint 的 require-mock-type-parameters 要求写清 mock 签名
  getPlayer: vi.fn<() => Promise<unknown>>(),
  health: vi.fn<() => Promise<unknown>>(),
  getAccount: vi.fn<() => Promise<unknown>>(),
  getPriceHistory: vi.fn<() => Promise<unknown>>(),
  getPositions: vi.fn<() => Promise<unknown>>(),
  getAnalysis: vi.fn<() => Promise<unknown>>(),
}))

vi.mock('../../api', () => ({
  api: {
    health: () => h.health(),
    getAccount: () => h.getAccount(),
    getPlayer: () => h.getPlayer(),
    getPriceHistory: () => h.getPriceHistory(),
    getPositions: () => h.getPositions(),
    getAnalysis: () => h.getAnalysis(),
  },
}))
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  RouterLink: { name: 'RouterLink', props: ['to'], template: '<a :href="to"><slot /></a>' },
}))

import PlayerDetailView from '../PlayerDetailView.vue'
import { currentRound } from '../../core/tradingStatus'
import { playingTeams, roundMatch, teamNames } from '../../core/schedule'

const names = teamNames()

function playerOf(team: string) {
  return {
    player_id: 1,
    name: 'TestPlayer',
    display_name: 'TestPlayer',
    team,
    role: 'AWPer',
    current_price: 10,
    prev_price: 10,
    change_pct: 0,
    rating: 80,
    status: 'trading',
    latest_reason: '测试原因',
  }
}

async function mountView(team: string) {
  h.getPlayer.mockResolvedValue(playerOf(team))
  const w = mount(PlayerDetailView)
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.useFakeTimers()
  // 钉在赛季内的比赛日（UTC）：第 14 轮 G2 vs Astralis，避免用例跟着真实日期变红
  vi.setSystemTime(new Date('2026-11-14T04:00:00Z'))
  vi.clearAllMocks()
  h.health.mockResolvedValue({ status: 'ok', service: 'playerstock-backend' })
  h.getAccount.mockResolvedValue({
    user_id: 1,
    balance: 5000,
    initial_balance: 5000,
    position_value: 0,
    total_asset: 5000,
  })
  h.getPriceHistory.mockResolvedValue({ player_id: 1, points: [] })
  h.getPositions.mockResolvedValue([])
  h.getAnalysis.mockResolvedValue({
    player_id: 1,
    action: 'HOLD',
    reason: '测试建议',
    risk_level: 'LOW',
    source: 'rule_fallback',
    disclaimer: '仅为分析建议',
  })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('详情页 · 本轮停牌', () => {
  it('本轮有比赛的选手：徽章变停牌、原因写清楚、买卖按钮禁用', async () => {
    const round = currentRound()!
    const playing = [...playingTeams(round)]
    const w = await mountView(names.get(playing[0] as number) as string)

    expect(w.find('.badge.halt').exists()).toBe(true)
    expect(w.get('.halt-note').text()).toContain('比赛中，暂停交易')
    expect(w.findAll('.actions button')[0]!.text()).toContain('暂停交易中')
    expect(w.findAll('.actions button')[0]!.attributes('disabled')).toBeDefined()
    // 文案要和后端 suspension_reason 同源：直接对照本轮对阵
    const match = roundMatch(round)
    expect(w.get('.halt-note').text()).toContain(
      `${names.get(Number(match.team_a))} vs ${names.get(Number(match.team_b))}`,
    )
  })

  it('本轮没比赛的选手：照常显示交易中，按钮可用', async () => {
    const round = currentRound()!
    const playing = playingTeams(round)
    const idleTeam = [...names.entries()].find(([id]) => !playing.has(id))?.[1] ?? ''
    const w = await mountView(idleTeam)

    expect(w.find('.badge.halt').exists()).toBe(false)
    expect(w.find('.halt-note').exists()).toBe(false)
    expect(w.findAll('.actions button')[0]!.attributes('disabled')).toBeUndefined()
  })
})
