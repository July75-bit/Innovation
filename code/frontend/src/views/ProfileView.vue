<script setup lang="ts">
/**
 * 个人主页（/me）：把原先堆在侧栏的个人信息收进来。
 *
 * 侧栏只留导航；身份、资产曲线、交易统计、偏好、账户安全（退出/删号）、关于都在这页。
 * 数据来源：GET /api/account（余额/资产）、GET /api/account/history（曲线+统计）、GET /api/trades（最近流水）。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { AccountHistoryResponse, TradeItem } from '../api/types'
import { money } from '../utils/format'
import { useAccount } from '../composables/useAccount'
import { useAuth } from '../composables/useAuth'
import { checkBackendHealth, useBackendHealth } from '../composables/useBackendHealth'
import { useTheme } from '../composables/useTheme'
import AboutDialog from '../components/AboutDialog.vue'
import AssetChart from '../components/AssetChart.vue'
import DeleteAccountDialog from '../components/DeleteAccountDialog.vue'
import ErrorState from '../components/ErrorState.vue'

const router = useRouter()
const { account, refreshAccount } = useAccount()
const { currentUser, accountLabel, isLoggedIn, logout } = useAuth()
const { preference, theme, setTheme } = useTheme()
const { service: backend } = useBackendHealth()

const history = ref<AccountHistoryResponse | null>(null)
const recentTrades = ref<TradeItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const aboutOpen = ref(false)
const deleteOpen = ref(false)

const THEME_OPTIONS = [
  { value: 'auto', label: '自动' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
] as const

const displayName = computed(() => currentUser.value?.nickname ?? '访客')
const userInitial = computed(() => displayName.value.charAt(0).toUpperCase())
const profit = computed(() =>
  account.value ? account.value.total_asset - account.value.initial_balance : null,
)
const stats = computed(() => history.value?.stats ?? null)
/** 资产结构：现金 vs 持仓市值占比（四舍五入到整数，合计保持 100%） */
const cashPct = computed(() => {
  if (!account.value || account.value.total_asset <= 0) return 0
  return Math.round((account.value.balance / account.value.total_asset) * 100)
})
const positionPct = computed(() => (account.value ? 100 - cashPct.value : 0))
const healthText = computed(() => {
  if (backend.value === null) return '检测后端连接…'
  if (backend.value === false) return '后端未连接'
  return '服务正常'
})

async function load(fresh = false): Promise<void> {
  if (fresh) api.invalidate?.()
  loading.value = true
  error.value = null
  checkBackendHealth()
  try {
    const [, data, trades] = await Promise.all([
      refreshAccount(),
      api.getAccountHistory(30),
      api.listTrades(),
    ])
    history.value = data
    recentTrades.value = trades.slice(0, 5)
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载账户信息失败'
  } finally {
    loading.value = false
  }
}

/** 登录/退出：访客点「登录」去登录页；私人账户点「退出」先撤销令牌再回登录页 */
async function onAccountAction(): Promise<void> {
  if (!isLoggedIn.value) {
    await router.push({ name: 'auth' })
    return
  }
  await logout()
  await router.push({ name: 'auth' })
}

async function onAccountDeleted(): Promise<void> {
  await router.push({ name: 'auth', query: { deleted: '1' } })
}

onMounted(() => {
  void load()
})
</script>

