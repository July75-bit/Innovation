/**
 * 主题（浅色 / 深色）—— 全站唯一开关。
 *
 * 为什么要单独一个 composable：
 *   1) 令牌切换只靠 <html data-theme="light">（见 tokens.css），组件不需要写任何模式判断；
 *   2) 首屏不能闪：index.html 里有一段同 key 的内联脚本，在 CSS 之前就把 data-theme 设好；
 *   3) 用户选择要记住（localStorage），未选择时跟随系统 prefers-color-scheme，最后兜底深色。
 *
 * 用法：const { theme, toggleTheme, setTheme } = useTheme()
 */
import { ref } from 'vue'

export type ThemeMode = 'dark' | 'light'

export const THEME_STORAGE_KEY = 'playerstock.theme.v1'

const theme = ref<ThemeMode>('dark')

function readStored(): ThemeMode | null {
  try {
    const v = localStorage.getItem(THEME_STORAGE_KEY)
    return v === 'light' || v === 'dark' ? v : null
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

/** 把模式写到 <html data-theme>（CSS 令牌据此整块切换）并记住选择 */
export function applyTheme(mode: ThemeMode): void {
  theme.value = mode
  if (typeof document !== 'undefined') document.documentElement.dataset.theme = mode
  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode)
  } catch {
    /* 隐私模式存不下：仅影响"下次打开是否记得"，不影响当前显示 */
  }
}

/** 应用启动时调用一次：已存选择 > 系统偏好 > 深色（产品默认） */
export function initTheme(): ThemeMode {
  const mode = readStored() ?? (systemPrefersLight() ? 'light' : 'dark')
  applyTheme(mode)
  return mode
}

export function useTheme() {
  return {
    theme,
    setTheme: applyTheme,
    toggleTheme: () => applyTheme(theme.value === 'light' ? 'dark' : 'light'),
  }
}
