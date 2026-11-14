/**
 * 白话导读：市场页的"本轮停牌"可见性测试。
 *
 * 背景：后端 `players.status` 现在全是 trading（手动冻结已解除），停牌完全靠赛程派生。
 * 如果市场页还按老字段显示，就会出现"比赛中的选手看起来照样能买"——这正是要守住的回归点。
 * 名单用 8 队 × 2 人，所以**无论今天轮到第几轮，被停的都是 4 人**，断言不依赖具体日期。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const TEAMS = [
  'Vitality',
  'Spirit',
  'Falcons',
  'FaZe Clan',
  'G2',
  'NAVI',
  'Astralis',
  'The MongolZ',
]

const h = vi.hoisted(() => ({
  // oxlint 的 require-mock-type-parameters 要求写清 mock 签名
  listPlayers: vi.fn<() => Promise<unknown>>(),
  health: vi.fn<() => Promise<unknown>>(),
}))

vi.mock('../../api', () => ({
  api: { listPlayers: () => h.listPlayers(), health: () => h.health() },
}))

import MarketView from '../MarketView.vue'
import { currentRound } from '../../core/tradingStatus'

function roster() {
  return TEAMS.flatMap((team, index) => [
    {
      player_id: index * 2 + 1,
      name: `${team}-1`,
      display_name: `${team}-1`,
      team,
      role: 'Rifler',
      current_price: 10,
      prev_price: 10,
      change_pct: 0,
      rating: 80,
      status: 'trading',
    },
    {
      player_id: index * 2 + 2,
      name: `${team}-2`,
      display_name: `${team}-2`,
      team,
      role: 'AWPer',
      current_price: 10,
      prev_price: 10,
      change_pct: 0,
      rating: 80,
      status: 'trading',
    },
  ])
}

function mountView() {
  return mount(MarketView, {
    global: {
      components: {
        RouterLink: { name: 'RouterLink', props: ['to'], template: '<a :href="to"><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  vi.useFakeTimers()
  // 钉在赛季内的比赛日（UTC）：第 14 轮 G2 vs Astralis，避免用例跟着真实日期变红
  vi.setSystemTime(new Date('2026-11-14T04:00:00Z'))
  h.listPlayers.mockReset()
  h.health.mockReset()
  h.listPlayers.mockResolvedValue(roster())
  h.health.mockResolvedValue({ status: 'ok', service: 'playerstock-backend' })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('市场页 · 本轮停牌可见性', () => {
  it('16 人名单里按赛程停掉 4 人，徽章与卡片都跟着变', async () => {
    const w = mountView()
    await flushPromises()

    expect(w.findAll('.card')).toHaveLength(16)
    expect(w.findAll('.card.suspended')).toHaveLength(4)
    expect(w.findAll('.badge.halt')).toHaveLength(4)
  })

  it('顶部横幅说明"谁在打比赛、停了几个人"，并能直接去赛程页', async () => {
    const w = mountView()
    await flushPromises()

    const note = w.get('.round-note').text()
    expect(note).toContain(`第 ${currentRound()} 轮`)
    expect(note).toContain('比赛中')
    expect(note).toContain('4 人暂停交易')
    expect(w.get('.rn-link').attributes('href')).toBe('/schedule')
  })

  it('筛选"暂停"只剩本轮停牌的那 4 人', async () => {
    const w = mountView()
    await flushPromises()

    const haltedBtn = w.findAll('.seg-btn').find((btn) => btn.text() === '暂停')
    await haltedBtn!.trigger('click')

    expect(w.findAll('.card')).toHaveLength(4)
    expect(w.findAll('.card.suspended')).toHaveLength(4)
  })

  it('筛选"交易中"排除本轮停牌的 4 人', async () => {
    const w = mountView()
    await flushPromises()

    const tradingBtn = w.findAll('.seg-btn').find((btn) => btn.text() === '交易中')
    await tradingBtn!.trigger('click')

    expect(w.findAll('.card')).toHaveLength(12)
    expect(w.findAll('.card.suspended')).toHaveLength(0)
  })

  it('停牌卡片的悬浮提示是本轮对阵，不会误报成"手动暂停"', async () => {
    const w = mountView()
    await flushPromises()

    // 原因必须拿"原始 status"去算：拿派生后的对象会被判成手动冻结
    const titles = w.findAll('.card.suspended').map((card) => card.attributes('title'))
    expect(titles).toHaveLength(4)
    for (const title of titles) {
      expect(title).toContain('比赛中，暂停交易')
      expect(title).not.toContain('手动暂停')
    }
  })
})
