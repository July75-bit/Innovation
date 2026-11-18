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
import { money, pct, trendClass, clockTime } from '../utils/format'
import { useAccount } from '../composables/useAccount'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'

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
    updatedAt.value = clockTime()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载持仓失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>


<template>
  <article class="page">
    <header class="page-head">
      <div>
        <h1>持仓</h1>
        <p v-if="updatedAt && !loading && !error" class="meta">更新于 {{ updatedAt }}</p>
      </div>
      <div class="head-actions">
        <button class="quiet-btn" :disabled="loading" @click="load">
          {{ loading ? '刷新中' : '刷新' }}
        </button>
        <button class="quiet-btn danger" :disabled="rebuilding || loading" @click="rebuildBalance">
          {{ rebuilding ? '重建中' : '余额重建' }}
        </button>
      </div>
    </header>

    <p v-if="rebuildNotice" class="notice">{{ rebuildNotice }}</p>

    <dl v-if="account" class="summary num">
      <div>
        <dt>余额</dt>
        <dd>{{ money(account.balance) }}</dd>
      </div>
      <div>
        <dt>持仓市值</dt>
        <dd>{{ money(account.position_value) }}</dd>
      </div>
      <div>
        <dt>总资产</dt>
        <dd>{{ money(account.total_asset) }}</dd>
      </div>
      <div>
        <dt>总收益</dt>
        <dd :class="trendClass(account.total_asset - account.initial_balance)">
          {{ (account.total_asset - account.initial_balance >= 0 ? '+' : '') + money(account.total_asset - account.initial_balance) }}
        </dd>
      </div>
    </dl>

    <div v-if="loading" class="sk-list" aria-busy="true" aria-label="加载持仓">
      <div v-for="i in 4" :key="i" class="sk-row">
        <span class="sk sk-name"></span><span class="sk sk-mid"></span
        ><span class="sk sk-num"></span>
      </div>
    </div>
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="positions.length === 0">
      暂无持仓，去 <RouterLink to="/">市场</RouterLink> 看看。
    </EmptyState>

    <table v-else class="list">
      <thead>
        <tr>
          <th>选手</th>
          <th class="num">持仓 / 均价</th>
          <th class="num">现价</th>
          <th class="num">盈亏</th>
          <th class="op"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in positions" :key="p.player_id">
          <td data-label="选手">
            <RouterLink class="name" :to="`/players/${p.player_id}`">{{ p.name }}</RouterLink>
          </td>
          <td data-label="持仓 / 均价" class="num">{{ p.quantity }} 股 · {{ money(p.avg_cost) }}</td>
          <td data-label="现价" class="num">{{ money(p.current_price) }}</td>
          <td data-label="盈亏" :class="['num', trendClass(p.profit_pct)]">
            {{ money(p.profit) }}（{{ pct(p.profit_pct) }}）
          </td>
          <td class="op">
            <RouterLink class="go" :to="`/players/${p.player_id}`">交易</RouterLink>
          </td>
        </tr>
      </tbody>
    </table>
  </article>
</template>

<style scoped>
/* 持仓页（纸感）：总览只做排版，不套四张卡；明细表只留 5 列、行高 64 */
.page {
  display: flex;
  flex-direction: column;
}
.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.page-head h1 {
  margin: 0;
  font-size: var(--fs-h1);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.meta {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--faint);
}
.head-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.quiet-btn {
  padding: var(--space-2) 0;
  border: 0;
  background: none;
  color: var(--muted);
  font: inherit;
  font-size: var(--fs-aux);
  cursor: pointer;
}
.quiet-btn:hover {
  color: var(--text);
}
.quiet-btn.danger:hover {
  color: var(--up-text);
}
.quiet-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.notice {
  margin: 0 0 var(--space-4);
  font-size: var(--fs-cap);
  color: var(--muted);
}

/* 总览：四个数字一行，靠留白分开 */
.summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-5);
  margin: 0 0 var(--space-6);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.summary dt {
  font-size: var(--fs-cap);
  color: var(--faint);
}
.summary dd {
  margin: var(--space-2) 0 0;
  font-size: 24px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--text);
}
.summary dd.up {
  color: var(--up-text);
}
.summary dd.down {
  color: var(--down);
}
.summary dd.flat {
  color: var(--muted);
}

/* 明细表：无外框、无斑马纹，只有行分割线 */
.list {
  width: 100%;
  border-collapse: collapse;
}
.list th {
  padding: 0 0 var(--space-3);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--fs-cap);
  font-weight: 400;
  color: var(--faint);
  text-align: left;
}
.list th.num {
  text-align: right;
}
.list td {
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--color-border);
  font-size: var(--fs-body);
  color: var(--text);
  vertical-align: baseline;
}
.list td.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.list .name {
  color: var(--text);
  font-weight: 500;
  text-decoration: none;
}
.list .name:hover {
  text-decoration: underline;
  text-underline-offset: 3px;
}
.list td.up {
  color: var(--up-text);
}
.list td.down {
  color: var(--down);
}
.list td.flat {
  color: var(--muted);
}
.list .op {
  text-align: right;
}
.list .go {
  color: var(--faint);
  font-size: var(--fs-aux);
  text-decoration: none;
}
.list .go:hover {
  color: var(--text);
  text-decoration: underline;
  text-underline-offset: 3px;
}

@media (max-width: 720px) {
  .summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-4);
  }
  .summary dd {
    font-size: 20px;
  }
  /* 窄屏：表格转成"标签 + 值"的行，一行一件事，便于扫读 */
  .list thead {
    display: none;
  }
  .list tr {
    display: block;
    padding: var(--space-4) 0;
    border-bottom: 1px solid var(--color-border);
  }
  .list td {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-4);
    padding: 3px 0;
    border: 0;
    font-size: var(--fs-aux);
  }
  .list td[data-label]::before {
    content: attr(data-label);
    flex: none;
    color: var(--faint);
    font-size: var(--fs-cap);
  }
  .list td.num {
    text-align: right;
  }
  .list td.op {
    justify-content: flex-end;
  }
  .list .name {
    font-size: var(--fs-body);
  }
}
</style>
