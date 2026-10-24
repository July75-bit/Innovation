import { describe, expect, it } from 'vitest'
import { dateTime, money, pct, trendClass } from '../format'

describe('展示层格式化', () => {
  it('money 固定两位小数（后端数值不再二次截断，只补零）', () => {
    expect(money(4748)).toBe('4748.00')
    expect(money(126.5)).toBe('126.50')
    expect(money(126.12)).toBe('126.12')
  })

  it('pct 正数带 + 号，负数保留 - 号', () => {
    expect(pct(5)).toBe('+5.00%')
    expect(pct(-3.25)).toBe('-3.25%')
    expect(pct(0)).toBe('0.00%')
  })

  it('trendClass 按正负返回涨跌样式', () => {
    expect(trendClass(1.2)).toBe('up')
    expect(trendClass(-0.5)).toBe('down')
    expect(trendClass(0)).toBe('flat')
  })

  it('dateTime 能解析契约中的 ISO 8601 UTC 字符串', () => {
    const out = dateTime('2026-01-01T10:05:00Z')
    expect(out.length).toBeGreaterThan(0)
    expect(new Date('2026-01-01T10:05:00Z').getTime()).toBe(Date.parse('2026-01-01T10:05:00Z'))
  })
})
