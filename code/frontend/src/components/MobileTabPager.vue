<script setup lang="ts">
/**
 * 移动端四页横向滑动画廊。
 *
 * 四个主页面（市场/赛程/持仓/流水）并排挂载在一条横向滚动容器里，
 * 手指拖动时当前页与下一页同时可见（scroll-snap），松手吸附后同步 URL。
 * 桌面端不渲染本组件，仍用 RouterView。
 */
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { nearestTabIndex, pathForTabIndex, TAB_PATHS, tabIndexForPath } from '../core/tabPager'

const pages = [
  { key: 'market', path: TAB_PATHS.market, component: defineAsyncComponent(() => import('../views/MarketView.vue')) },
  { key: 'schedule', path: TAB_PATHS.schedule, component: defineAsyncComponent(() => import('../views/ScheduleView.vue')) },
  { key: 'positions', path: TAB_PATHS.positions, component: defineAsyncComponent(() => import('../views/PositionsView.vue')) },
  { key: 'trades', path: TAB_PATHS.trades, component: defineAsyncComponent(() => import('../views/TradesView.vue')) },
]

const route = useRoute()
const router = useRouter()
const scroller = ref<HTMLElement | null>(null)
const activeIndex = computed(() => tabIndexForPath(route.path))

let settleTimer: number | undefined
let programmaticTimer: number | undefined
let syncing = false

function pageWidth(): number {
  return scroller.value?.clientWidth ?? 0
}

function scrollToIndex(index: number, smooth: boolean): void {
  const el = scroller.value
  if (!el || index < 0) return
  const left = pageWidth() * index
  if (Math.abs(el.scrollLeft - left) < 2) return
  syncing = true
  el.scrollTo({ left, behavior: smooth ? 'smooth' : 'auto' })
  window.clearTimeout(programmaticTimer)
  programmaticTimer = window.setTimeout(
    () => {
      syncing = false
    },
    smooth ? 420 : 40,
  )
}

// 点底部 Tab / 程序化换页：滚到对应页
watch(
  activeIndex,
  (index) => {
    if (index < 0) return
    void nextTick(() => scrollToIndex(index, true))
  },
  { immediate: true },
)

// 手指滑完松手：吸附到最近一页，并把 URL 同步过去（replace，不堆历史）
function onScroll(): void {
  const el = scroller.value
  if (!el || syncing) return
  window.clearTimeout(settleTimer)
  settleTimer = window.setTimeout(() => {
    const index = nearestTabIndex(el.scrollLeft, el.clientWidth)
    if (index < 0 || index === activeIndex.value) return
    const path = pathForTabIndex(index)
    if (path) void router.replace(path)
  }, 140)
}

onMounted(() => {
  // 首屏直接定位到当前页，不要出现从第一页滑过去的动画
  requestAnimationFrame(() => scrollToIndex(activeIndex.value, false))
})

onBeforeUnmount(() => {
  window.clearTimeout(settleTimer)
  window.clearTimeout(programmaticTimer)
})
</script>

<template>
  <div
    ref="scroller"
    class="tab-pager"
    role="region"
    aria-label="市场、赛程、持仓、流水（左右滑动切换）"
    @scroll.passive="onScroll"
  >
    <section
      v-for="(page, index) in pages"
      :key="page.key"
      class="tab-pager__pane"
      :inert="index !== activeIndex"
      :aria-label="page.key"
    >
      <component :is="page.component" />
    </section>
  </div>
</template>

<style scoped>
.tab-pager {
  display: flex;
  width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  scroll-snap-type: x mandatory;
  overscroll-behavior-x: contain;
  scrollbar-width: none;
  align-items: flex-start;
}
.tab-pager::-webkit-scrollbar {
  display: none;
}
.tab-pager__pane {
  flex: 0 0 100%;
  min-width: 0;
  scroll-snap-align: start;
  scroll-snap-stop: always;
}
</style>
