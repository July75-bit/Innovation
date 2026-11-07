<script setup lang="ts">
/**
 * 应用外壳：顶部导航 + 后端连接徽标 + 余额徽标 + 合规声明页脚。
 * 余额始终从后端 GET /api/account 拉取（交易后由各页面触发 refreshAccount）。
 * 连接徽标走 GET /api/health（day1 验收项：页面显示"连接成功：<service>"）。
 */
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { money } from './utils/format'
import { refreshAccount, useAccount } from './composables/useAccount'
import { checkBackendHealth, useBackendHealth } from './composables/useBackendHealth'

const { account } = useAccount()

const { service: backend } = useBackendHealth()

const healthText = computed(() => {
  if (backend.value === null) return '检测后端连接…'
  if (backend.value === false) return '后端未连接'
  return `连接成功：${backend.value}`
})

onMounted(() => {
  checkBackendHealth()
  refreshAccount().catch(() => {
    /* 后端未启动时头部不展示余额即可，页面各自有错误提示 */
  })
})
</script>

<template>
  <!-- CS2 氛围背景（纯装饰）：雷达网格 + 红色氛围光 + 警示斜纹 -->
  <div class="backdrop" aria-hidden="true"></div>
  <header class="nav">
    <div class="nav-inner">
      <RouterLink to="/" class="brand">PlayerStock <span class="sub">虚拟选手股</span></RouterLink>
      <nav>
        <RouterLink to="/">市场</RouterLink>
        <RouterLink to="/positions">持仓</RouterLink>
        <RouterLink to="/trades">交易记录</RouterLink>
      </nav>
      <span :class="['health', backend === null ? 'checking' : backend === false ? 'bad' : 'good']">
        {{ healthText }}
      </span>
      <div class="balance" v-if="account">
        余额 <strong>{{ money(account.balance) }}</strong>
      </div>
    </div>
  </header>

  <main class="content">
    <RouterView />
  </main>

  <footer class="foot">
    本项目为课程作品：全程虚拟币，不可充值 / 提现 / 兑换；选手信息与价格评分均为模拟数据，与
    Valve、HLTV 及相关俱乐部无关联，不构成投资建议。
  </footer>
</template>

<style scoped>
.nav {
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky;
  top: 0;
  z-index: 10;
}
.nav-inner {
  max-width: 1000px;
  margin: 0 auto;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.brand {
  font-weight: 800;
  font-size: 18px;
  color: var(--text);
  text-decoration: none;
}
.brand .sub {
  font-weight: 400;
  font-size: 12px;
  color: var(--muted);
  margin-left: 4px;
}
nav {
  display: flex;
  gap: 16px;
  flex: 1;
}
nav a {
  color: var(--muted);
  text-decoration: none;
  font-size: 15px;
  padding: 4px 2px;
}
nav a.router-link-active {
  color: var(--text);
  font-weight: 700;
  border-bottom: 2px solid var(--up);
}
.health {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}
.health.good {
  background: var(--down-bg);
  color: var(--down);
}
.health.bad {
  background: rgba(211, 58, 58, 0.12);
  color: var(--up);
}
.health.checking {
  background: rgba(127, 127, 127, 0.12);
  color: var(--muted);
}
.balance {
  font-size: 14px;
  color: var(--muted);
  white-space: nowrap;
}
.balance strong {
  color: var(--text);
  font-size: 16px;
}
.content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  flex: 1;
  width: 100%;
  box-sizing: border-box;
}
.foot {
  max-width: 1000px;
  margin: 0 auto;
  padding: 16px 20px 28px;
  font-size: 12px;
  color: var(--muted);
  border-top: 1px solid var(--border);
}

/* ===== CS2 氛围背景层：雷达网格 + 氛围光 + 警示斜纹 ===== */
.backdrop {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  pointer-events: none;
  background:
    /* 顶部红色氛围光（赛场灯光感） */
    radial-gradient(55% 42% at 50% 0%, rgba(229, 72, 77, 0.1), transparent 70%),
    /* 雷达式细网格 */
    repeating-linear-gradient(0deg, transparent 0 39px, rgba(255, 255, 255, 0.028) 39px 40px),
    repeating-linear-gradient(90deg, transparent 0 39px, rgba(255, 255, 255, 0.028) 39px 40px);
}
.backdrop::after {
  /* 左下角警示斜纹（CS2 加载条风格），向右上淡出 */
  content: '';
  position: absolute;
  left: -60px;
  bottom: -60px;
  width: 360px;
  height: 240px;
  transform: rotate(-8deg);
  background: repeating-linear-gradient(
    45deg,
    rgba(229, 72, 77, 0.1) 0 10px,
    transparent 10px 22px
  );
  mask-image: linear-gradient(55deg, #000 0%, transparent 72%);
  -webkit-mask-image: linear-gradient(55deg, #000 0%, transparent 72%);
}
</style>
