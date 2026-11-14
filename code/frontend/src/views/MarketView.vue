<script setup lang="ts">
/**
 * 白话导读：默认首页（URL 是 /），把 8 名选手做成一张可搜索、可排序、可筛选的行情列表。
 *
 * 页面套路（本项目四个数据页都一样，看懂一个就全懂）：
 *   1) 三个响应式变量：players(数据)、loading(转圈中)、error(错误文案)；
 *   2) onMounted(load)：一进页面就调 load()；
 *   3) load() 里 api.listPlayers() 拿数据，成功填 players，失败把中文 message 填进 error；
 *   4) <template> 用 v-if / v-else-if 四选一：骨架屏 / 错误重试 / 空列表 / 正常表格；
 *   5) 搜索和排序是 computed(filtered)：纯前端展示过滤，不发请求、不改原始数据。
 *
 * 涨跌幅、评分都是后端算好的，这里只做展示；点一行跳到详情页 /players/编号。
 */
/**
 * 市场页（路由 /）：GET /api/players（契约 §4.2）。
 * change_pct 用后端算好的值；rating 必须标注「模拟」。
 * 界面设计层：搜索 / 排序 / 状态筛选让"找到目标选手"这一步最短；
 * 状态层：空 / 骨架加载 / 成功 / 出错四态齐备，加载不再整页闪白。
 */
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { PlayerSummary } from '../api/types'
import { money, pct, trendClass } from '../utils/format'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import StatusBadge from '../components/StatusBadge.vue'

const players = ref<PlayerSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
/** 系统状态可见：告诉用户"这批行情是什么时候拉的" */
const updatedAt = ref('')

/* ---- 今日智能体简报（第 8 轮：让智能体出现在首屏，而不是只藏在详情页） ---- */
type BriefItem = { title: string; detail: string; player_id?: number | null }
const brief = ref<{ summary: string; items: BriefItem[]; source: string } | null>(null)

async function loadBrief() {
  try {
    const data = await api.getAgentBrief()
    brief.value = { summary: data.summary, items: data.items, source: data.source }
  } catch {
    // 简报是"锦上添花"：拿不到就整块隐藏，绝不影响行情列表
    brief.value = null
  }
}

/* ---- 筛选 / 排序（纯前端展示逻辑，不改后端数据） ---- */
const keyword = ref('')
const statusFilter = ref<'all' | 'trading' | 'halted'>('all')
const sortBy = ref<'default' | 'price' | 'change' | 'rating'>('default')

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  let list = players.value
  if (kw) {
    list = list.filter(
      (p) =>
        (p.display_name || p.name || '').toLowerCase().includes(kw) ||
        (p.team || '').toLowerCase().includes(kw),
    )
  }
  if (statusFilter.value !== 'all') {
    list = list.filter((p) =>
      statusFilter.value === 'trading' ? p.status === 'trading' : p.status !== 'trading',
    )
  }
  switch (sortBy.value) {
    case 'price':
      return [...list].sort((a, b) => b.current_price - a.current_price)
    case 'change':
      return [...list].sort((a, b) => b.change_pct - a.change_pct)
    case 'rating':
      return [...list].sort((a, b) => b.rating - a.rating)
    default:
      return list
  }
})

