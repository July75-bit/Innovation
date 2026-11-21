/**
 * 移动端左右滑动切换底部 4 个 Tab。
 *
 * 只做一件事：在页面上横向滑（左滑=下一个，右滑=上一个），路由里 push 到相邻 Tab。
 * 不接管纵向滚动、不接管弹窗/抽屉/下拉/图表的横向手势。
 */
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/** 底部 Tab 的顺序：与 UiBottomTab 保持一致 */
export const TAB_ORDER = ['market', 'schedule', 'positions', 'trades'] as const

/** 路由名 → 路径（market 是 "/"） */
export const TAB_PATHS: Record<(typeof TAB_ORDER)[number], string> = {
  market: '/',
  schedule: '/schedule',
  positions: '/positions',
  trades: '/trades',
}

/** 这些元素上的横滑不当作切页：弹窗/抽屉/输入框/自绘下拉/图表等 */
export const SWIPE_IGNORE_SELECTOR = [
  '[role="dialog"]',
  '[role="listbox"]',
  'input',
  'textarea',
  'select',
  '[contenteditable="true"]',
  '[data-no-swipe]',
].join(',')

/**
 * 根据滑动距离算出目标路径；不满足条件返回 null。
 * - 水平位移太小，或纵向明显大于横向 → 不算切页；
 * - 当前路由不在 4 个 Tab 里（详情页/我的/登录页…）→ 不切；
 * - 已经在第一个/最后一个 → 不越界。
 */
export function swipeTarget(
  currentName: unknown,
  dx: number,
  dy: number,
  threshold = 56,
): string | null {
  if (Math.abs(dx) < threshold) return null
  if (Math.abs(dx) < Math.abs(dy) * 1.2) return null
  const index = TAB_ORDER.indexOf(currentName as (typeof TAB_ORDER)[number])
  if (index < 0) return null
  const next = dx < 0 ? index + 1 : index - 1
  if (next < 0 || next >= TAB_ORDER.length) return null
  return TAB_PATHS[TAB_ORDER[next]!]
}

/** 祖先里是否有横向可滚动区域（例如赛程的轮次横滑条），有就不切页 */
function hasHorizontalScroller(node: Element): boolean {
  let el: Element | null = node
  while (el && el !== document.documentElement) {
    const style = window.getComputedStyle(el)
    const overflowX = style.overflowX
    if ((overflowX === 'auto' || overflowX === 'scroll') && el.scrollWidth > el.clientWidth + 4) {
      return true
    }
    el = el.parentElement
  }
  return false
}

/** 触摸起点是否应当忽略 */
export function shouldIgnoreSwipe(target: EventTarget | null): boolean {
  const el = target as Element | null
  if (!el || typeof el.closest !== 'function') return false
  if (el.closest(SWIPE_IGNORE_SELECTOR)) return true
  return hasHorizontalScroller(el)
}

export interface SwipeNavOptions {
  /** 最小水平位移（px），默认 56 */
  threshold?: number
  /** 只在窄屏启用，默认 960（与底部 Tab 的断点一致） */
  maxWidth?: number
}

export function useSwipeNav(options: SwipeNavOptions = {}): void {
  const route = useRoute()
  const router = useRouter()
  const threshold = options.threshold ?? 56
  const maxWidth = options.maxWidth ?? 960

  let startX = 0
  let startY = 0
  let tracking = false

  function reset(): void {
    tracking = false
  }

  function onTouchStart(event: TouchEvent): void {
    if (typeof window === 'undefined' || window.innerWidth > maxWidth) {
      tracking = false
      return
    }
    if (event.touches.length !== 1 || shouldIgnoreSwipe(event.target)) {
      tracking = false
      return
    }
    const touch = event.touches[0]
    if (!touch) {
      tracking = false
      return
    }
    startX = touch.clientX
    startY = touch.clientY
    tracking = true
  }

  function onTouchEnd(event: TouchEvent): void {
    if (!tracking) return
    tracking = false
    const touch = event.changedTouches[0]
    if (!touch) return
    const target = swipeTarget(route.name, touch.clientX - startX, touch.clientY - startY, threshold)
    if (target) void router.push(target)
  }

  onMounted(() => {
    document.addEventListener('touchstart', onTouchStart, { passive: true })
    document.addEventListener('touchend', onTouchEnd)
    document.addEventListener('touchcancel', reset)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('touchstart', onTouchStart)
    document.removeEventListener('touchend', onTouchEnd)
    document.removeEventListener('touchcancel', reset)
  })
}
