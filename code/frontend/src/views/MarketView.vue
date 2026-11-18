<script setup lang="ts">
/**
 * 白话导读：默认首页（URL 是 /），把 16 名选手做成一张可搜索、可排序、可筛选的行情列表。
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
import { TRADING } from '../core/schedule'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import { roundMatch, teamNames } from '../core/schedule'
import TeamLogo from '../components/TeamLogo.vue'
import { currentRound, haltReason, withRoundStatus } from '../core/tradingStatus'

const players = ref<PlayerSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
/** 系统状态可见：告诉用户"这批行情是什么时候拉的" */
const updatedAt = ref('')

/* ---- 今日智能体简报（第 8 轮：让智能体出现在首屏，而不是只藏在详情页） ---- */
type BriefItem = { title: string; detail: string; player_id?: number | null }
/**
 * 简报总述清洗（防守）：
 * 模型偶尔返回 JSON（`{"action":"HOLD","reason":"..."}`），后端旧版本会原样透传，
 * 前端必须再兜一层——界面上只允许出现一句话，不允许出现花括号/字段名/代码块。
 */
const WRAP_QUOTES: Record<string, string> = {
  '"': '"',
  "'": "'",
  '“': '”',
  '‘': '’',
  '「': '」',
  '『': '』',
}

/** 去掉模型给整句套的外层引号（最多 3 层），并合并多余空白 */
function tidySentence(text: string): string {
  let t = text.trim()
  for (let i = 0; i < 3; i += 1) {
    if (t.length >= 2 && WRAP_QUOTES[t[0]!] === t[t.length - 1]) t = t.slice(1, -1).trim()
    else break
  }
  return t.replace(/\s+/g, ' ').trim()
}

function cleanSummary(raw: string | null | undefined): string {
  let text = (raw ?? '').trim()
  if (!text) return ''
  text = text.replace(/^```\w*\s*/, '').replace(/\s*```$/, '').trim()
  if (text.startsWith('{')) {
    const match = text.match(/"(?:reason|summary|text)"\s*:\s*"([^"]*)/)
    const picked = match?.[1]
    if (picked) return tidySentence(picked)
    return tidySentence(
      text
        .replace(/[{}"]/g, '')
        .replace(/\b(action|risk_level|reason|summary|text)\s*[:：]\s*/g, ''),
    )
  }
  return tidySentence(text)
}

const brief = ref<{ summary: string; items: BriefItem[]; source: string } | null>(null)
/** 简报默认只显示一句话；要看三条要点再展开 */
const briefOpen = ref(false)

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

/**
 * 市场页显示的是"现在能不能买"：后端 status 只有初始/手动值，
 * 本轮停牌由赛程派生（`core/tradingStatus.ts`，与后端 suspension_reason 同口径）。
 */
const round = currentRound()
/**
 * 在册名单 + 本轮派生状态。
 * halt_note 必须用**原始**选手算：派生后的 status 已经是 suspended，再喂给 haltReason
 * 会被当成手动冻结（实测踩过：悬浮提示变成"状态 suspended（手动暂停）"）。
 */
const listed = computed(() =>
  players.value.map((player) => ({
    ...withRoundStatus(player, round),
    halt_note: haltReason(player, round),
  })),
)
const haltedCount = computed(() => listed.value.filter((p) => p.status !== TRADING).length)
/** 今天是不是比赛日：不是就没有“本轮停牌”，横幅换成“休赛日”而不是硬指一场比赛 */
const liveMatch = computed(() => (round === null ? null : roundMatch(round)))

/** 本轮对阵的两支队伍（队标 + 队名）：用 team_id → 名字，避免从 "A vs B" 反解 */
const teamNameMap = teamNames()
const matchSides = computed(() => {
  const m = liveMatch.value
  if (!m) return null
  const a = Number(m.team_a)
  const b = Number(m.team_b)
  return {
    a: { id: a, name: teamNameMap.get(a) ?? String(m.team_a) },
    b: { id: b, name: teamNameMap.get(b) ?? String(m.team_b) },
  }
})

