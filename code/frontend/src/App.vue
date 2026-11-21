<script setup lang="ts">
/**
 * 白话导读：全站唯一的"外壳"页面——侧栏、导航、账户卡片、后端连接徽标都在这里，
 * 中间的 <RouterView> 才是当前 URL 对应页面的出口（市场/详情/持仓/流水都渲染在那一块）。
 *
 * 一个 .vue 文件固定三段：<script setup> 写逻辑（TS）、<template> 写结构（HTML）、<style scoped>
 写样式（CSS）。
 * scoped 的意思是"这里的样式只管本组件"，不会污染别的页面。
 *
 * 本文件里的关键逻辑：
 *   - 挂载时(onMounted)拉一次余额 + 检测后端；
 *   - ≤960px 时侧栏隐藏，移动端导航交给底部 Tab（4 项）+ 顶栏头像进「我的」；
 *   - 登录页 /auth 不套外壳，直接全屏渲染（isAuthPage）。
 */
/**
 * 应用外壳（界面设计层）：
 * - 桌面端 = 左侧栏（品牌 + 导航 + 账户概览 + 连接状态 + 合规）+ 右主区（内容）；
 * - ≤960px = 顶栏 + 抽屉导航（A4 响应式保留），合规声明回页面底部。
 * 余额/总资产始终从后端 GET /api/account 拉取（交易后由页面触发 refreshAccount）。
 * 连接徽标走 GET /api/health（day1 验收项：页面显示"连接成功：<service>"）。
 * - 登录 / 注册页（/auth）走独立全屏布局，isAuthPage 为真时不渲染侧栏与顶栏；
 * - 侧栏常驻本地账号卡片（用户名 / 本地账号或访客 / 退出），会话来自 useAuth，只存浏览器。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { checkBackendHealth, useBackendHealth } from './composables/useBackendHealth'
import { refreshAccount } from './composables/useAccount'
import UiBottomTab from './components/ui/UiBottomTab.vue'
import type { UiTabItem } from './components/ui/UiBottomTab.vue'
import { useAuth } from './composables/useAuth'
import { useTheme } from './composables/useTheme'
import MobileTabPager from './components/MobileTabPager.vue'
import { TAB_PATHS } from './core/tabPager'

/** 移动端底部 Tab：主导航的等价入口（玻璃材质层，≤960px 显示） */
const TAB_ROUTES: Record<string, string> = {
  market: '/',
  schedule: '/schedule',
  positions: '/positions',
  trades: '/trades',
}
const tabItems: UiTabItem[] = [
  { key: 'market', label: '市场', icon: 'M2 13h12M4 13V8m4 5V4m4 9v-6' },
  { key: 'schedule', label: '赛程', icon: 'M2.5 4h11v9.5h-11zM2.5 7h11M5.5 2.5V5M10.5 2.5V5' },
  { key: 'positions', label: '持仓', icon: 'M2 5.5 8 3l6 2.5L8 8 2 5.5Zm0 3L8 11l6-2.5M2 11 8 13.5 14 11' },
  { key: 'trades', label: '流水', icon: 'M3 4h10M3 8h10M3 12h6' },
]
const activeTab = computed(() => {
  if (route.path.startsWith('/players')) return 'market' // 详情页属于"市场"这条线
  if (route.path === '/me') return '' // 个人页不在底部 Tab 里，不高亮任何一项
  const hit = Object.entries(TAB_ROUTES).find(([, path]) => path === route.path)
  return hit ? hit[0] : 'market'
})
function onTabSelect(key: string): void {
  const path = TAB_ROUTES[key]
  if (path) void router.push(path)
}

const route = useRoute()

const { currentUser } = useAuth()
const router = useRouter()

/** 桌面玻璃顶栏的页面标题（来自路由 meta.title；必须放在 useRoute/useRouter 之后——
    immediate watch 会在 setup 阶段立刻执行，早于 const route 声明会报 TDZ） */
