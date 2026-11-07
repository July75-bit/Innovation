<script setup lang="ts">
/**
 * 应用外壳（界面设计层）：
 * - 桌面端 = 左侧栏（品牌 + 导航 + 账户概览 + 连接状态 + 合规）+ 右主区（内容）；
 * - ≤960px = 顶栏 + 抽屉导航（A4 响应式保留），合规声明回页面底部。
 * 余额/总资产始终从后端 GET /api/account 拉取（交易后由页面触发 refreshAccount）。
 * 连接徽标走 GET /api/health（day1 验收项：页面显示"连接成功：<service>"）。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { money } from './utils/format'
import { refreshAccount, useAccount } from './composables/useAccount'
import { checkBackendHealth, useBackendHealth } from './composables/useBackendHealth'

const { account } = useAccount()

/** 响应式：≤960px 时导航收进汉堡按钮，路由切换后自动收起 */
const navOpen = ref(false)
const route = useRoute()
watch(
  () => route.path,
  () => (navOpen.value = false),
)

const { service: backend } = useBackendHealth()

const healthText = computed(() => {
  if (backend.value === null) return '检测后端连接…'
  if (backend.value === false) return '后端未连接'
  return `连接成功：${backend.value}`
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
  <!-- CS2 氛围背景（纯装饰）：雷达网格 + 红色氛围光 -->
  <div class="backdrop" aria-hidden="true"></div>

  <div class="shell">
    <!-- ===== 侧栏（桌面端）/ 抽屉（移动端） ===== -->
    <aside :class="['sidebar', { open: navOpen }]">
      <RouterLink to="/" class="brand">
        <span class="brand-mark" aria-hidden="true"></span>
        PlayerStock<span class="sub">虚拟选手股</span>
      </RouterLink>

      <nav :class="{ open: navOpen }" aria-label="主导航">
        <RouterLink to="/" class="nav-item">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 13h12M4 13V8m4 5V4m4 9v-6" /></svg>
          市场
        </RouterLink>
        <RouterLink to="/positions" class="nav-item">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 5.5 8 3l6 2.5L8 8 2 5.5Zm0 3L8 11l6-2.5M2 11 8 13.5 14 11" /></svg>
          持仓
        </RouterLink>
        <RouterLink to="/trades" class="nav-item">
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 4h10M3 8h10M3 12h6" /></svg>
          交易记录
        </RouterLink>
      </nav>

      <!-- 账户概览：系统状态可见——余额/总资产/收益常驻侧栏 -->
      <div class="account-card" v-if="account">
        <div class="acct-row">
          <span>余额（虚拟币）</span>
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
        <span class="sk sk-line"></span><span class="sk sk-line"></span><span class="sk sk-line"></span>
      </div>

      <div :class="['health', backend === null ? 'checking' : backend === false ? 'bad' : 'good']">
        <i class="h-dot" aria-hidden="true"></i>{{ healthText }}
      </div>

      <p class="side-note">
        本项目为课程作品：全程虚拟币，不可充值 / 提现 / 兑换；选手信息与价格评分均为模拟数据，与
        Valve、HLTV 及相关俱乐部无关联，不构成投资建议。
      </p>
    </aside>

    <!-- ===== 移动端顶栏 ===== -->
    <header class="topbar">
      <RouterLink to="/" class="brand brand-sm">
        <span class="brand-mark" aria-hidden="true"></span>PlayerStock
      </RouterLink>
      <div class="balance" v-if="account">
        余额 <strong>{{ money(account.balance) }}</strong>
      </div>
      <button
        class="menu-toggle"
        type="button"
        :aria-expanded="navOpen"
        aria-label="打开导航菜单"
        @click="navOpen = !navOpen"
      >
        {{ navOpen ? '关闭菜单' : '菜单' }}
      </button>
    </header>

    <main class="content">
      <RouterView />
    </main>


  </div>

  <!-- 抽屉遮罩（移动端） -->
  <div v-if="navOpen" class="scrim" @click="navOpen = false"></div>
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

/* ===== 侧栏 ===== */
.sidebar {
  grid-area: sidebar;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-3);
  background: var(--surface);
  border-right: 1px solid var(--border);
  overflow-y: auto;
}
.brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 800;
  font-size: var(--fs-h3);
  color: var(--text);
  text-decoration: none;
  padding: var(--space-1) var(--space-2);
}
.brand .sub {
  font-weight: 400;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.brand-mark {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 10px var(--accent);
  flex-shrink: 0;
}

nav {
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
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.nav-item.router-link-active {
  color: var(--text);
  font-weight: 700;
  background: var(--up-bg);
  border-left-color: var(--accent);
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
  color: var(--up);
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
  color: var(--up);
  background: var(--up-bg);
}
.health.checking {
  color: var(--muted);
}

.side-note {
  margin: auto 0 0;
  padding: var(--space-3);
  font-size: var(--fs-cap);
  color: var(--muted);
  border-top: 1px solid var(--border);
  line-height: 1.5;
}

/* ===== 移动端顶栏（桌面隐藏） ===== */
.topbar {
  grid-area: topbar;
  display: none;
  align-items: center;
  gap: var(--space-3);
  padding: 10px 14px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
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
.menu-toggle {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text);
  padding: 6px 10px;
  font-size: var(--fs-aux);
  cursor: pointer;
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
    border-right: 1px solid var(--border);
    box-shadow: var(--shadow-2);
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
  }

}

/* ===== CS2 氛围背景层：雷达网格 + 氛围光 ===== */
.backdrop {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(55% 42% at 50% 0%, rgba(229, 72, 77, 0.09), transparent 70%),
    repeating-linear-gradient(0deg, transparent 0 39px, rgba(255, 255, 255, 0.025) 39px 40px),
    repeating-linear-gradient(90deg, transparent 0 39px, rgba(255, 255, 255, 0.025) 39px 40px);
}
</style>