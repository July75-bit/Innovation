<script setup lang="ts">
/**
 * 白话导读：持仓页（/positions）= 我的股票列表：持有几只、成本多少、现价多少、赚还是亏。
 *
 * 数据来自两个接口并发请求：GET /api/positions（明细）和 GET /api/account（顶部四个汇总数字）。
 * 盈亏(profit)和盈亏率(profit_pct)由后端算好，这里不重算——避免两边数字打架。
 *
 * 小细节：余额刷新失败不影响持仓展示（Promise.all 里给 refreshAccount 挂了 catch），
 * 窄屏时表格靠 CSS 自动变卡片（每列的 data-label 属性就是卡片上显示的字段名）。
 */
/**
 * 持仓页（路由 /positions）：GET /api/positions（§4.6）+ GET /api/account（§4.5）
 * profit / profit_pct 直接用后端算好的值。
 * 信息架构：先看总览（余额/市值/总资产/收益），再看明细表；窄屏自动转卡片。
 */
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { PositionItem } from '../api/types'
import { money, pct, trendClass } from '../utils/format'
import { useAccount } from '../composables/useAccount'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const positions = ref<PositionItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const updatedAt = ref('')
const { account, refreshAccount } = useAccount()

// 「余额重建」：把自己这个账户恢复成刚注册的样子（余额回 5000、清空本账户持仓与流水）。
// 语义说明：重置行情（/api/debug/reseed）**不会**动任何账号的余额与流水——它们跟着账号走，
// 所以"我想重新开始"只能由用户自己按这个按钮。
const rebuilding = ref(false)
const rebuildNotice = ref<string | null>(null)

async function rebuildBalance() {
  const ok = window.confirm(
    '确定重建余额吗？\n\n' +
      '· 你的余额会恢复到初始 5000 信用点\n' +
      '· 本账户的持仓与交易记录会被清空（不可撤销）\n' +
      '· 其它账号与市场行情不受影响',
  )
  if (!ok) return

  rebuilding.value = true
  rebuildNotice.value = null
  try {
    const result = await api.rebuildAccount()
    rebuildNotice.value =
      `已重建：余额 ${money(result.balance)}；清空持仓 ${result.cleared_positions} 条、` +
      `交易记录 ${result.cleared_trades} 条`
    await load()
  } catch (err) {
    rebuildNotice.value = err instanceof ApiError ? err.message : '重建失败，请稍后再试'
  } finally {
    rebuilding.value = false
  }
}

