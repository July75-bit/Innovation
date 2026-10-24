<script setup lang="ts">
/**
 * 市场页（路由 /）：GET /api/players（契约 §4.2）。
 * change_pct 用后端算好的值；rating 必须标注「模拟」。
 */
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { PlayerSummary } from '../api/types'
import { money, pct, trendClass } from '../utils/format'

const players = ref<PlayerSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    players.value = await api.listPlayers()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载选手列表失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-head">
      <h2>选手市场</h2>
      <button class="refresh" :disabled="loading" @click="load">刷新</button>
    </div>

    <p v-if="loading" class="state">加载中…</p>
    <div v-else-if="error" class="state error">
      <span>{{ error }}</span>
      <button @click="load">重试</button>
    </div>

    <ul v-else class="grid">
      <li
        v-for="p in players"
        :key="p.player_id"
        :class="['card', { suspended: p.status !== 'trading' }]"
      >
        <RouterLink :to="`/players/${p.player_id}`" class="card-link">
          <div class="top">
            <span class="name">{{ p.display_name || p.name }}</span>
            <span :class="['status', p.status === 'trading' ? 'ok' : 'halt']">
              {{ p.status === 'trading' ? '交易中' : '暂停交易' }}
            </span>
          </div>
          <div class="meta">
            <span>{{ p.team ?? '—' }}</span>
            <span class="role">{{ p.role ?? '—' }}</span>
          </div>
          <div class="price-row">
            <span class="price">{{ money(p.current_price) }}</span>
            <span :class="['change', trendClass(p.change_pct)]">{{ pct(p.change_pct) }}</span>
          </div>
          <div class="rating-row">
            <span class="rating-label">模拟表现分 <span class="sim-tag">模拟数据</span></span>
            <span class="rating">{{ p.rating }}</span>
          </div>
        </RouterLink>
      </li>
    </ul>
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
.grid {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  transition: box-shadow 0.15s ease;
}
.card:hover {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}
.card.suspended {
  opacity: 0.65;
}
.card-link {
  display: block;
  padding: 14px 16px;
  text-decoration: none;
  color: inherit;
}
.top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.name {
  font-size: 18px;
  font-weight: 700;
}
.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
}
.status.ok {
  background: rgba(10, 143, 74, 0.12);
  color: var(--down);
}
.status.halt {
  background: rgba(178, 106, 0, 0.14);
  color: #b26a00;
}
.meta {
  display: flex;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  margin-top: 2px;
}
.role {
  padding: 0 6px;
  border-radius: 4px;
  background: rgba(127, 127, 127, 0.12);
}
.price-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 10px;
}
.price {
  font-size: 22px;
  font-weight: 700;
}
.change {
  font-size: 14px;
  font-weight: 600;
}
.change.up {
  color: var(--up);
}
.change.down {
  color: var(--down);
}
.change.flat {
  color: var(--muted);
}
.rating-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 13px;
  color: var(--muted);
}
.rating {
  font-weight: 700;
  color: var(--text);
}
.sim-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(127, 127, 127, 0.16);
}
</style>
