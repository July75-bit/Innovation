/**
 * 白话导读：组件测试——把 PriceChart.vue 用 @vue/test-utils 的 mount() 在假浏览器(jsdom)里渲染出来，
 * 再检查"没数据时不画 svg""每个点的 reason 能在明细里看到"这些行为是否成立。
 * mount 的 props 就是父组件正常会传的数据，测试用的 points 是手写的假行情。
 */

import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PriceChart from '../PriceChart.vue'
import type { PricePoint } from '../../api/types'

const points: PricePoint[] = [
  { ts: '2026-10-01T00:00:00Z', price: 100, reason: '初始价格' },
  { ts: '2026-10-02T00:00:00Z', price: 110, reason: '表现提升，价格上涨 10.00%（本轮模拟得分 85.2）' },
  { ts: '2026-10-03T00:00:00Z', price: 105, reason: '表现下滑，价格下跌 4.55%（本轮模拟得分 70.1）' },
]

describe('PriceChart（T4-02 每点 reason 展示）', () => {
  it('无数据点显示空态，不渲染 svg', () => {
    const w = mount(PriceChart, { props: { points: [] } })
    expect(w.text()).toContain('暂无价格历史数据')
    expect(w.find('svg').exists()).toBe(false)
  })

  it('每个数据点带原生 title（时间/价格/reason 兜底提示）', () => {
    const w = mount(PriceChart, { props: { points } })
    const titles = w.findAll('.hit title')
    expect(titles).toHaveLength(3)
    expect(titles[0]!.text()).toContain('初始价格')
    expect(titles[2]!.text()).toContain('表现下滑，价格下跌 4.55%')
  })

  it('悬停数据点显示含 reason 的 tooltip，移开后消失', async () => {
    const w = mount(PriceChart, { props: { points } })
    expect(w.find('.tip').exists()).toBe(false)
    await w.findAll('.hit')[1]!.trigger('mouseenter')
    const tip = w.get('.tip')
    expect(tip.text()).toContain('110.00')
    expect(tip.text()).toContain('表现提升，价格上涨 10.00%')
    await w.findAll('.hit')[1]!.trigger('mouseleave')
    expect(w.find('.tip').exists()).toBe(false)
  })

  it('键盘 Tab 聚焦数据点同样弹出 tooltip，失焦隐藏（A6 无障碍）', async () => {
    const w = mount(PriceChart, { props: { points } })
    const hits = w.findAll('.hit')
    expect(hits[1]!.attributes('tabindex')).toBe('0')
    expect(hits[1]!.attributes('aria-label')).toContain('表现提升，价格上涨 10.00%')
    await hits[1]!.trigger('focus')
    expect(w.get('.tip').text()).toContain('表现提升，价格上涨 10.00%')
    await hits[1]!.trigger('blur')
    expect(w.find('.tip').exists()).toBe(false)
  })

  it('明细列表默认收起，展开后逐点展示时间/价格/reason', async () => {
    const w = mount(PriceChart, { props: { points } })
    expect(w.find('.detail-list').exists()).toBe(false)
    await w.get('.detail-toggle').trigger('click')
    const items = w.findAll('.detail-list li')
    expect(items).toHaveLength(3)
    expect(items[1]!.text()).toContain('表现提升，价格上涨 10.00%')
    expect(items[2]!.text()).toContain('表现下滑，价格下跌 4.55%')
  })
})

describe('PriceChart 显示窗口（只保留最新 10 个日历天）', () => {
  /** 造 n 个连续日期的点（UTC 零点），起始日可指定 */
  function daily(from: string, n: number): PricePoint[] {
    return Array.from({ length: n }, (_, i) => {
      const day = new Date(Date.parse(`${from}T00:00:00Z`) + i * 86_400_000).toISOString().slice(0, 10)
      return { ts: `${day}T00:00:00Z`, price: 100 + i, reason: `第 ${i + 1} 点` }
    })
  }

  it('12 个连续日点 → 只画最近 10 天（最旧 2 点被裁掉）', () => {
    const w = mount(PriceChart, { props: { points: daily('2026-10-01', 12) } })
    const titles = w.findAll('.hit title')
    expect(titles).toHaveLength(10)
    expect(titles[0]!.text()).toContain('第 3 点')
    expect(titles[9]!.text()).toContain('第 12 点')
  })

  it('窗口按日历天而非点数：含停牌缺口时点数可少于 10', () => {
    const pts = daily('2026-10-01', 12).filter((p) => !p.ts.startsWith('2026-10-05') && !p.ts.startsWith('2026-10-06'))
    const w = mount(PriceChart, { props: { points: pts } })
    // 最新点 10-12 → 窗口 10-03 起；10-05/06 本就不存在 → 8 个点
    expect(w.findAll('.hit title')).toHaveLength(8)
  })

  it('锚定最新点所在日：选手停牌时窗口跟着回退，不会裁成空图', () => {
    const pts = daily('2026-10-01', 12).slice(0, 10) // 最新点 10-10，今天可能是 10-20
    const w = mount(PriceChart, { props: { points: pts } })
    expect(w.findAll('.hit title')).toHaveLength(10)
  })

  it('windowDays=0 → 全量展示（逃生口）', () => {
    const w = mount(PriceChart, { props: { points: daily('2026-10-01', 12), windowDays: 0 } })
    expect(w.findAll('.hit title')).toHaveLength(12)
  })
})