/** 简报来源做成图标 + tooltip，屏幕上不再占一行字 */
const sourceLabel = computed(() =>
  brief.value?.source === 'llm' ? 'AI 生成简报' : '简化模式（未连接模型）',
)

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  let list = listed.value
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
  <article class="market">
    <header class="masthead">
      <div>
        <h1>市场</h1>
        <p v-if="updatedAt && !loading && !error" class="mast-meta">
          16 名选手 · 更新于 {{ updatedAt }}
        </p>
      </div>
      <button type="button" class="quiet-btn" :disabled="loading" @click="load">
        <span :class="['ico-refresh', { spinning: loading }]" aria-hidden="true">⟳</span>
        {{ loading ? '刷新中' : '刷新' }}
      </button>
    </header>

    <!-- 今日简报：一句话说结论，要点收起来 -->
    <section v-if="brief" class="lede-block" aria-label="今日简报">
      <p class="lede">{{ cleanSummary(brief.summary) }}</p>
      <div class="lede-actions">
        <span class="src-ico" role="img" :aria-label="sourceLabel" :title="sourceLabel">
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d="M8 2.2 9.3 6 13 7.2 9.3 8.4 8 12.2 6.7 8.4 3 7.2 6.7 6Z" />
          </svg>
        </span>
        <button
          v-if="brief.items.length"
          type="button"
          class="icon-btn"
          :class="{ 'is-open': briefOpen }"
          :aria-expanded="briefOpen"
          @click="briefOpen = !briefOpen"
        >
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6.2 8 10.2l4-4" /></svg>
          <span class="sr-only">{{ briefOpen ? '收起要点' : '展开要点' }}</span>
        </button>
      </div>
      <ul v-if="briefOpen" class="lede-items">
        <li v-for="(item, i) in brief.items" :key="i">
          <span class="item-ico" aria-hidden="true">
            <svg v-if="i === 0" viewBox="0 0 16 16"><path d="M3 11.2 7 7.2l3 2 3-5" /></svg>
            <svg v-else-if="i === 1" viewBox="0 0 16 16"><path d="M8 3v8M5 8l3 3 3-3" /></svg>
            <svg v-else viewBox="0 0 16 16">
              <circle cx="8" cy="8" r="5.6" />
              <path d="M6.6 6.1v3.8M9.4 6.1v3.8" />
            </svg>
          </span>
          <span class="k">{{ item.title }}</span>
          <span class="v">{{ item.detail }}</span>
        </li>
      </ul>
    </section>

    <div class="round-line match-line">
      <template v-if="liveMatch && matchSides">
        <span class="round-chip num">第 {{ round }} 轮</span>
        <span class="match">
          <span class="side">
            <TeamLogo :team="matchSides.a.id" :name="matchSides.a.name" size="xs" />
            <span class="team-name">{{ matchSides.a.name }}</span>
          </span>
          <span class="vs" aria-hidden="true">vs</span>
          <span class="side side-b">
            <span class="team-name">{{ matchSides.b.name }}</span>
            <TeamLogo :team="matchSides.b.id" :name="matchSides.b.name" size="xs" />
          </span>
        </span>
        <span
          class="halt-ico num"
          :title="`比赛中，${haltedCount} 人暂停交易`"
          aria-hidden="true"
        >
          <svg viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="5.6" />
            <path d="M6.6 6.1v3.8M9.4 6.1v3.8" />
          </svg>
          {{ haltedCount }} 人
        </span>
        <span class="sr-only">比赛中，{{ haltedCount }} 人暂停交易</span>
      </template>
      <template v-else>
        <span class="round-chip">休赛日</span>
        <span class="rest">全部选手照常交易</span>
      </template>
      <RouterLink class="icon-btn rn-link" to="/schedule" aria-label="查看赛程" title="查看赛程">
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M3 4.5h10v9H3zM3 7h10M5.5 2.8V5M10.5 2.8V5" />
        </svg>
        <span class="sr-only">看赛程</span>
      </RouterLink>
    </div>

    <div class="controls">
      <input
        v-model="keyword"
        class="search"
        type="search"
        placeholder="搜索选手 / 战队"
        aria-label="搜索选手或战队"
      />
      <div class="filters" role="group" aria-label="按交易状态筛选">
        <button
          v-for="opt in [
            { v: 'all', t: '全部' },
            { v: 'trading', t: '交易中' },
            { v: 'halted', t: '停牌' },
          ]"
          :key="opt.v"
          type="button"
          :class="['filter', { active: statusFilter === opt.v }]"
          @click="statusFilter = opt.v as typeof statusFilter"
        >
          {{ opt.t }}
        </button>
      </div>
      <label class="sort">
        <select v-model="sortBy" aria-label="排序方式">
          <option value="default">默认排序</option>
          <option value="price">价格从高到低</option>
          <option value="change">涨幅从高到低</option>
          <option value="rating">评分从高到低</option>
        </select>
      </label>
    </div>

    <ul v-if="loading" class="grid" aria-busy="true" aria-label="加载选手列表">
      <li v-for="i in 6" :key="i" class="p-card skeleton">
        <span class="sk sk-name"></span>
        <span class="sk sk-meta"></span>
        <span class="sk sk-price"></span>
      </li>
    </ul>
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="players.length === 0">市场暂无选手</EmptyState>
    <EmptyState v-else-if="filtered.length === 0">
      没有符合条件的选手。
      <button type="button" class="quiet-link" @click="resetFilters">清除筛选</button>
    </EmptyState>

    <ul v-else class="grid">
      <li
        v-for="p in filtered"
        :key="p.player_id"
        :class="['p-card', { suspended: p.status !== TRADING }]"
        :title="p.halt_note ?? undefined"
      >
        <RouterLink :to="`/players/${p.player_id}`" class="p-link">
          <div class="p-top">
            <span class="p-name">{{ p.display_name || p.name }}</span>
            <span :class="['p-status', p.status === TRADING ? 'on' : 'off']">
              <i aria-hidden="true"></i>{{ p.status === TRADING ? '交易中' : '停牌' }}
            </span>
          </div>
          <p class="p-meta">
            {{ p.team ?? '—' }}<template v-if="p.role"> · {{ p.role }}</template>
          </p>
          <p class="p-price">
            <span class="num">{{ money(p.current_price) }}</span>
            <span :class="['p-chg', trendClass(p.change_pct)]">{{ pct(p.change_pct) }}</span>
          </p>
        </RouterLink>
      </li>
    </ul>
  </article>