watch(
  () => route.meta.title,
  (title) => {
    if (typeof document !== 'undefined') {
      document.title = title ? `${title} · PlayerStock` : 'PlayerStock · 虚拟选手股交易模拟'
    }
  },
  { immediate: true },
)

/** 登录 / 注册页用独立全屏布局，外壳（侧栏 + 顶栏 + 氛围背景）在这页不渲染 */
const isAuthPage = computed(() => route.name === 'auth')

/** 四个主页面（市场/赛程/持仓/流水）：移动端用横向滑动容器，桌面仍走 RouterView */
const isTabRoute = computed(() => (Object.values(TAB_PATHS) as string[]).includes(route.path))

/** 是否是移动端断点（与底部 Tab / 侧栏隐藏的 960px 一致） */
const isMobile = ref(false)
let mobileQuery: MediaQueryList | null = null
function onMobileQueryChange(event: MediaQueryListEvent): void {
  isMobile.value = event.matches
}

/** 深浅色快捷开关：外壳里一键切换（/me 仍保留「自动/浅色/深色」三档偏好） */
const { theme, setTheme } = useTheme()
const themeSwitchLabel = computed(() => (theme.value === 'light' ? '深色' : '浅色'))
function toggleTheme(): void {
  setTheme(theme.value === 'light' ? 'dark' : 'light')
}

/** 移动端顶栏头像：入口指向个人页（侧栏里也有「我的」） */
const displayName = computed(() => currentUser.value?.nickname ?? '访客')
const userInitial = computed(() => displayName.value.charAt(0).toUpperCase())

const { service: backend } = useBackendHealth()

const healthText = computed(() => {
  if (backend.value === null) return '检测后端连接…'
  if (backend.value === false) return '后端未连接'
  return '服务正常'
})

/** 移动端顶栏：下滑收起、上滑出现（参考主流 App 的 hide-on-scroll 行为） */
const topbarHidden = ref(false)
let lastScrollY = 0
let scrollTicking = false

function updateTopbarVisibility(): void {
  if (window.innerWidth > 960) {
    topbarHidden.value = false
    lastScrollY = window.scrollY
    return
  }
  const y = Math.max(window.scrollY, 0)
  if (y < 24) {
    topbarHidden.value = false // 回到顶部一定显示
  } else if (y > lastScrollY + 6) {
    topbarHidden.value = true // 下滑：收起
  } else if (y < lastScrollY - 6) {
    topbarHidden.value = false // 上滑：出现
  }
  lastScrollY = y
}

function onScroll(): void {
  if (scrollTicking) return
  scrollTicking = true
  requestAnimationFrame(() => {
    updateTopbarVisibility()
    scrollTicking = false
  })
}

function onResize(): void {
  updateTopbarVisibility()
}

// 换页后回到顶部时顶栏必须可见
watch(
  () => route.path,
  () => {
    topbarHidden.value = false
    lastScrollY = window.scrollY
  },
)

onMounted(() => {
  lastScrollY = window.scrollY
  updateTopbarVisibility()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onResize)
  if (typeof window.matchMedia === 'function') {
    mobileQuery = window.matchMedia('(max-width: 960px)')
    isMobile.value = mobileQuery.matches
    mobileQuery.addEventListener('change', onMobileQueryChange)
  }
  checkBackendHealth()
  // 余额/资产是交易面板的依赖（最大可买/预估金额），外壳启动时静默拉一次；
  // 侧栏不再展示它，但也不该让详情页的交易面板缺数据。
  refreshAccount().catch(() => {
    /* 后端未启动时页面各自有错误提示 */
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onResize)
  mobileQuery?.removeEventListener('change', onMobileQueryChange)
})
</script>

