import { describe, expect, it } from 'vitest'
import { swipeTarget } from '../useSwipeNav'

describe('useSwipeNav / swipeTarget', () => {
  it('左滑：市场 → 赛程 → 持仓 → 流水', () => {
    expect(swipeTarget('market', -120, 10)).toBe('/schedule')
    expect(swipeTarget('schedule', -120, 10)).toBe('/positions')
    expect(swipeTarget('positions', -120, 10)).toBe('/trades')
  })

  it('右滑：反方向回上一个', () => {
    expect(swipeTarget('trades', 120, 10)).toBe('/positions')
    expect(swipeTarget('positions', 120, 10)).toBe('/schedule')
    expect(swipeTarget('schedule', 120, 10)).toBe('/')
  })

  it('第一个/最后一个不越界', () => {
    expect(swipeTarget('market', 120, 10)).toBeNull()
    expect(swipeTarget('trades', -120, 10)).toBeNull()
  })

  it('位移太小或纵向为主不算切页', () => {
    expect(swipeTarget('market', -40, 5)).toBeNull()
    expect(swipeTarget('market', -120, 150)).toBeNull()
  })

  it('非底部 Tab 页面不切', () => {
    expect(swipeTarget('player-detail', -120, 10)).toBeNull()
    expect(swipeTarget('profile', -120, 10)).toBeNull()
    expect(swipeTarget('auth', -120, 10)).toBeNull()
    expect(swipeTarget(undefined, -120, 10)).toBeNull()
  })
})
