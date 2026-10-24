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