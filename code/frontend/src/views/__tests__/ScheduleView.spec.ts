/**
 * 白话导读：赛程页的组件测试——不连后端，把 src/api 换成可控假货（16 人 / 8 队名单），
 * 然后验证"点一轮 → 页面按赛程算法重算"这件事真的发生了。
 *
 * 为什么值得测：这页把算法结论（谁暂停 / 几点可交易 / 第 29 轮循环回哪一轮）直接摆给用户看，
 * 一旦移植或改动让它和 core/schedule.ts 的结论不一致，答辩现场就是硬伤。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

/** 8 队 × 2 人 = 16 人，队伍名与 data/match_schedule.json 完全一致 */
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
}))

vi.mock('../../api', () => ({ api: { listPlayers: () => h.listPlayers() } }))
import ScheduleView from '../ScheduleView.vue'

/** 页面里有跳往选手详情的链接，测试里不需要真的路由，给个 <a> 替身即可 */
const stubs = {
  RouterLink: { name: 'RouterLink', props: ['to'], template: '<a><slot /></a>' },
}

function mountView() {
  return mount(ScheduleView, { global: { components: stubs } })
}

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

beforeEach(() => {
  h.listPlayers.mockReset()
  h.listPlayers.mockResolvedValue(roster())
})

describe('ScheduleView', () => {
  it('渲染 28 轮 / 7 组的赛程表与轮次选择条', async () => {
    const w = mountView()
    await flushPromises()

    expect(w.text()).toContain('赛程')
    expect(w.findAll('.strip .chip')).toHaveLength(28)
    expect(w.findAll('tr.row')).toHaveLength(28)
    expect(w.findAll('tr.group-row')).toHaveLength(7)
    expect(w.find('.chip-d i').exists()).toBe(true) // 焦点局标了 ★
  })

  it('点第 12 轮：焦点局两队整队暂停，其余 12 人可交易', async () => {
    const w = mountView()
    await flushPromises()

    const chips = w.findAll('.strip .chip')
    await chips[11]!.trigger('click')

    expect(w.text()).toContain('第 12 轮')
    expect(w.findAll('.list.halt li')).toHaveLength(4)
    expect(w.findAll('.chips .pchip')).toHaveLength(12)
    expect(w.text()).toContain('Vitality vs Spirit 比赛中，暂停交易')
    // 点数公式：第 12 轮 = 2 种子点 + 9 个可交易轮
    expect(w.text()).toContain('11')
  })

  it('轮次换算器：第 29 轮按 (29 − 1) % 28 + 1 回落到第 1 轮', async () => {
    const w = mountView()
    await flushPromises()

    const input = w.get('#probe-round')
    await input.setValue('29')

    expect((input.element as HTMLInputElement).value).toBe('29')
    expect(w.text()).toContain('29 − 1) % 28 + 1 = 1')
  })

  it('手动冻结的选手不会出现在"可交易"列表里', async () => {
    const frozen = roster()
    const target = frozen.find((player) => player.team === 'NAVI')
    if (target) target.status = 'halted'
    h.listPlayers.mockResolvedValue(frozen)

    const w = mountView()
    await flushPromises()

    // 第 12 轮暂停的是 Vitality / Spirit；NAVI 本该可交易，但被手动冻结的那位不算
    await w.findAll('.strip .chip')[11]!.trigger('click')
    expect(w.findAll('.chips .pchip')).toHaveLength(11)
    expect(w.text()).toContain('另有 1 人是手动冻结')
  })

  it('后端没连上时降级：仍给出暂停结论，不整页报错', async () => {
    h.listPlayers.mockRejectedValue(new Error('network down'))

    const w = mountView()
    await flushPromises()

    expect(w.findAll('tr.row')).toHaveLength(28)
    expect(w.text()).toContain('按规则给结论')
  })

  it('自检卡：注入"自己打自己"后 validate() 会报错', async () => {
    const w = mountView()
    await flushPromises()

    const box = w.get('.inject input[type=checkbox]')
    expect(w.text()).toContain('当前赛程通过全部')

    await box.setValue(true)
    expect(w.text()).toContain('打自己')
  })
})
