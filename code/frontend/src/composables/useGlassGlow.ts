/**
 * 液态玻璃的"液面感"：指针在玻璃上移动时，把柔和高光的位置写进 CSS 变量
 * （--glow-x / --glow-y 百分比，供 liquid-glass.css 的 .glass--interactive::after 使用）。
 *
 * 约束（与规范一致）：
 *  - 只在「有鼠标 + 精细指针」设备上启用；触屏不启用；
 *  - 尊重 prefers-reduced-motion：减少动效时完全不启用（高光保持静态 0 状态）；
 *  - 用 requestAnimationFrame 节流，只在指针位置变化时写 2 个 CSS 变量，不触发重排；
 *  - 离开玻璃时清掉变量，高光淡出（由 CSS transition 负责）。
 */
import { onBeforeUnmount } from 'vue'

export interface GlowPoint {
  x: number
  y: number
}

/** 纯函数：把指针坐标换算成元素内的百分比（0–100，越界会夹住） */
export function glowPosition(
  rect: { left: number; top: number; width: number; height: number },
  clientX: number,
  clientY: number,
): GlowPoint {
  const clamp = (v: number): number => Math.max(0, Math.min(100, v))
  if (rect.width <= 0 || rect.height <= 0) return { x: 50, y: 0 }
  return {
    x: clamp(((clientX - rect.left) / rect.width) * 100),
    y: clamp(((clientY - rect.top) / rect.height) * 100),
  }
}

const GLOW_SELECTOR = '.glass--interactive'

function canUse(): boolean {
  if (typeof window === 'undefined' || typeof document === 'undefined') return false
  try {
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    return fine && !reduceMotion
  } catch {
    return false
  }
}

/** 启动全局指针跟踪；返回清理函数（组件卸载时调用） */
export function initGlassGlow(): () => void {
  if (!canUse()) return () => {}

  let current: HTMLElement | null = null
  let raf = 0
  let lastEvent: PointerEvent | null = null

  const apply = (): void => {
    raf = 0
    const event = lastEvent
    if (!event) return
    const el = (event.target as Element | null)?.closest?.(GLOW_SELECTOR) as HTMLElement | null
    if (el !== current) {
      if (current) {
        current.style.removeProperty('--glow-x')
        current.style.removeProperty('--glow-y')
      }
      current = el
    }
    if (!current) return
    const point = glowPosition(current.getBoundingClientRect(), event.clientX, event.clientY)
    current.style.setProperty('--glow-x', `${point.x.toFixed(1)}%`)
    current.style.setProperty('--glow-y', `${point.y.toFixed(1)}%`)
  }

  const onPointerMove = (event: PointerEvent): void => {
    lastEvent = event
    if (!raf) raf = requestAnimationFrame(apply)
  }

  const onPointerLeave = (): void => {
    if (current) {
      current.style.removeProperty('--glow-x')
      current.style.removeProperty('--glow-y')
      current = null
    }
  }

  document.addEventListener('pointermove', onPointerMove, { passive: true })
  document.addEventListener('pointerleave', onPointerLeave, { passive: true })
  return () => {
    document.removeEventListener('pointermove', onPointerMove)
    document.removeEventListener('pointerleave', onPointerLeave)
    if (raf) cancelAnimationFrame(raf)
    onPointerLeave()
  }
}

/** 组合式用法：在组件 setup 里调用，卸载自动清理 */
export function useGlassGlow(): void {
  const cleanup = initGlassGlow()
  onBeforeUnmount(cleanup)
}
