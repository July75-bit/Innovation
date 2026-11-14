/**
 * 主题测试：默认「自动跟随系统」、系统切换实时跟随、手动选择后不再被系统覆盖、持久化、三档循环。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  THEME_STORAGE_KEY,
  applyTheme,
  cycleTheme,
  initTheme,
  resolveTheme,
  useTheme,
} from '../../composables/useTheme'

/** 可手动触发的 matchMedia 桩：既能读 matches，也能模拟系统切换事件 */
function stubMatchMedia(initialLight: boolean) {
  const listeners: Array<() => void> = []
  const state = { light: initialLight }
  vi.stubGlobal('matchMedia', (query: string) => ({
    get matches() {
      return state.light && query.includes('prefers-color-scheme: light')
    },
    media: query,
    addEventListener: (_: string, cb: () => void) => listeners.push(cb),
    removeEventListener: () => {},
  }))
  return {
    setLight(value: boolean) {
      state.light = value
      listeners.forEach((cb) => cb())
    },
  }
}

describe('useTheme（三档：自动 / 浅色 / 深色）', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    stubMatchMedia(false)
  })

  it('默认是 auto，并按系统解析（系统深色 → dark）', () => {
    expect(initTheme()).toBe('auto')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('auto 模式下跟随系统（系统浅色 → light）', () => {
    stubMatchMedia(true)
    expect(initTheme()).toBe('auto')
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('auto 模式下系统切换时页面实时跟随', () => {
    const media = stubMatchMedia(false)
    initTheme()
    expect(document.documentElement.dataset.theme).toBe('dark')

    media.setLight(true)
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('手动选 light/dark 后不再被系统覆盖', () => {
    const media = stubMatchMedia(false)
    applyTheme('light')
    const before = document.documentElement.dataset.theme
    media.setLight(false)
    expect(document.documentElement.dataset.theme).toBe(before)
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('存过的偏好优先于系统（存 dark，系统浅色也保持 dark）', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    stubMatchMedia(true)
    expect(initTheme()).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('三档循环：auto → light → dark → auto，并持久化', () => {
    applyTheme('auto')
    expect(cycleTheme()).toBe('light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')

    expect(cycleTheme()).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')

    expect(cycleTheme()).toBe('auto')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('auto')
  })

  it('resolveTheme：auto 看系统，light/dark 原样', () => {
    stubMatchMedia(true)
    expect(resolveTheme('auto')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
  })

  it('非法存储值 → 回落到 auto', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'rainbow')
    stubMatchMedia(true)
    expect(initTheme()).toBe('auto')
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('useTheme 暴露 preference 与 theme（偏好 vs 实际生效）', () => {
    const { preference, theme, setTheme } = useTheme()
    setTheme('auto')
    expect(preference.value).toBe('auto')
    expect(['light', 'dark']).toContain(theme.value)
  })
})
