<script setup lang="ts">
/**
 * 交易记录页（路由 /trades）：GET /api/trades（§4.9，后端已按时间倒序，前端不再排序）。
 * 流水是"可验证性"的核心：每笔成交的时间/价格/金额/交易后余额全部回显，用户可自行核对。
 */
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { TradeItem } from '../api/types'
import { dateTime, money } from '../utils/format'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const trades = ref<TradeItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const updatedAt = ref('')

async function load() {
  loading.value = true
  error.value = null
  checkBackendHealth()
  try {
    trades.value = await api.listTrades()
    updatedAt.value = new Date().toLocaleTimeString()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载交易流水失败'
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
        <h2>交易记录</h2>
        <p class="updated" v-if="updatedAt && !loading && !error">更新于 {{ updatedAt }}</p>
      </div>
      <button class="refresh" :disabled="loading" @click="load">刷新</button>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="trades.length === 0">
      暂无交易记录。去 <RouterLink to="/">市场</RouterLink> 完成第一笔虚拟交易吧。
    </EmptyState>

    <table v-else>
      <thead>
        <tr>
          <th>时间</th>
          <th>方向</th>
          <th>选手</th>
          <th class="num">数量</th>
          <th class="num">成交价</th>
          <th class="num">金额</th>
          <th class="num">交易后余额</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in trades" :key="t.trade_id">
          <td data-label="时间">{{ dateTime(t.created_at) }}</td>
          <td data-label="方向">
            <span :class="['side', t.side.toLowerCase()]">{{
              t.side === 'BUY' ? '买入' : '卖出'
            }}</span>
          </td>
          <td data-label="选手">
            <RouterLink class="go" :to="`/players/${t.player_id}`">{{ t.name }}</RouterLink>
          </td>
          <td data-label="数量" class="num">{{ t.quantity }}</td>
          <td data-label="成交价" class="num">{{ money(t.price) }}</td>
          <td data-label="金额" class="num">{{ money(t.amount) }}</td>
          <td data-label="交易后余额" class="num">{{ money(t.balance_after) }}</td>
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
  border-color: var(--accent);
  color: var(--accent);
}
.refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: var(--space-4);
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
.side {
  font-size: var(--fs-cap);
  font-weight: 700;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
}
.side.buy {
  background: var(--up-bg);
  color: var(--up);
}
.side.sell {
  background: var(--down-bg);
  color: var(--down);
}
.go {
  color: var(--accent);
  text-decoration: none;
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