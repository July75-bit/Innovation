<script setup lang="ts">
/**
 * 白话导读：全站唯一的"外壳"页面——侧栏、导航、账户卡片、后端连接徽标都在这里，
 * 中间的 <RouterView> 才是当前 URL 对应页面的出口（市场/详情/持仓/流水都渲染在那一块）。
 *
 * 一个 .vue 文件固定三段：<script setup> 写逻辑（TS）、<template> 写结构（HTML）、<style scoped> 写样式（CSS）。
 * scoped 的意思是"这里的样式只管本组件"，不会污染别的页面。
 *
 * 本文件里的关键逻辑：
 *   - 挂载时(onMounted)拉一次余额 + 检测后端；
 *   - ≤960px 时侧栏变成抽屉（CSS 媒体查询 + navOpen 控制）；
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
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { money } from './utils/format'
import { refreshAccount, useAccount } from './composables/useAccount'
import { checkBackendHealth, useBackendHealth } from './composables/useBackendHealth'
import DeleteAccountDialog from './components/DeleteAccountDialog.vue'
import UiBottomTab from './components/ui/UiBottomTab.vue'
import type { UiTabItem } from './components/ui/UiBottomTab.vue'
import { useAuth } from './composables/useAuth'
import { useTheme } from './composables/useTheme'

const { account } = useAccount()

/** 主题：浅色/深色双模式（令牌在 tokens.css；选择记在 localStorage） */
const { theme, toggleTheme } = useTheme()
const themeActionLabel = computed(() => (theme.value === 'light' ? '切到深色模式' : '切到浅色模式'))

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
  const hit = Object.entries(TAB_ROUTES).find(([, path]) => path === route.path)
  return hit ? hit[0] : 'market'
})
function onTabSelect(key: string): void {
  const path = TAB_ROUTES[key]
  if (path) void router.push(path)
}

/** 响应式：≤960px 时导航收进汉堡按钮，路由切换后自动收起 */
const navOpen = ref(false)
const route = useRoute()
watch(
  () => route.path,
  () => (navOpen.value = false),
)

const { currentUser, accountLabel: accountKind, isLoggedIn, logout } = useAuth()
const router = useRouter()

/** 桌面玻璃顶栏的页面标题（来自路由 meta.title；必须放在 useRoute/useRouter 之后——
    immediate watch 会在 setup 阶段立刻执行，早于 const route 声明会报 TDZ） */
const pageTitle = computed(() => route.meta.title ?? '选手市场')
watch(
  () => route.meta.title,
  (title) => {
    if (typeof document !== 'undefined') {
      document.title = title ? `${title} · PlayerStock` : 'PlayerStock · 虚拟选手股交易模拟'
    }
  },
  { immediate: true },
)

/** 删除账号弹窗：只对私人账号开放（公共演示账户不属于任何个人，见契约 §4.16） */
const deleteOpen = ref(false)

/**
 * 删除成功后：弹窗内部已经清掉会话，这里只负责把人送回登录页，
 * 并用 ?deleted=1 让登录页显示一句结果说明（不带 message 进 query：
 * 后端回报的行数已经打在控制台，URL 里塞长文本既难看又会被收藏成怪链接）。
 */
async function onAccountDeleted(): Promise<void> {
  await router.push({ name: 'auth', query: { deleted: '1' } })
}

/** 登录 / 注册页用独立全屏布局，外壳（侧栏 + 顶栏 + 氛围背景）在这页不渲染 */
const isAuthPage = computed(() => route.name === 'auth')

/** 私人账户只有用户名（注册不收昵称/邮箱），侧栏就用它；头像取首字母，比引一套图标库划算 */
const displayName = computed(() => currentUser.value?.nickname ?? '访客')
const userInitial = computed(() => displayName.value.charAt(0).toUpperCase())

/**
 * 侧栏账号按钮：私人账户 = 退出（撤销服务端令牌），访客 = 放弃访客态去登录页。
 * 两种情况都先清会话再跳 /auth——不清的话守卫会把"已登录"的用户从 /auth 弹回市场页。
 */
async function onAccountAction(): Promise<void> {
  await logout()
  await router.push({ name: 'auth' })
}

const { service: backend } = useBackendHealth()

const healthText = computed(() => {
  if (backend.value === null) return '检测后端连接…'
  if (backend.value === false) return '后端未连接'
  return '服务正常'
})

/** 总收益 = 总资产 - 初始本金（后端字段，前端只做展示计算） */
const profit = computed(() =>
  account.value ? account.value.total_asset - account.value.initial_balance : null,
)

