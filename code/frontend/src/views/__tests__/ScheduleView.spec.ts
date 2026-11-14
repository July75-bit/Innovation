/**
 * 白话导读：赛程页的组件测试——不连后端，把 src/api 换成可控假货（16 人 / 8 队名单），
 * 然后验证"换一轮 → 名单跟着重算"这件事真的发生了。
 *
 * 为什么值得测：这页把算法结论（谁停牌 / 谁能买）直接摆给用户看，
 * 一旦页面和 core/schedule.ts 的结论不一致，答辩现场就是硬伤。
 * 算法本身的六条契约（结构 / 均衡 / 派生 / 循环 / 生成 / 校验）在
 * `src/core/__tests__/schedule.spec.ts` 里逐条守着，这里只测界面。
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

/** 页面里有跳往选手详情的链接，测试里不需要真的路由，给个 <a> 替身即可 */
function mountView() {
  return mount(ScheduleView, {
    global: {
      components: {
        RouterLink: { name: 'RouterLink', props: ['to'], template: '<a><slot /></a>' },
      },
    },
  })
}

async function pickRound(w: ReturnType<typeof mountView>, round: number) {
  await w.findAll('.strip .chip')[round - 1]!.trigger('click')
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

  it('点第 12 轮：焦点局两队整队停牌 4 人，其余 12 人可交易', async () => {
    const w = mountView()
    await flushPromises()

    await pickRound(w, 12)

    expect(w.text()).toContain('第 12 轮')
    expect(w.text()).toContain('Vitality / Spirit')
    expect(w.findAll('.list li')).toHaveLength(4)
    expect(w.findAll('.chips .pchip')).toHaveLength(12)
    // 焦点局那轮的对阵与"暂停"提示同时出现，说明结论来自赛程而不是写死的文案
    expect(w.find('.match').text()).toContain('Vitality')
    expect(w.find('.match').text()).toContain('Spirit')
  })

  it('左右翻页按钮按轮次移动，边界处禁用', async () => {
    const w = mountView()
    await flushPromises()

    await pickRound(w, 2)
    await w.get('button[aria-label="下一轮"]').trigger('click')
    expect(w.find('.match-meta').text()).toContain('第 3 轮')

    await pickRound(w, 1)
    expect(w.get('button[aria-label="上一轮"]').attributes('disabled')).toBeDefined()

    await pickRound(w, 28)
    expect(w.get('button[aria-label="下一轮"]').attributes('disabled')).toBeDefined()
  })

  it('手动冻结的选手不会出现在"可交易"列表里', async () => {
    const frozen = roster()
    const target = frozen.find((player) => player.team === 'NAVI')
    if (target) target.status = 'halted'
    h.listPlayers.mockResolvedValue(frozen)

    const w = mountView()
    await flushPromises()

    // 第 12 轮停牌的是 Vitality / Spirit；NAVI 本该可交易，但被手动冻结的那位不算
    await pickRound(w, 12)
    expect(w.findAll('.chips .pchip')).toHaveLength(11)
    expect(w.text()).toContain('另有 1 人暂停（非赛程原因）')
  })

  it('后端没连上时降级：仍按赛程给出暂停结论，不整页报错', async () => {
    h.listPlayers.mockRejectedValue(new Error('network down'))

    const w = mountView()
    await flushPromises()

    expect(w.findAll('tr.row')).toHaveLength(28)
    expect(w.text()).toContain('按赛程给结论')
    expect(w.text()).toContain('整队停牌')
  })
})
