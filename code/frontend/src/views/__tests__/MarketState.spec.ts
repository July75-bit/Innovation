/**
 * 市场页状态记忆回归：
 *  1) 默认排序是「涨幅从高到低」，不是按 id 的列表顺序；
 *  2) 从选手详情返回（组件卸载再挂载）后，排序/筛选/搜索词都还在。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'

const h = vi.hoisted(() => ({
  players: [
    { player_id: 1, name: 'Alpha', display_name: 'Alpha', team: 'Vitality', role: 'Rifler', current_price: 10, prev_price: 10, change_pct: 1, rating: 80, status: 'trading' },
    { player_id: 2, name: 'Bravo', display_name: 'Bravo', team: 'Spirit', role: 'AWPer', current_price: 30, prev_price: 28, change_pct: 8, rating: 90, status: 'trading' },
    { player_id: 3, name: 'Charlie', display_name: 'Charlie', team: 'NAVI', role: 'Rifler', current_price: 20, prev_price: 20, change_pct: -5, rating: 70, status: 'trading' },
  ],
}))

vi.mock('../../api', () => ({
  api: {
    listPlayers: () => Promise.resolve(h.players),
    getAgentBrief: () => Promise.reject(new Error('no brief in unit test')),
    health: () => Promise.resolve({ status: 'ok', service: 'playerstock-backend' }),
  },
}))

import MarketView from '../MarketView.vue'

const KEY = 'playerstock.market.v1'

async function settle() {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await flushPromises()
  await nextTick()
}

function mountView() {
  return mount(MarketView, {
    global: {
      // 默认的 RouterLink stub 不会渲染插槽，卡片内容就看不见；这里给一个会渲染 slot 的替身
      stubs: { RouterLink: { template: '<a :href="to"><slot /></a>', props: ['to'] } },
    },
  })
}

beforeEach(() => {
  sessionStorage.removeItem(KEY)
})

describe('市场页 · 状态记忆', () => {
  it('默认按涨幅从高到低排序（不是列表顺序）', async () => {
    const wrapper = mountView()
    await settle()

    const select = wrapper.get('select[aria-label="排序方式"]').element as HTMLSelectElement
    expect(select.value).toBe('change')

    const names = wrapper.findAll('.p-name').map((node) => node.text())
    expect(names).toEqual(['Bravo', 'Alpha', 'Charlie'])
    wrapper.unmount()
  })

  it('离开再回来：排序 / 筛选项 / 搜索词都保留', async () => {
    const first = mountView()
    await settle()

    await first.get('select[aria-label="排序方式"]').setValue('price')
    await first.get('input[type="search"]').setValue('Bra')
    const halted = first.findAll('.filter').find((btn) => btn.text() === '停牌')
    await halted!.trigger('click')
    await nextTick()
    first.unmount()

    // 模拟「点开选手再退回来」：组件重新挂载
    const second = mountView()
    await settle()

    expect((second.get('select[aria-label="排序方式"]').element as HTMLSelectElement).value).toBe(
      'price',
    )
    expect((second.get('input[type="search"]').element as HTMLInputElement).value).toBe('Bra')
    expect(second.get('.filter.active').text()).toBe('停牌')
    second.unmount()
  })

  it('刷新后恢复：sessionStorage 里的坏数据会退回默认值', async () => {
    sessionStorage.setItem(KEY, JSON.stringify({ sort: 'weird', status: 'nope', keyword: 123 }))
    const wrapper = mountView()
    await settle()

    expect((wrapper.get('select[aria-label="排序方式"]').element as HTMLSelectElement).value).toBe(
      'change',
    )
    expect(wrapper.get('.filter.active').text()).toBe('全部')
    wrapper.unmount()
  })
})