async function load() {
  loading.value = true
  error.value = null
  checkBackendHealth()
  try {
    // 余额刷新是 best-effort：失败不应把已能拿到的持仓列表也打成错误态
    const [list] = await Promise.all([api.getPositions(), refreshAccount().catch(() => {})])
    positions.value = list
    updatedAt.value = new Date().toLocaleTimeString()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载持仓失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2>我的持仓</h2>
        <p class="updated" v-if="updatedAt && !loading && !error">更新于 {{ updatedAt }}</p>
      </div>
      <div class="head-actions">
        <button class="refresh" :disabled="loading" @click="load">刷新</button>
        <button class="rebuild" :disabled="rebuilding || loading" @click="rebuildBalance">
          {{ rebuilding ? '重建中…' : '余额重建' }}
        </button>
      </div>
    </div>

    <p v-if="rebuildNotice" class="rebuild-notice">{{ rebuildNotice }}</p>

    <!-- 总览：四个关键指标一屏可见 -->
    <div v-if="account" class="summary num">
      <div class="stat">
        <span>余额（信用点）</span><strong>{{ money(account.balance) }}</strong>
      </div>
      <div class="stat">
        <span>持仓市值</span><strong>{{ money(account.position_value) }}</strong>
      </div>
      <div class="stat">
        <span>总资产</span><strong>{{ money(account.total_asset) }}</strong>
      </div>
      <div class="stat">
        <span>总收益</span>
        <strong :class="trendClass(account.total_asset - account.initial_balance)">
          {{ (account.total_asset - account.initial_balance >= 0 ? '+' : '') + money(account.total_asset - account.initial_balance) }}
        </strong>
      </div>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="positions.length === 0">
      暂无持仓，去 <RouterLink to="/">市场</RouterLink> 看看。
    </EmptyState>

    <table v-else>
      <thead>
        <tr>
          <th>选手</th>
          <th class="num">持仓</th>
          <th class="num">买入均价</th>
          <th class="num">现价</th>
          <th class="num">市值</th>
          <th class="num">盈亏</th>
          <th class="num">盈亏率</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in positions" :key="p.player_id">
          <td data-label="选手">{{ p.name }}</td>
          <td data-label="持仓" class="num">{{ p.quantity }}</td>
          <td data-label="买入均价" class="num">{{ money(p.avg_cost) }}</td>
          <td data-label="现价" class="num">{{ money(p.current_price) }}</td>
          <td data-label="市值" class="num">{{ money(p.market_value) }}</td>
          <td data-label="盈亏" :class="['num', trendClass(p.profit)]">{{ money(p.profit) }}</td>
          <td data-label="盈亏率" :class="['num', trendClass(p.profit_pct)]">{{ pct(p.profit_pct) }}</td>
          <td data-label="操作"><RouterLink class="go" :to="`/players/${p.player_id}`">交易 →</RouterLink></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
}
.page-head h2 {
  margin: 0;
  font-size: var(--fs-h2);
}
.updated {
  margin: 4px 0 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.refresh {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-body);
  cursor: pointer;
}
.refresh:hover {
  border-color: var(--accent-text);
  color: var(--accent-text);
}
.refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 头部按钮组：刷新 + 余额重建 */
.head-actions {
  display: flex;
  gap: var(--space-2);
  align-items: center;
}
.rebuild {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-body);
  cursor: pointer;
}
.rebuild:hover {
  border-color: var(--danger, #d9534f);
  color: var(--danger, #d9534f);
}
.rebuild:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.rebuild-notice {
  margin: var(--space-2) 0 0;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: var(--fs-cap);
  color: var(--text);
}

/* 总览卡片：统一间距/圆角/层级 */
.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-4);
  margin-top: var(--space-5);
}
.stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat span {
  font-size: var(--fs-cap);
  color: var(--muted);
}
.stat strong {
  font-size: var(--fs-h2);
  font-variant-numeric: tabular-nums;
}
.stat strong.up {
  color: var(--up-text);
}
.stat strong.down {
  color: var(--down);
}
.stat strong.flat {
  color: var(--muted);
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: var(--space-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
th,
td {
  padding: 11px var(--space-4);
  border-bottom: 1px solid var(--border);
  text-align: left;
  font-size: var(--fs-body);
}
tbody tr:last-child td {
  border-bottom: none;
}
tbody tr:hover {
  background: var(--surface-2);
}
th {
  color: var(--muted);
  font-weight: 600;
  font-size: var(--fs-aux);
  background: var(--surface-2);
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.up {
  color: var(--up-text);
}
.down {
  color: var(--down);
}
.flat {
  color: var(--muted);
}
.go {
  color: var(--accent-text);
  text-decoration: none;
  font-size: var(--fs-aux);
  font-weight: 600;
  white-space: nowrap;
}
.go:hover {
  text-decoration: underline;
}

/* 响应式（≤720px）：表格转卡片，杜绝横向滚动 */
@media (max-width: 720px) {
  table {
    display: block;
    background: transparent;
    border: none;
    border-radius: 0;
    margin-top: var(--space-3);
  }
  thead {
    display: none;
  }
  tbody {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  tr {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px var(--space-4);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: var(--space-3) var(--space-4);
  }
  td {
    border: none;
    padding: 3px 0;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
    font-size: var(--fs-aux);
  }
  td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: var(--fs-cap);
    flex-shrink: 0;
  }
  td:first-child {
    grid-column: 1 / -1;
    font-weight: 700;
    font-size: var(--fs-h3);
    padding-bottom: 6px;
  }
  .num {
    text-align: right;
  }
}
</style>