<template>
  <!-- 登录 / 注册页自带全屏 CS2 背景，不套侧栏外壳 -->
  <RouterView v-if="isAuthPage" />

  <template v-else>
    <!-- 键盘用户第一个 Tab 就能跳过导航（专业站点的常规做法） -->
    <a class="skip-link" href="#main">跳到主要内容</a>
    <!-- CS2 氛围背景（纯装饰）：雷达网格 + 红色氛围光 -->
    <div class="backdrop" aria-hidden="true"></div>

    <div class="shell">
      <!-- ===== 侧栏（仅桌面端；≤960px 隐藏，移动端用底部 4 项导航 + 顶栏头像） ===== -->
      <aside class="sidebar">
        <RouterLink to="/" class="brand">
          <span class="brand-mark" aria-hidden="true"></span>
          PlayerStock<span class="sub">虚拟选手股</span>
        </RouterLink>

        <nav aria-label="主导航">
          <RouterLink to="/" class="nav-item">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M2 13h12M4 13V8m4 5V4m4 9v-6" />
            </svg>
            市场
          </RouterLink>
          <RouterLink to="/schedule" class="nav-item">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M2.5 4h11v9.5h-11zM2.5 7h11M5.5 2.5V5M10.5 2.5V5M5.5 9.5h2M9 9.5h2" />
            </svg>
            赛程
          </RouterLink>
          <RouterLink to="/positions" class="nav-item">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M2 5.5 8 3l6 2.5L8 8 2 5.5Zm0 3L8 11l6-2.5M2 11 8 13.5 14 11" />
            </svg>
            持仓
          </RouterLink>
          <RouterLink to="/trades" class="nav-item">
            <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 4h10M3 8h10M3 12h6" /></svg>
            交易记录
          </RouterLink>
          <RouterLink to="/me" class="nav-item">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <circle cx="8" cy="5.5" r="2.5" />
              <path d="M3 13.5c0-2.5 2.2-4 5-4s5 1.5 5 4" />
            </svg>
            我的
          </RouterLink>
        </nav>

        <!-- 深浅色快捷切换：常驻侧栏底部，不用再进「我的」 -->
        <button
          type="button"
          class="sidebar-theme"
          :aria-label="`切换到${themeSwitchLabel}主题`"
          :title="`切换到${themeSwitchLabel}主题`"
          @click="toggleTheme"
        >
          <svg v-if="theme === 'light'" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M9.5 2.5a5.5 5.5 0 1 0 4 9.2 6 6 0 0 1-4-9.2Z" />
          </svg>
          <svg v-else viewBox="0 0 16 16" aria-hidden="true">
            <circle cx="8" cy="8" r="3" />
            <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4" />
          </svg>
          <span>{{ themeSwitchLabel }}</span>
        </button>

      </aside>

      <!-- ===== 顶栏（移动端：品牌 + 个人头像；底部 Tab 负责导航） ===== -->
      <header :class="['topbar', { 'is-hidden': topbarHidden }]">
        <RouterLink to="/" class="brand brand-sm only-mobile">
          <span class="brand-mark" aria-hidden="true"></span>PlayerStock
        </RouterLink>

        <div class="topbar__right">
          <button
            type="button"
            class="topbar-theme only-mobile"
            :aria-label="`切换到${themeSwitchLabel}主题`"
            :title="`切换到${themeSwitchLabel}主题`"
            @click="toggleTheme"
          >
            <svg v-if="theme === 'light'" viewBox="0 0 16 16" aria-hidden="true">
              <path d="M9.5 2.5a5.5 5.5 0 1 0 4 9.2 6 6 0 0 1-4-9.2Z" />
            </svg>
            <svg v-else viewBox="0 0 16 16" aria-hidden="true">
              <circle cx="8" cy="8" r="3" />
              <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4" />
            </svg>
          </button>
          <RouterLink
            to="/me"
            class="topbar-profile only-mobile"
            :aria-label="`我的：${displayName}`"
            :title="`我的：${displayName}`"
          >
            {{ userInitial }}
          </RouterLink>
        </div>
      </header>

      <main id="main" class="content">
        <!-- 移动端四个主页面：并排挂载，滑动时相邻页同时可见，松手吸附后同步 URL -->
        <MobileTabPager v-if="isMobile && isTabRoute" />
        <RouterView v-else v-slot="{ Component, route: current }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="current.path" />
          </Transition>
        </RouterView>
        <footer class="page-foot">
          <span :class="['foot-dot', backend === null ? 'checking' : backend === false ? 'bad' : 'good']"
            ><i aria-hidden="true"></i>{{ healthText }}</span
          >
        </footer>
      </main>

      <!-- 移动端底部 Tab（材质层：玻璃；≤960px 显示） -->
      <UiBottomTab :model-value="activeTab" :items="tabItems" @select="onTabSelect" />
    </div>
  </template>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 232px minmax(0, 1fr);
  grid-template-rows: auto 1fr;
  grid-template-areas:
    'sidebar topbar'
    'sidebar content';
  min-height: 100vh;
  width: 100%;
}

