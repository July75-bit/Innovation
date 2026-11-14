/**
 * 主题（**自动跟随系统** / 浅色 / 深色）—— 全站唯一开关。
 *
 * 三种偏好（`ThemePreference`）：
 *   - `auto`（默认）：跟随操作系统 `prefers-color-scheme`，系统切换时**实时**跟着变；
 *   - `light` / `dark`：用户明确指定，不再被系统覆盖。
 *
 * 设计要点：
 *   1) 样式只靠 `<html data-theme="light|dark">`（见 `tokens.css`），组件不写任何模式判断——
 *      所以"自动"在 CSS 层面不存在，必须由 JS 把 auto 解析成 light/dark 再写进 `data-theme`；
 *   2) 首屏不能闪：`index.html` 内联脚本在 CSS 之前用同一 storage key 先算一次；
 *   3) 用户选择持久化（localStorage）；存的是**偏好**（auto/light/dark），不是解析后的结果。
 *
 * 用法：const { preference, theme, setTheme, cycleTheme, toggleTheme } = useTheme()
 */
import { ref } from 'vue'

/** 用户偏好：自动 / 浅色 / 深色 */
export type ThemePreference = 'auto' | 'light' | 'dark'
/** 实际生效的模式（auto 解析后的结果） */
export type ThemeMode = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'playerstock.theme.v1'

/** 用户偏好（默认 auto：跟随系统） */
const preference = ref<ThemePreference>('auto')
/** 实际渲染的模式，供 UI 显示"当前是深还是浅" */
const theme = ref<ThemeMode>('dark')

let mediaQuery: MediaQueryList | null = null
let mediaBound = false

/** 系统主题变化时的回调（引用稳定，便于解绑） */
function onSystemThemeChange(): void {
  if (preference.value !== 'auto') return
  const next = resolveTheme('auto')
  theme.value = next
  if (typeof document !== 'undefined') document.documentElement.dataset.theme = next
}

function readStored(): ThemePreference | null {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY)
    return value === 'auto' || value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

function systemPrefersLight(): boolean {
  try {
    return window.matchMedia('(prefers-color-scheme: light)').matches
  } catch {
    return false
  }
}

/** 把偏好解析成实际模式：auto → 看系统，其余原样 */
export function resolveTheme(pref: ThemePreference): ThemeMode {
  if (pref === 'auto') return systemPrefersLight() ? 'light' : 'dark'
  return pref
}

/**
 * auto 模式下监听系统变化；**每次 applyTheme 都会核对一次**：
 * 若 `matchMedia` 返回的对象变了（浏览器/测试环境切换），先解绑旧的再绑新的，避免监听泄漏或失效。
 */
function bindSystemListener(): void {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
  try {
    const current = window.matchMedia('(prefers-color-scheme: light)')
    if (mediaBound && mediaQuery === current) return
    mediaQuery?.removeEventListener?.('change', onSystemThemeChange)
    current.addEventListener?.('change', onSystemThemeChange)
    mediaQuery = current
    mediaBound = true
  } catch {
    /* 老浏览器没有 addEventListener：退化为"下次打开才跟随"，不影响当前显示 */
  }
}

/** 应用偏好：写 `<html data-theme>` + 记住选择 */
export function applyTheme(pref: ThemePreference): void {
  preference.value = pref
  theme.value = resolveTheme(pref)
  if (typeof document !== 'undefined') document.documentElement.dataset.theme = theme.value
  try {
    localStorage.setItem(THEME_STORAGE_KEY, pref)
  } catch {
    /* 隐私模式存不下：只影响"下次打开是否记得"，不影响当前显示 */
  }
  bindSystemListener()
}

/** 启动时调用一次：已存偏好 > auto（默认跟随系统） */
export function initTheme(): ThemePreference {
  const stored = readStored()
  const pref: ThemePreference = stored ?? 'auto'
  applyTheme(pref)
  return pref
}

/** 循环切换：auto → light → dark → auto（按钮点一下换一档） */
export function cycleTheme(): ThemePreference {
  const order: ThemePreference[] = ['auto', 'light', 'dark']
  const next = order[(order.indexOf(preference.value) + 1) % order.length] ?? 'auto'
  applyTheme(next)
  return next
}

export function useTheme() {
  return {
    /** 用户偏好（auto/light/dark），用于显示"自动/浅色/深色" */
    preference,
    /** 实际生效的 light/dark */
    theme,
    setTheme: applyTheme,
    cycleTheme,
    /** 兼容旧调用：等同 cycleTheme（以前只有两档） */
    toggleTheme: cycleTheme,
  }
}