</template>

<style scoped>
/* 市场页（纸感）：一屏 3 列 × 2 行 = 6 张卡；区块之间用留白分开，不用分割线堆叠 */
.market {
  display: flex;
  flex-direction: column;
}

/* ===== 页头 ===== */
.masthead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.masthead h1 {
  margin: 0;
  font-size: var(--fs-h1);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.mast-meta {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--faint);
}
.quiet-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
  cursor: progress;
  opacity: 0.6;
}
.ico-refresh {
  display: inline-block;
  font-size: 15px;
  line-height: 1;
}
.spinning {
  animation: spin 0.9s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .spinning {
    animation: none;
  }
}

/* ===== 一句话简报 ===== */
.lede-block {
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.lede {
  margin: 0;
  max-width: 56em;
  font-size: var(--fs-body);
  line-height: var(--line-height-body);
  color: var(--text);
  text-wrap: pretty;
}
.lede-actions {
  margin-top: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--faint);
}

/* 图标按钮：默认低调，hover/展开时提一点；44px 点击区 */
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin-left: -8px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--faint);
  cursor: pointer;
}
.icon-btn:hover {
  color: var(--text);
  background: var(--neutral-bg);
}
.icon-btn:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
.icon-btn svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform var(--motion-fast) var(--motion-ease);
}
.icon-btn.is-open svg {
  transform: rotate(180deg);
}
@media (prefers-reduced-motion: reduce) {
  .icon-btn svg {
    transition: none;
  }
}
.src-ico {
  display: inline-flex;
  align-items: center;
  color: var(--faint);
}
.src-ico svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* 屏幕阅读器专用文字（图标按钮/图标数字的可读替代） */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
.lede-items {
  list-style: none;
  margin: var(--space-3) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-cap);
}
.lede-items li {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  line-height: 1.6;
}
.lede-items .item-ico {
  flex: none;
  width: 14px;
  align-self: center;
  color: var(--faint);
}
.lede-items .item-ico svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.lede-items .k {
  flex: none;
  min-width: 4.2em;
  color: var(--faint);
}
.lede-items .v {
  color: var(--text);
}
@media (max-width: 600px) {
  .lede-items li {
    flex-wrap: wrap;
  }
  .lede-items .k {
    min-width: 0;
  }
}