/* ===== 侧栏（桌面端材质层：玻璃） ===== */
.sidebar {
  grid-area: sidebar;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  padding: var(--space-5) var(--space-4);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
}
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 700;
  font-size: var(--fs-body);
  color: var(--text);
  text-decoration: none;
  padding: var(--space-2);
  white-space: nowrap;
  overflow: hidden;
}
.brand .sub {
  font-weight: 400;
  font-size: var(--fs-cap);
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-mark {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  border: 1px solid var(--accent);
  flex-shrink: 0;
}

/* 只作用于侧栏里的主导航；全局 `nav { }` 会串到子组件的 <nav> 根节点上
   （Vue 会把父组件的 scoped 属性加到子组件根元素，导致底部 Tab 被排成竖列——2026-11-14 实测踩过） */
.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  text-decoration: none;
  font-size: var(--fs-body);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
}
.nav-item {
  transition:
    color var(--motion-fast) ease,
    background-color var(--motion-fast) ease;
}
.nav-item:hover {
  background: var(--neutral-bg);
  color: var(--text);
}
.nav-item svg {
  width: var(--icon-sm);
  height: var(--icon-sm);
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.nav-item {
  position: relative;
}
.nav-item.router-link-active {
  /* 纸感：只用文字与一条 2px 竖线表示选中，不再用彩色底 */
  color: var(--text);
  font-weight: 600;
  background: transparent;
}
.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: -8px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  border-radius: 1px;
  background: var(--color-text);
}

/* 账户概览卡片 */
.acct-row strong {
  color: var(--text);
  font-size: var(--fs-h3);
  font-variant-numeric: tabular-nums;
}
@keyframes sk-pulse {
  0%,
  100% {
    opacity: 0.35;
  }
  50% {
    opacity: 0.8;
  }
}

/* 连接状态 */
.health {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-cap);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-pill);
  background: var(--neutral-bg);
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.health.good {
  color: var(--down);
  background: var(--down-bg);
}
.health.bad {
  color: var(--up-text);
  background: var(--up-bg);
}
.health.checking {
  color: var(--muted);
}

/* 主题切换：普通控件（内容层），44px 点击区，图标 + 文字双通道 */
.sidebar-theme {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 8px;
  border: 0;
  border-top: 1px solid var(--color-border);
  background: none;
  color: var(--muted);
  font-size: var(--fs-aux);
  cursor: pointer;
  text-align: left;
}
.sidebar-theme:hover {
  color: var(--text);
}
.sidebar-theme svg {
  width: 16px;
  height: 16px;
  flex: none;
}

.topbar-theme {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--neutral-bg);
  color: var(--text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.topbar-theme:hover {
  color: var(--text);
  border-color: var(--color-border-strong);
}
.topbar-theme svg {
  width: 16px;
  height: 16px;
}

.topbar-profile {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  background: var(--neutral-bg);
  color: var(--text);
  font-size: var(--fs-aux);
  font-weight: 600;
  text-decoration: none;
}
.topbar-profile:hover {
  border-color: var(--color-border-strong);
}

/* ===== 顶栏（桌面 fixed / 移动 sticky；材质层：玻璃，内容从它下面滚过） ===== */
.topbar {
  grid-area: topbar;
  display: none;
  align-items: center;
  gap: var(--space-3);
  padding: 10px 14px;
  border: 0;
  border-bottom: 1px solid var(--glass-border);
  position: sticky;
  top: 0;
  z-index: 20;
}
.brand-sm {
  padding: 0;
}



/* ===== 桌面（≥961px）：不要顶栏，把纵向空间还给内容 ===== */
@media (min-width: 961px) {
  .topbar {
    display: none;
  }
  .topbar__right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }
  /* 桌面内容区：大留白，视线从容 */
  .shell .content {
    padding: var(--space-7) var(--space-6) var(--space-6);
  }
}
.only-mobile {
  display: none;
}

