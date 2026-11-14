/**
 * 今日简报的可读性回归测试。
 *
 * 背景（线上真实问题）：模型偶尔不按"只输出一句话"来，返回
 * `{"action": "HOLD", "reason": "..."}`，后端旧版本只做截断就透传，
 * 首页简报直接显示成一整段代码。
 *
 * 这里守住两件事：
 * 1. 摘要里的 JSON / 字段名不许出现在界面上（cleanSummary 兜底）；
 * 2. 三条要点仍然正常渲染（清洗不能把内容洗没）。
 */

import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import MarketView from '../MarketView.vue'

const h = vi.hoisted(() => ({
  brief: {
    generated_at: '2026-11-14T07:00:00+00:00',
    ttl_seconds: 600,
    summary: '{"action": "HOLD", "reason": "sh1ro 现价 136.43，单日上涨 13.96%；bLitz 现价 48.48',
    source: 'llm',
    items: [
      { title: '今日最该看一眼', detail: 'sh1ro（Spirit）变动 +13.96%，现价 136.43', player_id: 7 },
      { title: '低价区标的', detail: 'bLitz 现价 48.48，评分 64', player_id: 16 },
      { title: '停牌提醒', detail: '当前无选手停牌', player_id: null },
    ],
  },
  players: [
    {
      player_id: 1,
      name: 'ZywOo',
      display_name: 'ZywOo',
      team: 'Vitality',
      role: 'AWPer',
      current_price: 100,
      prev_price: 99,
      change_pct: 1.01,
      rating: 88,
      status: 'trading',
    },
  ],
  api: {
    getPlayers: () => Promise.resolve({ players: [] }),
    getAccount: () =>
      Promise.resolve({
        user_id: 1,
        balance: 5000,
        initial_balance: 5000,
        position_value: 0,
        total_asset: 5000,
      }),
    getAgentBrief: () => Promise.resolve(h.brief),
  },
}))

vi.mock('../../api', () => ({ api: h.api }))

describe('市场页 · 今日简报', () => {
  it('摘要里的 JSON 被清洗成人话，界面上不出现花括号与字段名', async () => {
    const wrapper = mount(MarketView, { global: { stubs: { RouterLink: true } } })
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))
    await flushPromises()

    const summary = wrapper.find('.brief-summary')
    expect(summary.exists()).toBe(true)
    const text = summary.text()

    expect(text).not.toContain('{')
    expect(text).not.toContain('"reason"')
    expect(text).not.toContain('action')
    expect(text).toContain('sh1ro 现价 136.43')
  })

  it('三条要点照常显示（清洗不影响内容）', async () => {
    const wrapper = mount(MarketView, { global: { stubs: { RouterLink: true } } })
    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 0))
    await flushPromises()

    const items = wrapper.findAll('.brief-items li')
    expect(items).toHaveLength(3)
    expect(items[0]!.text()).toContain('今日最该看一眼')
    expect(items[1]!.text()).toContain('低价区标的')
    expect(items[2]!.text()).toContain('停牌提醒')
  })
})
