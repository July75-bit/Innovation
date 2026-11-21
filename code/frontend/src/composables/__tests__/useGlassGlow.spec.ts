/**
 * 液态玻璃指针高光：位置换算纯函数 + 降级行为。
 * 真实指针跟踪依赖 matchMedia/requestAnimationFrame，这里重点保证：
 *  - 坐标换算正确且夹在 0–100；
 *  - 触屏 / reduced-motion 环境下 initGlassGlow 不注册监听、返回可安全调用的清理函数。
 */
import { afterEach, describe, expect, it, vi } from 'vitest'

import { glowPosition, initGlassGlow } from '../useGlassGlow'

describe('glowPosition（指针 → 百分比）', () => {
  const rect = { left: 100, top: 50, width: 200, height: 100 }

  it('中心点 = 50% / 50%', () => {
    expect(glowPosition(rect, 200, 100)).toEqual({ x: 50, y: 50 })
  })

  it('左上角 = 0 / 0，右下角 = 100 / 100', () => {
    expect(glowPosition(rect, 100, 50)).toEqual({ x: 0, y: 0 })
    expect(glowPosition(rect, 300, 150)).toEqual({ x: 100, y: 100 })
  })

  it('越界坐标会被夹住（拖到元素外不产生负值/超界）', () => {
    expect(glowPosition(rect, -500, -500)).toEqual({ x: 0, y: 0 })
    expect(glowPosition(rect, 9999, 9999)).toEqual({ x: 100, y: 100 })
  })

  it('宽高为 0 时给安全默认值，不出现 NaN', () => {
    expect(glowPosition({ left: 0, top: 0, width: 0, height: 0 }, 10, 10)).toEqual({ x: 50, y: 0 })
  })
})

describe('initGlassGlow（降级）', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('触屏（无 hover）环境不注册监听，返回的清理函数可安全调用', () => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: false,
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
    const addSpy = vi.spyOn(document, 'addEventListener')
    const cleanup = initGlassGlow()
    expect(addSpy).not.toHaveBeenCalledWith('pointermove', expect.anything(), expect.anything())
    expect(() => cleanup()).not.toThrow()
    addSpy.mockRestore()
  })

  it('桌面且允许动效：注册 pointermove / pointerleave，清理后移除', () => {
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: !query.includes('reduced-motion'),
      media: query,
      addEventListener: () => {},
      removeEventListener: () => {},
    }))
    vi.stubGlobal('requestAnimationFrame', () => 1)
    vi.stubGlobal('cancelAnimationFrame', () => {})
    const addSpy = vi.spyOn(document, 'addEventListener')
    const removeSpy = vi.spyOn(document, 'removeEventListener')
    const cleanup = initGlassGlow()
    expect(addSpy).toHaveBeenCalledWith('pointermove', expect.any(Function), { passive: true })
    cleanup()
    expect(removeSpy).toHaveBeenCalledWith('pointermove', expect.any(Function))
    addSpy.mockRestore()
    removeSpy.mockRestore()
  })
})