<template>
  <article class="profile">
    <header class="page-head">
      <h1>我的</h1>
      <p class="sub">账户、资产、交易统计与偏好都收在这一页；侧栏只留导航。</p>
    </header>

    <!-- 身份 + 账户操作 -->
    <section class="card identity">
      <div class="who">
        <span class="avatar" aria-hidden="true">{{ userInitial }}</span>
        <div class="who-text">
          <strong class="name">{{ displayName }}</strong>
          <span class="kind">{{ accountLabel }}</span>
        </div>
      </div>
      <div class="who-actions">
        <button type="button" class="btn" @click="onAccountAction">
          {{ isLoggedIn ? '退出登录' : '登录 / 注册' }}
        </button>
        <button v-if="isLoggedIn" type="button" class="btn btn-quiet" @click="deleteOpen = true">
          删除账号
        </button>
      </div>
    </section>

    <ErrorState v-if="error" :message="error" @retry="load(true)" />

    <template v-else>
      <!-- 资产概览 + 曲线 -->
      <section class="card">
        <div class="card-head">
          <h2>资产</h2>
          <button type="button" class="refresh" :disabled="loading" @click="load(true)">
            {{ loading ? '刷新中…' : '刷新' }}
          </button>
        </div>
        <div v-if="account" class="asset-grid">
          <div class="asset">
            <span class="asset-label">余额（信用点）</span>
            <strong class="asset-value num">{{ money(account.balance) }}</strong>
          </div>
          <div class="asset">
            <span class="asset-label">总资产</span>
            <strong class="asset-value num">{{ money(account.total_asset) }}</strong>
          </div>
          <div class="asset">
            <span class="asset-label">总收益</span>
            <strong
              :class="['asset-value', 'num', (profit ?? 0) > 0 ? 'up' : (profit ?? 0) < 0 ? 'down' : 'flat']"
            >
              {{ profit === null ? '—' : (profit >= 0 ? '+' : '') + money(profit) }}
            </strong>
          </div>
        </div>
        <div v-else class="asset-grid">
          <span class="sk sk-value"></span><span class="sk sk-value"></span><span class="sk sk-value"></span>
        </div>
        <!-- 资产结构：现金 / 持仓市值占比（一眼看清仓位轻重） -->
        <div v-if="account" class="structure">
          <div
            class="structure-bar"
            role="img"
            :aria-label="`资产结构：现金 ${cashPct}%，持仓 ${positionPct}%`"
          >
            <span class="seg-cash" :style="{ width: `${cashPct}%` }"></span>
            <span class="seg-pos" :style="{ width: `${positionPct}%` }"></span>
          </div>
          <div class="structure-legend">
            <span class="item">
              <i class="swatch cash" aria-hidden="true"></i>
              现金 <b class="num">{{ money(account.balance) }}</b>
              <span class="pct num">{{ cashPct }}%</span>
            </span>
            <span class="item">
              <i class="swatch pos" aria-hidden="true"></i>
              持仓 <b class="num">{{ money(account.position_value) }}</b>
              <span class="pct num">{{ positionPct }}%</span>
            </span>
          </div>
        </div>
        <AssetChart v-if="history" :points="history.points" />
        <p v-else-if="loading" class="muted">资产曲线加载中…</p>
      </section>

      <!-- 交易统计 + 最近流水 -->
      <section class="card">
        <div class="card-head">
          <h2>交易统计</h2>
          <span class="muted">全部来自当前账户</span>
        </div>
        <dl v-if="stats" class="stats">
          <div><dt>交易笔数</dt><dd class="num">{{ stats.trades }}</dd></div>
          <div><dt>买入 / 卖出</dt><dd class="num">{{ stats.buys }} / {{ stats.sells }}</dd></div>
          <div><dt>买入金额</dt><dd class="num">{{ money(stats.buy_amount) }}</dd></div>
          <div><dt>卖出金额</dt><dd class="num">{{ money(stats.sell_amount) }}</dd></div>
          <div><dt>持仓数</dt><dd class="num">{{ stats.positions }}</dd></div>
          <div><dt>持仓市值</dt><dd class="num">{{ money(stats.position_value) }}</dd></div>
        </dl>
        <h3 class="sub-title">最近交易</h3>
        <ul v-if="recentTrades.length" class="trades">
          <li v-for="trade in recentTrades" :key="trade.trade_id">
            <span class="t-time num">{{ trade.created_at.slice(5, 16).replace('T', ' ') }}</span>
            <span class="t-name">{{ trade.name }}</span>
            <span :class="['t-side', trade.side === 'BUY' ? 'up' : 'down']">
              {{ trade.side === 'BUY' ? '买入' : '卖出' }}
            </span>
            <span class="t-qty num">{{ trade.quantity }} × {{ money(trade.price) }}</span>
            <span class="t-amount num">{{ money(trade.amount) }}</span>
          </li>
        </ul>
        <p v-else-if="!loading" class="muted">还没有交易记录，去市场挑一位选手吧。</p>
      </section>

      <!-- 偏好 + 关于 -->
      <section class="card">
        <h2>偏好与关于</h2>
        <div class="row">
          <span class="row-label">主题</span>
          <div class="segmented" role="group" aria-label="主题偏好">
            <button
              v-for="option in THEME_OPTIONS"
              :key="option.value"
              type="button"
              :class="['seg', { on: preference === option.value }]"
              :aria-pressed="preference === option.value"
              @click="setTheme(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <div class="row">
          <span class="row-label">服务状态</span>
          <span :class="['health', theme]">{{ healthText }}</span>
        </div>
        <div class="row">
          <span class="row-label">关于本站</span>
          <button type="button" class="link" @click="aboutOpen = true">查看说明与合规声明</button>
        </div>
      </section>
    </template>

    <AboutDialog :open="aboutOpen" @update:open="aboutOpen = $event" />
    <DeleteAccountDialog
      v-model="deleteOpen"
      :nickname="displayName"
      @deleted="onAccountDeleted"
    />
  </article>
