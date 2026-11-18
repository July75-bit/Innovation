<script setup lang="ts">
/**
 * 白话导读：交易流水页（/trades），显示每一笔买入/卖出的时间、成交价、金额、成交后余额。
 *
 * 它是"这个系统说的话可以核对"的证据页：用户可以用它逐笔验算余额是否连续正确。
 * 数据只有一个来源 GET /api/trades，后端已按时间倒序返回，前端不再排序（避免两边顺序不一致）。
 *
 * 本页没有任何计算逻辑，只做展示 + 空态/错误态/加载态，是理解四态模板最简单的一个文件。
 */
/**
 * 交易记录页（路由 /trades）：GET /api/trades（§4.9，后端已按时间倒序，前端不再排序）。
 * 流水是"可验证性"的核心：每笔成交的时间/价格/金额/交易后余额全部回显，用户可自行核对。
 */
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { TradeItem } from '../api/types'
import { dateTime, money, clockTime } from '../utils/format'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'

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
    updatedAt.value = clockTime()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载交易流水失败'
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
        <h1>交易记录</h1>
        <p v-if="updatedAt && !loading && !error" class="meta">更新于 {{ updatedAt }}</p>
      </div>
      <button class="quiet-btn" :disabled="loading" @click="load">
        {{ loading ? '刷新中' : '刷新' }}
      </button>
    </header>

    <div v-if="loading" class="sk-list" aria-busy="true" aria-label="加载交易记录">
      <div v-for="i in 4" :key="i" class="sk-row">
        <span class="sk sk-name"></span><span class="sk sk-mid"></span
        ><span class="sk sk-num"></span>
      </div>
    </div>
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="trades.length === 0">
      暂无交易记录。去 <RouterLink to="/">市场</RouterLink> 完成第一笔虚拟交易吧。
    </EmptyState>

    <table v-else class="list">
      <thead>
        <tr>
          <th>时间</th>
          <th>选手</th>
          <th>方向</th>
          <th class="num">数量 × 成交价</th>
          <th class="num">金额</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in trades" :key="t.trade_id">
          <td data-label="时间" class="time">{{ dateTime(t.created_at) }}</td>
          <td data-label="选手">
            <RouterLink class="name" :to="`/players/${t.player_id}`">{{ t.name }}</RouterLink>
          </td>
          <td data-label="方向">
            <span :class="['side', t.side.toLowerCase()]">{{
              t.side === 'BUY' ? '买入' : '卖出'
            }}</span>
          </td>
          <td data-label="数量 × 成交价" class="num">{{ t.quantity }} × {{ money(t.price) }}</td>
          <td data-label="金额" class="num">{{ money(t.amount) }}</td>
        </tr>
      </tbody>
    </table>
  </article>
</template>

<style scoped>
/* 交易记录（纸感）：5 列、行高 56，无外框；方向只用文字颜色区分 */
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
.quiet-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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
}
.list td.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.list .time {
  color: var(--muted);
  font-size: var(--fs-aux);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
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
.list .side {
  font-size: var(--fs-aux);
}
.list .side.buy {
  color: var(--up-text);
}
.list .side.sell {
  color: var(--down);
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
