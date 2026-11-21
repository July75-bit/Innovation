/** 移动端四页滑动的顺序、路径与索引换算（纯函数，便于测试） */
export const TAB_ORDER = ['market', 'schedule', 'positions', 'trades'] as const

export const TAB_PATHS: Record<(typeof TAB_ORDER)[number], string> = {
  market: '/',
  schedule: '/schedule',
  positions: '/positions',
  trades: '/trades',
}

/** 路由路径 → 第几页；不是四个主页面就返回 -1 */
export function tabIndexForPath(path: string): number {
  const index = TAB_ORDER.findIndex((key) => TAB_PATHS[key] === path)
  return index
}

/** 第几页 → 路由路径；越界返回 null */
export function pathForTabIndex(index: number): string | null {
  if (index < 0 || index >= TAB_ORDER.length) return null
  return TAB_PATHS[TAB_ORDER[index]!] ?? null
}

/** 横向滚动位置 → 最近的页索引（用于松手后同步 URL） */
export function nearestTabIndex(scrollLeft: number, pageWidth: number): number {
  if (!pageWidth || pageWidth < 1) return -1
  const index = Math.round(scrollLeft / pageWidth)
  if (index < 0 || index >= TAB_ORDER.length) return -1
  return index
}