async function load() {
  loading.value = true
  error.value = null
  checkBackendHealth()
  void loadBrief() // 简报与行情并发，互不阻塞
  try {
    players.value = await api.listPlayers()
    updatedAt.value = new Date().toLocaleTimeString()
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : '加载选手列表失败'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  keyword.value = ''
  statusFilter.value = 'all'
  sortBy.value = 'default'
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2>选手市场</h2>
        <p class="updated" v-if="updatedAt && !loading && !error">更新于 {{ updatedAt }}</p>
      </div>
      <button class="refresh" :disabled="loading" @click="load">
        <span :class="['ico-refresh', { spinning: loading }]" aria-hidden="true">⟳</span> 刷新
      </button>
    </div>

    <!-- 今日智能体简报：一进首页就能看到智能体的判断，而不只是行情表 -->
    <section v-if="brief" class="brief" aria-label="今日智能体简报">
      <div class="brief-head">
        <span class="brief-tag">智能体简报</span>
        <span class="brief-src">{{ brief.source === 'llm' ? '模型生成' : '规则兜底' }}</span>
      </div>
      <p class="brief-summary">{{ brief.summary }}</p>
      <ul class="brief-items">
        <li v-for="(item, i) in brief.items" :key="i">
          <strong>{{ item.title }}</strong>
          <span>{{ item.detail }}</span>
        </li>
      </ul>
    </section>

    <!-- 工具条：搜索 + 筛选 + 排序（任务流最短化） -->
    <div class="toolbar">
      <input
        v-model="keyword"
        class="search"
        type="search"
        placeholder="搜索选手 / 战队…"
        aria-label="搜索选手或战队"
      />
      <div class="segment" role="group" aria-label="按交易状态筛选">
        <button
          v-for="opt in [
            { v: 'all', t: '全部' },
            { v: 'trading', t: '交易中' },
            { v: 'halted', t: '暂停' },
          ]"
          :key="opt.v"
          type="button"
          :class="['seg-btn', { active: statusFilter === opt.v }]"
          @click="statusFilter = opt.v as typeof statusFilter"
        >
          {{ opt.t }}
        </button>
      </div>
      <label class="sort">
        <span>排序</span>
        <select v-model="sortBy" aria-label="排序方式">
          <option value="default">默认</option>
          <option value="price">价格高→低</option>
          <option value="change">涨幅高→低</option>
          <option value="rating">评分高→低</option>
        </select>
      </label>
    </div>

    <!-- 加载态：骨架卡片，保持布局不跳动 -->
    <ul v-if="loading" class="grid" aria-busy="true" aria-label="加载选手列表">
      <li v-for="i in 8" :key="i" class="card skeleton">
        <span class="sk sk-name"></span><span class="sk sk-meta"></span><span class="sk sk-price"></span>
      </li>
    </ul>
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="players.length === 0">市场暂无选手</EmptyState>
    <EmptyState v-else-if="filtered.length === 0">
      没有符合条件的选手。
      <button type="button" class="link-btn" @click="resetFilters">清除筛选</button>
    </EmptyState>

    <ul v-else class="grid">
      <li
        v-for="p in filtered"
        :key="p.player_id"
        :class="['card', { suspended: p.status !== 'trading' }]"
      >
        <RouterLink :to="`/players/${p.player_id}`" class="card-link">
          <div class="top">
            <span class="name">{{ p.display_name || p.name }}</span>
            <StatusBadge :status="p.status" />
          </div>
          <div class="meta">
            <span>{{ p.team ?? '—' }}</span>
            <span class="role">{{ p.role ?? '—' }}</span>
          </div>
          <div class="price-row num">
            <span class="price">{{ money(p.current_price) }}</span>
            <span :class="['change', trendClass(p.change_pct)]">{{ pct(p.change_pct) }}</span>
          </div>
          <div class="rating-row">
            <span class="rating-label">模拟表现分</span>
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
.ico-refresh {
  display: inline-block;
}
.ico-refresh.spinning {
  animation: spin 0.9s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ---- 今日智能体简报 ---- */
.brief {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-md);
  background: var(--surface);
}
.brief-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}
.brief-tag {
  font-size: var(--fs-cap);
  padding: 1px 8px;
  border-radius: var(--radius-sm);
  background: var(--accent-dim, rgba(122, 162, 255, 0.16));
  color: var(--accent);
}
.brief-src {
  font-size: var(--fs-cap);
  color: var(--muted);
}
.brief-summary {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-body);
}
.brief-items {
  margin: 0;
  padding-left: 1.1em;
  display: grid;
  gap: 4px;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.brief-items strong {
  color: var(--text);
  margin-right: 6px;
}

/* ---- 工具条 ---- */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-top: var(--space-4);
}
.search {
  flex: 1;
  min-width: 180px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-body);
}
.search::placeholder {
  color: var(--muted);
}
.segment {
  display: inline-flex;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--surface);
}
.seg-btn {
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-aux);
  cursor: pointer;
}
.seg-btn.active {
  background: var(--up-bg);
  color: var(--accent);
  font-weight: 700;
}
.sort {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  color: var(--muted);
}
.sort select {
  padding: var(--space-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-aux);
}

/* ---- 卡片网格 ---- */
.grid {
  list-style: none;
  padding: 0;
  margin: var(--space-4) 0 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-4);
}
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition:
    box-shadow 0.15s ease,
    transform 0.15s ease,
    border-color 0.15s ease;
}
.card:hover {
  box-shadow: var(--shadow-2);
  transform: translateY(-2px);
  border-color: #3a3e46;
}
.card.suspended {
  opacity: 0.65;
}
.card-link {
  display: block;
  padding: var(--space-4);
  text-decoration: none;
  color: inherit;
}
.top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
}
.name {
  font-size: var(--fs-h3);
  font-weight: 700;
}
.meta {
  display: flex;
  gap: var(--space-2);
  color: var(--muted);
  font-size: var(--fs-aux);
  margin-top: 2px;
}
.role {
  padding: 0 6px;
  border-radius: 4px;
  background: var(--neutral-bg);
}
.price-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: var(--space-3);
}
.price {
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.change {
  font-size: var(--fs-body);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
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
  margin-top: var(--space-2);
  font-size: var(--fs-aux);
  color: var(--muted);
}
.rating {
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}
.link-btn {
  background: none;
  border: none;
  color: var(--accent);
  font-size: inherit;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

/* ---- 骨架屏 ---- */
.card.skeleton {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  pointer-events: none;
}
.sk {
  border-radius: 6px;
  background: var(--neutral-bg);
  animation: sk-pulse 1.2s ease-in-out infinite;
}
.sk-name {
  height: 20px;
  width: 60%;
}
.sk-meta {
  height: 12px;
  width: 40%;
}
.sk-price {
  height: 26px;
  width: 75%;
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

/* ===== 窄屏：工具条纵向堆叠，搜索占整行 ===== */
@media (max-width: 720px) {
  .toolbar {
    gap: var(--space-2);
  }
  .search {
    flex-basis: 100%;
  }
}
</style>