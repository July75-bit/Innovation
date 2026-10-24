<script setup lang="ts">
/**
 * 交易记录页（路由 /trades）：GET /api/trades（§4.9，后端已按时间倒序，前端不再排序）。
 */
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { TradeItem } from '../api/types'
import { dateTime, money } from '../utils/format'

const trades = ref<TradeItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    trades.value = await api.listTrades()
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
      <h2>交易记录</h2>
      <button class="refresh" :disabled="loading" @click="load">刷新</button>
    </div>

    <p v-if="loading" class="state">加载中…</p>
    <div v-else-if="error" class="state error">
      <span>{{ error }}</span>
      <button @click="load">重试</button>
    </div>
    <p v-else-if="trades.length === 0" class="state">暂无交易记录。</p>

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
          <td>{{ dateTime(t.created_at) }}</td>
          <td>
            <span :class="['side', t.side.toLowerCase()]">{{
              t.side === 'BUY' ? '买入' : '卖出'
            }}</span>
          </td>
          <td>
            <RouterLink :to="`/players/${t.player_id}`">{{ t.name }}</RouterLink>
          </td>
          <td class="num">{{ t.quantity }}</td>
          <td class="num">{{ money(t.price) }}</td>
          <td class="num">{{ money(t.amount) }}</td>
          <td class="num">{{ money(t.balance_after) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-head h2 {
  margin: 0;
}
.refresh {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}
.refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.state {
  color: var(--muted);
  padding: 24px 0;
  display: flex;
  gap: 12px;
  align-items: center;
}
.state.error {
  color: var(--up);
}
.state button {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
}
th,
td {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  font-size: 14px;
}
th {
  color: var(--muted);
  font-weight: 600;
  font-size: 13px;
}
.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.side {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 999px;
  color: #fff;
}
.side.buy {
  background: var(--up);
}
.side.sell {
  background: var(--down);
}
</style>
