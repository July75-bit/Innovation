/**
 * 主题（浅色/深色）测试：默认值、跟随系统、持久化、toggle 后 <html data-theme> 生效。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { THEME_STORAGE_KEY, applyTheme, initTheme, useTheme } from '../../composables/useTheme'

function stubMatchMedia(light: boolean): void {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: light && query.includes('prefers-color-scheme: light'),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    stubMatchMedia(false)
  })

  it('没有存过选择且系统是深色 → 默认深色', () => {
    expect(initTheme()).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('没有存过选择但系统是浅色 → 跟随系统', () => {
    stubMatchMedia(true)
    expect(initTheme()).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('存过选择时优先用存的值（不被系统覆盖）', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'light')
    stubMatchMedia(false)
    expect(initTheme()).toBe('light')
  })

  it('toggle 后写 <html data-theme> 并持久化', () => {
    const { theme, toggleTheme } = useTheme()
    applyTheme('dark')
    expect(theme.value).toBe('dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')

    toggleTheme()
    expect(theme.value).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')

    toggleTheme()
    expect(theme.value).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('存了非法值 → 回落到系统偏好', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'rainbow')
    stubMatchMedia(true)
    expect(initTheme()).toBe('light')
  })
})