onMounted(() => {
  checkBackendHealth()
  refreshAccount().catch(() => {
    /* 后端未启动时侧栏显示占位即可，页面各自有错误提示 */
  })
})
</script>

<template>
  <!-- 登录 / 注册页自带全屏 CS2 背景，不套侧栏外壳 -->
  <RouterView v-if="isAuthPage" />

  <template v-else>
    <!-- CS2 氛围背景（纯装饰）：雷达网格 + 红色氛围光 -->
    <div class="backdrop" aria-hidden="true"></div>

    <div class="shell">
      <!-- ===== 侧栏（桌面端）/ 抽屉（移动端） =====
           材质层：桌面端是玻璃壳（导航属于材质层）；≤960px 的抽屉是实色 sheet——
           抽屉占屏 78vw × 100dvh，玻璃面积会直接冲破 30% 配额，且里面是文字密集区。 -->
      <aside :class="['sidebar', 'glass', 'glass--nav', { open: navOpen }]">
        <RouterLink to="/" class="brand">
          <span class="brand-mark" aria-hidden="true"></span>
          PlayerStock<span class="sub">虚拟选手股</span>
        </RouterLink>

        <nav :class="{ open: navOpen }" aria-label="主导航">
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
        </nav>

        <!-- 当前身份：私人账户（令牌）/ 公共演示账户（访客）/ 未登录 -->
        <div class="user-card">
          <span class="avatar" aria-hidden="true">{{ userInitial }}</span>
          <span class="who">
            <strong>{{ displayName }}</strong>
            <small>{{ accountKind }}</small>
          </span>
          <button type="button" class="acct-action" @click="onAccountAction">
            {{ currentUser ? '退出' : '登录' }}
          </button>
        </div>

        <!-- 删除账号：只有私人账户能删，且要口令二次确认（契约 §4.16） -->
        <button v-if="isLoggedIn" type="button" class="danger-link" @click="deleteOpen = true">
          删除账号
        </button>

        <!-- 账户概览：系统状态可见——余额/总资产/收益常驻侧栏 -->
        <div class="account-card" v-if="account">
          <div class="acct-row">
            <span>余额（信用点）</span>
            <strong>{{ money(account.balance) }}</strong>
          </div>
          <div class="acct-row">
            <span>总资产</span>
            <strong>{{ money(account.total_asset) }}</strong>
          </div>
          <div class="acct-row">
            <span>总收益</span>
            <strong :class="(profit ?? 0) > 0 ? 'up' : (profit ?? 0) < 0 ? 'down' : 'flat'">
              {{ profit === null ? '—' : (profit >= 0 ? '+' : '') + money(profit) }}
            </strong>
          </div>
        </div>
        <div class="account-card placeholder" v-else aria-busy="true">
          <span class="sk sk-line"></span><span class="sk sk-line"></span
          ><span class="sk sk-line"></span>
        </div>

        <div
          :class="['health', backend === null ? 'checking' : backend === false ? 'bad' : 'good']"
        >
          <i class="h-dot" aria-hidden="true"></i>{{ healthText }}
        </div>

        <!-- 主题切换：浅色/深色双模式（材质层之外的普通控件，44px 点击区） -->
        <button
          type="button"
          class="theme-toggle"
          :aria-label="themeActionLabel"
          :title="themeActionLabel"
          @click="toggleTheme"
        >
          <svg v-if="theme === 'light'" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M9.5 2.5a5.5 5.5 0 1 0 4 9.2 6 6 0 0 1-4-9.2Z" />
          </svg>
          <svg v-else viewBox="0 0 16 16" aria-hidden="true">
            <circle cx="8" cy="8" r="3" />
            <path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4" />
          </svg>
          <span>{{ theme === 'light' ? '深色' : '浅色' }}</span>
        </button>

        <p class="side-note">
          本项目为课程作品：全程信用点，不可充值 / 提现 / 兑换；选手信息与价格评分均为模拟数据，与
          Valve、HLTV 及相关俱乐部无关联，不构成投资建议。
        </p>
      </aside>

      <!-- ===== 顶栏（材质层：玻璃）=====
           桌面：fixed 在内容列上方，页面内容从它下面滚过 → 真模糊（这是桌面端唯一"有东西可糊"的位置）
           移动：sticky 在页面顶部，内容同样从下面滚过 -->
      <header class="topbar glass glass--nav">
        <div class="topbar__title only-desktop">
          <span class="topbar__crumb">PlayerStock</span>
          <h1 class="topbar__h">{{ pageTitle }}</h1>
        </div>
        <RouterLink to="/" class="brand brand-sm only-mobile">
          <span class="brand-mark" aria-hidden="true"></span>PlayerStock
        </RouterLink>

        <div class="topbar__right">
          <span
            class="topbar__health only-desktop"
            :class="backend === null ? 'checking' : backend === false ? 'bad' : 'good'"
          >
            <i class="h-dot" aria-hidden="true"></i>{{ healthText }}
          </span>
          <div class="balance" v-if="account">
            余额 <strong>{{ money(account.balance) }}</strong>
          </div>
          <button
            class="theme-toggle topbar-theme"
            type="button"
            :aria-label="themeActionLabel"
            :title="themeActionLabel"
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
          <button
            class="menu-toggle only-mobile"
            type="button"
            :aria-expanded="navOpen"
            aria-label="打开导航菜单"
            @click="navOpen = !navOpen"
          >
            {{ navOpen ? '关闭菜单' : '菜单' }}
          </button>
        </div>
      </header>

      <main class="content">
        <RouterView />
      </main>

      <!-- 移动端底部 Tab（材质层：玻璃；≤960px 显示） -->
      <UiBottomTab :model-value="activeTab" :items="tabItems" @select="onTabSelect" />
    </div>

    <!-- 抽屉遮罩（移动端） -->
    <div v-if="navOpen" class="scrim" @click="navOpen = false"></div>

    <!-- 删除账号确认弹窗（Teleport 到 body，不受侧栏 / 抽屉布局影响） -->
    <!--
      这里故意不写 v-if="currentUser"：删除成功时 useAuth 会清会话，
      currentUser 立刻变 null，组件会在 emit('deleted') 之前被卸载，父层就再也收不到通知
      （实测踩过：账号删掉了但页面停在市场页）。组件自己按 open 控制渲染。
    -->
    <DeleteAccountDialog
      v-model="deleteOpen"
      :nickname="currentUser?.nickname ?? ''"
      @deleted="onAccountDeleted"
    />
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
  gap: var(--space-4);
  padding: var(--space-4) var(--space-3);
  /* 底色/模糊由全局 .glass 提供；这里只留"靠边一侧"的描边，避免玻璃四周都描边显得像卡片 */
  border: 0;
  border-right: 1px solid var(--glass-border);
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
  border-radius: var(--radius-sm);
  border-left: 2px solid transparent;
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
.nav-item.router-link-active {
  color: var(--text);
  font-weight: 600;
  background: var(--surface-3);
  border-left-color: var(--accent-text);
}

