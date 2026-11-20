/**
 * 个人主页（/me）回归测试：
 * 资产数字、资产曲线、交易统计/最近交易、主题偏好与关于入口都要在。
 */
import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const push = vi.fn<() => Promise<void>>()

const h = vi.hoisted(() => ({
  account: {
    user_id: 1,
    balance: 4400,
    initial_balance: 5000,
    position_value: 900,
    total_asset: 5300,
  },
  history: {
    initial_balance: 5000,
    points: [
      { ts: '2026-11-01T00:00:00Z', cash: 5000, position_value: 0, total_asset: 5000 },
      { ts: '2026-11-10T00:00:00Z', cash: 4400, position_value: 800, total_asset: 5200 },
      { ts: '2026-11-20T00:00:00Z', cash: 4400, position_value: 900, total_asset: 5300 },
    ],
    stats: {
      trades: 2,
      buys: 1,
      sells: 1,
      buy_amount: 1260,
      sell_amount: 105,
      positions: 1,
      position_value: 900,
      profit: 300,
    },
  },
  trades: [
    {
      trade_id: 2,
      player_id: 1,
      name: 'ZywOo',
      side: 'SELL',
      quantity: 1,
      price: 105,
      amount: 105,
      balance_after: 4400,
      created_at: '2026-11-19T10:00:00Z',
    },
  ],
}))

vi.mock('../../api', () => ({
  api: {
    getAccount: () => Promise.resolve(h.account),
    getAccountHistory: () => Promise.resolve(h.history),
    listTrades: () => Promise.resolve(h.trades),
    health: () => Promise.resolve({ status: 'ok', service: 'playerstock-backend' }),
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
  RouterLink: { name: 'RouterLink', props: ['to'], template: '<a :href="to"><slot /></a>' },
}))

import ProfileView from '../ProfileView.vue'

const mountView = () =>
  mount(ProfileView, { global: { components: { RouterLink: { template: '<a><slot /></a>' } } } })

describe('个人主页', () => {
  it('展示资产数字、曲线、统计与最近交易', async () => {
    const w = mountView()
    await flushPromises()

    expect(w.text()).toContain('我的')
    const values = w.findAll('.asset-value').map((node) => node.text())
    expect(values[0]).toBe('4,400.00') // 余额
    expect(values[1]).toBe('5,300.00') // 总资产
    expect(values[2]).toBe('+300.00') // 总收益
    expect(w.find('svg').exists()).toBe(true)
    expect(w.text()).toContain('交易笔数')
    expect(w.text()).toContain('买入 / 卖出')
    expect(w.text()).toContain('ZywOo')
    expect(w.text()).toContain('卖出')
    w.unmount()
  })

  it('主题偏好可切换（自动/浅色/深色 → 写 data-theme）', async () => {
    const w = mountView()
    await flushPromises()

    const buttons = w.findAll('.segmented .seg')
    expect(buttons.map((button) => button.text())).toEqual(['自动', '浅色', '深色'])

    await buttons[2]!.trigger('click')
    expect(document.documentElement.dataset.theme).toBe('dark')
    w.unmount()
  })

  it('「关于本站」可打开说明弹窗', async () => {
    const w = mountView()
    await flushPromises()

    const about = w.findAll('button').find((button) => button.text().includes('查看说明'))
    await about!.trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('不可充值')
    w.unmount()
  })

  it('访客态显示登录入口，不显示删除账号', async () => {
    const w = mountView()
    await flushPromises()

    expect(w.text()).toContain('登录 / 注册')
    expect(w.text()).not.toContain('删除账号')
    w.unmount()
  })
})
