/**
 * 白话导读：详情页测试——用受控 Promise 造一个"很慢的 AI 接口"，
 * 验证 AI 结果还没回来时页面显示「AI 分析中…」占位，回来后换成真正的建议卡片。
 * vi.hoisted / vi.mock 是 Vitest 的"假接口(mock)"写法：把 src/api 整个换成可控的假货，
 * 这样测试不需要真的后端在跑，也不会真的下单。
 */

import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import PlayerDetailView from '../PlayerDetailView.vue'

/**
 * A5 验收：AI 请求未返回期间，卡片位显示「AI 分析中…」占位（防布局跳动）；
 * 返回后替换为建议卡。用受控 Promise 模拟 Slow 3G 的慢 AI，无需真实网络。
 */
const h = vi.hoisted(() => {
  let resolveAnalysis!: (v: unknown) => void
  const analysisPromise = new Promise((r) => {
    resolveAnalysis = r
  })
  return {
    resolve: () =>
      resolveAnalysis({
        player_id: 1,
        action: 'HOLD',
        reason: '测试建议：估值合理',
        risk_level: 'LOW',
        source: 'rule_fallback',
        disclaimer: '仅为分析建议，不构成投资建议',
      }),
    api: {
      health: () => Promise.resolve({ status: 'ok', service: 'playerstock-backend' }),
      getAccount: () =>
        Promise.resolve({ user_id: 1, balance: 5000, initial_balance: 5000, position_value: 0, total_asset: 5000 }),
      getPlayer: () =>
        Promise.resolve({
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
          latest_reason: '测试原因',
        }),
      getPriceHistory: () => Promise.resolve({ player_id: 1, points: [] }),
      getPositions: () => Promise.resolve([]),
      getAnalysis: () => analysisPromise,
    },
  }
})

vi.mock('../../api', () => ({ api: h.api }))
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
  RouterLink: { name: 'RouterLink', props: ['to'], template: '<a><slot /></a>' },
}))

describe('PlayerDetailView AI 分析中态（A5）', () => {
  it('AI 未返回时显示「AI 分析中…」，返回后显示建议卡', async () => {
    const w = mount(PlayerDetailView)
    await flushPromises() // 行情/持仓/价格历史已回，AI Promise 故意不 resolve
    expect(w.text()).toContain('ZywOo')
    expect(w.text()).toContain('AI 分析中…')
    expect(w.text()).not.toContain('测试建议：估值合理')

    h.resolve()
    await flushPromises()
    expect(w.text()).toContain('测试建议：估值合理')
    expect(w.text()).not.toContain('AI 分析中…')
  })
})