/* ===== 轮次提示 ===== */
/* 比赛行：轮次 + 队标对阵 + 停牌人数 + 赛程图标，基本不用句子 */
.match-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin: 0 0 var(--space-6);
  font-size: var(--fs-aux);
  color: var(--muted);
}
.round-chip {
  color: var(--faint);
  font-size: var(--fs-cap);
  white-space: nowrap;
}
.match {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}
.match .side {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.match .side-b {
  flex-direction: row;
}
.team-name {
  color: var(--text);
  font-size: var(--fs-cap);
  font-weight: 500;
  white-space: nowrap;
}
.match .vs {
  color: var(--faint);
  font-size: var(--fs-cap);
}
.halt-ico {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--halt);
  font-variant-numeric: tabular-nums;
}
.halt-ico svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
}
.rest {
  color: var(--faint);
}
.match-line .rn-link {
  margin-left: 0;
}

/* ===== 搜索 / 筛选 / 排序 ===== */
.controls {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  margin-bottom: var(--space-5);
}
.search {
  width: 240px;
  padding: var(--space-2) 0;
  border: 0;
  border-bottom: 1px solid var(--color-border);
  background: none;
  color: var(--text);
  font: inherit;
  font-size: var(--fs-body);
}
.search::placeholder {
  color: var(--faint);
}
.search:focus {
  outline: none;
  border-bottom-color: var(--color-border-strong);
}
.filters {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.filter {
  padding: 0;
  border: 0;
  background: none;
  color: var(--faint);
  font: inherit;
  font-size: var(--fs-aux);
  cursor: pointer;
}
.filter:hover {
  color: var(--text);
}
.filter.active {
  color: var(--text);
  font-weight: 600;
  box-shadow: inset 0 -2px 0 var(--color-text);
}
.sort {
  margin-left: auto;
}
.sort select {
  border: 0;
  background: none;
  color: var(--faint);
  font: inherit;
  font-size: var(--fs-aux);
  cursor: pointer;
}
.sort select:hover {
  color: var(--text);
}

/* ===== 选手卡：一屏 6 张，留白优先 ===== */
.grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}
.p-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: border-color var(--motion-fast) var(--motion-ease);
}
.p-card:hover {
  border-color: var(--color-border-strong);
}
.p-link {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  color: inherit;
  text-decoration: none;
}
.p-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}
.p-name {
  font-size: var(--fs-h3);
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
}
.p-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--fs-cap);
  color: var(--faint);
  white-space: nowrap;
}
.p-status i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}
.p-status.on {
  color: var(--down);
}
.p-status.off {
  color: var(--halt);
}
.p-meta {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--muted);
  line-height: 1.4;
}
.p-price {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin: 0;
}
.p-price .num {
  font-size: 26px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--text);
}
.p-chg {
  font-size: var(--fs-aux);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}
.p-chg.up {
  color: var(--up-text);
}
.p-chg.down {
  color: var(--down);
}
.p-chg.flat {
  color: var(--muted);
}

/* 骨架 */
.skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
}
.sk {
  display: block;
  border-radius: 4px;
  background: var(--neutral-bg);
  animation: sk-pulse 1.2s ease-in-out infinite;
}
.sk-name {
  width: 46%;
  height: 18px;
}
.sk-meta {
  width: 64%;
  height: 12px;
}
.sk-price {
  width: 38%;
  height: 24px;
}
@keyframes sk-pulse {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.85;
  }
}

/* ===== 窄屏：2 列 → 1 列 ===== */
@media (max-width: 1100px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 720px) {
  .grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .masthead {
    margin-bottom: var(--space-5);
  }
  .controls {
    flex-wrap: wrap;
    gap: var(--space-4);
  }
  .search {
    width: 100%;
  }
  .sort {
    margin-left: 0;
  }
  .p-price .num {
    font-size: 24px;
  }
}
</style>