/* 账户概览卡片 */
.account-card {
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.acct-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  color: var(--muted);
}
.acct-row strong {
  color: var(--text);
  font-size: var(--fs-h3);
  font-variant-numeric: tabular-nums;
}
.acct-row strong.up {
  color: var(--up-text);
}
.acct-row strong.down {
  color: var(--down);
}
.acct-row strong.flat {
  color: var(--muted);
}
.account-card.placeholder .sk-line {
  height: 14px;
  border-radius: 4px;
  background: var(--neutral-bg);
  animation: sk-pulse 1.2s ease-in-out infinite;
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
.h-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
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

.side-note {
  margin: auto 0 0;
  padding: var(--space-3);
  font-size: var(--fs-aux);
  color: var(--muted);
  border-top: 1px solid var(--border);
  line-height: 1.5;
}

/* 主题切换：普通控件（内容层），44px 点击区，图标 + 文字双通道 */
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: 44px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--muted);
  font-family: inherit;
  font-size: var(--fs-cap);
  cursor: pointer;
}
.theme-toggle:hover {
  color: var(--text);
  border-color: var(--border-strong);
  background: var(--neutral-bg);
}
.theme-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.theme-toggle svg {
  width: var(--icon-sm);
  height: var(--icon-sm);
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.topbar-theme {
  min-height: 36px;
  padding: 0 var(--space-2);
}
@media (max-width: 960px) {
  .topbar-theme span {
    display: none; /* 窄屏只留图标，省空间 */
  }
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
.balance {
  margin-left: auto;
  font-size: var(--fs-aux);
  color: var(--muted);
  white-space: nowrap;
}
.balance strong {
  color: var(--text);
  font-size: var(--fs-h3);
  font-variant-numeric: tabular-nums;
}
@media (max-width: 420px) {
  .balance {
    font-size: var(--fs-cap);
  }
  .balance strong {
    font-size: var(--fs-body);
  }
}
.menu-toggle {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 6px 10px;
  font-size: var(--fs-aux);
  cursor: pointer;
}

/* ===== 桌面（≥961px）：顶栏 fixed 在内容列上方，内容从它下面滚过 ===== */
@media (min-width: 961px) {
  .topbar {
    display: flex;
    position: fixed;
    top: 0;
    left: var(--layout-sidebar-width);
    right: 0;
    height: var(--layout-topbar-height);
    padding: 0 var(--space-5);
    border: 0;
    border-bottom: 1px solid var(--glass-border);
    z-index: var(--z-nav);
  }
  .topbar__title {
    display: flex;
    align-items: baseline;
    gap: var(--space-2);
    min-width: 0;
  }
  .topbar__crumb {
    font-size: var(--fs-cap);
    color: var(--muted);
    white-space: nowrap;
  }
  .topbar__h {
    margin: 0;
    font-size: var(--fs-h3);
    font-weight: 600;
    color: var(--text);
    white-space: nowrap;
  }
  .topbar__right .balance {
    margin-left: 0;
  }
  .topbar__right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }
  .topbar__health {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: var(--fs-cap);
    color: var(--muted);
  }
  .topbar__health.good {
    color: var(--down);
  }
  .topbar__health.bad {
    color: var(--up-text);
  }
  /* 桌面内容区给 fixed 顶栏让出高度（内容从顶栏下面滚过）
     用 .shell .content 提高优先级：基础 .content 规则在文件更后面 */
  .shell .content {
    padding-top: calc(var(--layout-topbar-height) + var(--space-5));
  }
}
.only-mobile {
  display: none;
}

/* ===== 主区 ===== */
.content {
  grid-area: content;
  padding: var(--space-5);
  width: 100%;
  /* 宽屏修复：主区在侧栏右侧的剩余空间内居中，避免右侧大片空白 */
  max-width: 1280px;
  margin-inline: auto;
}

/* 遮罩（仅移动端抽屉用） */
.scrim {
  display: none;
}

/* ===== ≤960px：侧栏转抽屉，顶栏出现 ===== */
@media (max-width: 960px) {
  .shell {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas:
      'topbar'
      'content';
  }
  .topbar {
    display: flex;
  }
  .only-desktop {
    display: none !important;
  }
  .only-mobile {
    display: inline-flex;
  }
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    height: 100dvh;
    width: min(78vw, 300px);
    z-index: 30;
    transform: translateX(-105%);
    transition: transform 0.2s ease;
    /* 抽屉=文字密集的浮层 sheet：实色，不用玻璃（玻璃面积 78vw×100dvh 会超配额，
       而且导航/账户/合规声明这类文本直接坐在玻璃上不可读） */
    background-color: var(--surface);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
    box-shadow: var(--shadow-2);
    border: 1px solid var(--border);
    border-radius: 0 var(--glass-radius-sheet) var(--glass-radius-sheet) 0;
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .scrim {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 25;
  }
  .content {
    padding: var(--space-4) var(--space-4) var(--space-5);
    /* 给底部玻璃 Tab 栏留出空间（12px 底距 + 56 高度 + 安全区） */
    padding-bottom: calc(96px + env(safe-area-inset-bottom, 0px));
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
.user-card {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-2);
}
.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  /* 实色主色底 + 白字：红字压在红色调底上只有 1.7:1，2026-11-14 实测不合格，改实心底 */
  background: var(--color-action);
  color: var(--color-action-text);
  font-size: var(--fs-cap);
  font-weight: 800;
  flex-shrink: 0;
}
.who {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.who strong {
  font-size: var(--fs-aux);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.who small {
  font-size: var(--fs-cap);
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.acct-action {
  margin-left: auto;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: none;
  color: var(--muted);
  font-size: var(--fs-cap);
  cursor: pointer;
  flex-shrink: 0;
}
.acct-action:hover {
  border-color: var(--accent-text);
  color: var(--accent-text);
}

/* 删除账号入口：刻意做成不起眼的文字链——低频高危操作，不该长得像主按钮 */
.danger-link {
  align-self: flex-start;
  margin-top: calc(var(--space-2) * -1);
  padding: 2px 4px;
  border: none;
  background: none;
  color: var(--muted);
  font-size: var(--fs-cap);
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}
.danger-link:hover {
  color: var(--accent-text);
}
</style>