</template>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-width: 880px;
}
.page-head h1 {
  margin: 0;
  font-size: var(--fs-h1);
}
.sub {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: var(--fs-aux);
}
.card {
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.card h2 {
  margin: 0;
  font-size: var(--fs-h3);
}
.muted {
  color: var(--faint);
  font-size: var(--fs-cap);
}
.refresh {
  border: 0;
  background: none;
  color: var(--muted);
  font-size: var(--fs-aux);
  cursor: pointer;
}
.refresh:hover:not(:disabled) {
  color: var(--text);
}
/* 身份 */
.identity {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.who {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--neutral-bg);
  border: 1px solid var(--color-border);
  color: var(--muted);
  font-weight: 600;
}
.who-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.name {
  font-size: var(--fs-body);
  color: var(--text);
}
.kind {
  font-size: var(--fs-cap);
  color: var(--faint);
}
.who-actions {
  display: flex;
  gap: var(--space-2);
}
.btn {
  min-height: 36px;
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--text);
  font-size: var(--fs-aux);
  cursor: pointer;
}
.btn:hover {
  background: var(--neutral-bg);
}
.btn-quiet {
  border-color: var(--color-border);
  color: var(--muted);
}
.btn-quiet:hover {
  color: var(--color-error-base);
  border-color: var(--color-error-base);
}
/* 资产 */
.asset-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}
.asset {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.asset-label {
  font-size: var(--fs-cap);
  color: var(--faint);
}
.asset-value {
  font-size: var(--fs-h2);
  font-weight: 600;
  color: var(--text);
}
.sk-value {
  width: 100%;
  height: 30px;
}
/* 资产结构条 */
.structure {
  margin: 0 0 var(--space-4);
}
.structure-bar {
  display: flex;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--neutral-bg);
  margin-bottom: var(--space-2);
}
.structure-bar span {
  display: block;
  height: 100%;
}
.seg-cash {
  background: var(--color-border-strong);
}
.seg-pos {
  background: var(--accent-text);
}
.structure-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  font-size: var(--fs-cap);
  color: var(--muted);
}
.structure-legend .item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.structure-legend b {
  color: var(--text);
  font-weight: 500;
}
.structure-legend .pct {
  color: var(--faint);
}
.swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}
.swatch.cash {
  background: var(--color-border-strong);
}
.swatch.pos {
  background: var(--accent-text);
}
/* 统计 */
.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  margin: 0 0 var(--space-5);
}
.stats div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stats dt {
  font-size: var(--fs-cap);
  color: var(--faint);
}
.stats dd {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--text);
}
.sub-title {
  margin: var(--space-4) 0 var(--space-2);
  font-size: var(--fs-aux);
  color: var(--muted);
  font-weight: 500;
}
.trades {
  list-style: none;
  margin: 0;
  padding: 0;
}
.trades li {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr) 48px 120px 90px;
  align-items: baseline;
  gap: var(--space-3);
  padding: 10px 0;
  border-top: 1px solid var(--color-border);
  font-size: var(--fs-aux);
}
.trade:first-child {
  border-top: 0;
}
.t-time,
.t-qty,
.t-amount {
  color: var(--muted);
}
.t-name {
  color: var(--text);
}
.t-side.up {
  color: var(--up-text);
}
.t-side.down {
  color: var(--color-down);
}
.t-amount {
  text-align: right;
}
/* 偏好 */
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) 0;
  border-top: 1px solid var(--color-border);
}
.row:first-child {
  border-top: 0;
}
.row-label {
  font-size: var(--fs-aux);
  color: var(--muted);
}
.segmented {
  display: inline-flex;
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.seg {
  min-height: 28px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-cap);
  cursor: pointer;
}
.seg.on {
  background: var(--neutral-bg);
  color: var(--text);
}
.health {
  font-size: var(--fs-cap);
  color: var(--color-success-base);
}
.health.bad {
  color: var(--color-error-base);
}
.link {
  border: 0;
  background: none;
  padding: 0;
  color: var(--accent-text);
  font-size: var(--fs-aux);
  cursor: pointer;
}
.link:hover {
  text-decoration: underline;
  text-underline-offset: 3px;
}
@media (max-width: 720px) {
  .asset-grid,
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .trades li {
    grid-template-columns: minmax(0, 1fr) auto;
    row-gap: 2px;
  }
  .t-time {
    display: none;
  }
  .t-amount {
    text-align: left;
  }
}
</style>
