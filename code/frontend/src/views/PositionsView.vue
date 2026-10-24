<script setup lang="ts">
/**
 * 持仓页（路由 /positions）：GET /api/positions（§4.6）+ GET /api/account（§4.5）
 * profit / profit_pct 直接用后端算好的值。
 */
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { PositionItem } from '../api/types'
import { money, pct, trendClass } from '../utils/format'
import { useAccount } from '../composables/useAccount'

const positions = ref<PositionItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const { account, refreshAccount } = useAccount()

async function load() {
  loading.value = true
  error.value = null
  try {
    const [list] = await Promise.all([api.getPositions(), refreshAccount()])
    positions.value = list
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
      <h2>我的持仓</h2>
      <button class="refresh" :disabled="loading" @click="load">刷新</button>
    </div>

    <div v-if="account" class="summary">
      <div>
        <span>余额</span><strong>{{ money(account.balance) }}</strong>
      </div>
      <div>
        <span>持仓市值</span><strong>{{ money(account.position_value) }}</strong>
      </div>
      <div>
        <span>总资产</span><strong>{{ money(account.total_asset) }}</strong>
      </div>
      <div>
        <span>总收益</span>
        <strong :class="trendClass(account.total_asset - account.initial_balance)">
          {{ money(account.total_asset - account.initial_balance) }}
        </strong>
      </div>
    </div>

    <p v-if="loading" class="state">加载中…</p>
    <div v-else-if="error" class="state error">
      <span>{{ error }}</span>
      <button @click="load">重试</button>
    </div>
    <p v-else-if="positions.length === 0" class="state">
      暂无持仓，去 <RouterLink to="/">市场</RouterLink> 看看。
    </p>

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
          <td>{{ p.name }}</td>
          <td class="num">{{ p.quantity }}</td>
          <td class="num">{{ money(p.avg_cost) }}</td>
          <td class="num">{{ money(p.current_price) }}</td>
          <td class="num">{{ money(p.market_value) }}</td>
          <td :class="['num', trendClass(p.profit)]">{{ money(p.profit) }}</td>
          <td :class="['num', trendClass(p.profit_pct)]">{{ pct(p.profit_pct) }}</td>
          <td><RouterLink :to="`/players/${p.player_id}`">交易</RouterLink></td>
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
.summary {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 18px;
  margin-top: 14px;
}
.summary div {
  display: flex;
  flex-direction: column;
}
.summary span {
  font-size: 12px;
  color: var(--muted);
}
.summary strong {
  font-size: 18px;
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
.up {
  color: var(--up);
}
.down {
  color: var(--down);
}
.flat {
  color: var(--muted);
}
</style>