/* ===== 主区 ===== */
.content {
  grid-area: content;
  padding: var(--space-6) var(--space-5);
  width: 100%;
  max-width: var(--layout-content-max);
  margin-inline: auto;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 页脚：服务状态 + 关于（低调，不抢内容） */
.page-foot {
  margin-top: auto;
  padding-top: var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  font-size: var(--fs-cap);
  color: var(--faint);
}
.foot-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.foot-dot i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.foot-dot.good {
  color: var(--down);
}
.foot-dot.bad {
  color: var(--up-text);
}

/* ===== ≤960px：侧栏隐藏，顶栏（品牌+头像）+ 底部 4 项导航 ===== */
@media (max-width: 960px) {
  .shell {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: 1fr;
    /* 顶栏改为 fixed 覆盖层：不再占网格行，否则收起后会留下一条空白 */
    grid-template-areas: 'content';
  }
  .topbar {
    display: flex;
    /* fixed 覆盖在内容之上：实色底，内容从下面滚过不会透出文字叠字 */
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 30;
    align-items: center;
    flex-wrap: nowrap;
    gap: var(--space-2);
    min-height: 56px;
    height: auto;
    /* 顶部安全区（刘海屏） */
    padding: calc(8px + env(safe-area-inset-top, 0px)) 12px 8px;
    background: var(--color-canvas);
    border-bottom: 1px solid var(--color-border);
    transform: translateY(0);
    /* 丝滑收起/出现：与主流 App 同款 ease-out 曲线 */
    transition: transform 240ms cubic-bezier(0.22, 1, 0.36, 1);
    will-change: transform;
  }
  .topbar.is-hidden {
    transform: translateY(calc(-100% - 1px));
  }
  .topbar__right {
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: var(--space-2);
    margin-left: auto;
    min-width: 0;
  }
  .brand-sm {
    flex: none;
    min-width: 0;
  }
  .only-mobile {
    display: inline-flex;
  }
  /* 手机端不需要抽屉：导航由底部 Tab 承担，「我的」走顶栏头像 */
  .sidebar {
    display: none;
  }
  .content {
    /* 给 fixed 顶栏让出位置（56 + 安全区），换页/滚动时内容不会被遮住 */
    padding: calc(56px + env(safe-area-inset-top, 0px) + var(--space-4)) var(--space-4)
      var(--space-5);
    /* 给底部玻璃 Tab 栏留出空间（12px 底距 + 56 高度 + 安全区） */
    padding-bottom: calc(96px + env(safe-area-inset-bottom, 0px));
  }
}

@media (prefers-reduced-motion: reduce) {
  .topbar {
    transition: none;
  }
}

/* ===== CS2 氛围背景层：雷达网格 + 氛围光 ===== */
.backdrop {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
  background: transparent;
}

/* ===== 本地账号卡片（会话来自 useAuth，只存浏览器） ===== */
.who strong {
  font-size: var(--fs-aux);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 删除账号入口：刻意做成不起眼的文字链——低频高危操作，不该长得像主按钮 */

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .nav-item,
  .icon-btn svg {
    transition: none !important;
  }
}

/* 跳转链接：默认藏在视口外，键盘聚焦时才出现 */
.skip-link {
  position: fixed;
  top: var(--space-3);
  left: var(--space-3);
  z-index: calc(var(--z-modal) + 10);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  color: var(--text);
  font-size: var(--fs-aux);
  text-decoration: none;
  transform: translateY(-200%);
  transition: transform var(--motion-fast) var(--motion-ease);
}
.skip-link:focus-visible {
  transform: translateY(0);
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
</style>
