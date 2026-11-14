<script setup lang="ts">
/**
 * 白话导读：赛程页（/schedule）——给交易者看的"这一轮谁在打比赛、谁因此不能买"。
 *
 * 页面只有三块，从上到下就是你要做的三个决定：
 *   1. 选轮次（默认停在今天这一轮，也能左右翻）；
 *   2. 看本轮：对阵 + 暂停名单（点不进交易的那些人）+ 还能交易的名单；
 *   3. 看全季：28 轮一张表，点任意一行就切到那一轮。
 *
 * 算法不在这里写：派生规则来自 `src/core/schedule.ts`（`core_engine/schedule.py` 的移植），
 * 赛程数据来自 `src/data/demoSchedule.ts`（`scripts/build_schedule.py` 生成的镜像）。
 * 选手名单走 GET /api/players（契约 §4.2）；后端没起时只降级名单，赛程照常能看。
 */
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import LoadingState from '../components/LoadingState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import {
  DEFAULT_BLOCK,
  blocksOf,
  phaseOf,
  playingTeams,
  roundMatch,
  roundOfDate,
  rounds,
  schedule,
  suspendedPlayers,
  teamNames,
  todayIso,
  tradablePlayers,
  weekdayCn,
  type ScheduleMatch,
  type SchedulePlayer,
} from '../core/schedule'

/* ------------------------------------------------------------------ 数据装载 */

const today = todayIso()
const totalRounds = rounds()
const todayRound = roundOfDate(today)

const selected = ref(todayRound)
const players = ref<SchedulePlayer[]>([])
const rosterLoading = ref(true)
const rosterError = ref<string | null>(null)

async function loadRoster(): Promise<void> {
  rosterLoading.value = true
  rosterError.value = null
  try {
    players.value = await api.listPlayers()
  } catch (err) {
    rosterError.value = err instanceof ApiError ? err.message : '选手名单加载失败（后端未连接）'
    players.value = []
  } finally {
    rosterLoading.value = false
  }
}

onMounted(loadRoster)

/* -------------------------------------------------------------- 选中轮次派生 */

const names = teamNames()
const featuredRound = schedule.featured_round ? Number(schedule.featured_round) : null
const playersPerTeam = Number((schedule.rules ?? {}).suspended_players_per_round ?? 4) / 2

const selectedMatch = computed(() => roundMatch(selected.value))
const selectedPhase = computed(() => phaseOf(selectedMatch.value, today))
const phaseText: Record<string, string> = {
  played: '已结束',
  today: '今天开打',
  upcoming: '未开始',
}
const playingIds = computed(() => [...playingTeams(selected.value)])
const playingLabel = computed(() =>
  playingIds.value.map((id) => names.get(id) ?? String(id)).join(' / '),
)

const suspended = computed(() => suspendedPlayers(players.value, selected.value))
/** 可交易 = 赛程没停牌 且 没被运维手动冻结（后者后端结算时也会跳过） */
const tradable = computed(() =>
  tradablePlayers(players.value, selected.value).filter((player) => !isManual(player)),
)

/** 名单没加载时按规则给结论：每轮 2 队 × 每队 playersPerTeam 人 */
const suspendedCount = computed(() =>
  players.value.length ? suspended.value.length : 2 * playersPerTeam,
)
const tradableCount = computed(() =>
  players.value.length ? tradable.value.length : Math.max(16 - 2 * playersPerTeam, 0),
)

function isManual(player: SchedulePlayer): boolean {
  return String(player.status ?? 'trading') !== 'trading'
}

/** 手动冻结但本轮没有比赛的选手：他不能买的原因不是赛程，得单独说一句 */
const manualHalted = computed(() => {
  const haltedIds = new Set(suspended.value.map((player) => player.player_id))
  return players.value.filter((player) => isManual(player) && !haltedIds.has(player.player_id))
})

function teamOf(match: ScheduleMatch, side: 'team_a' | 'team_b'): string {
  const id = Number(match[side])
  return names.get(id) ?? String(id)
}

function displayName(player: SchedulePlayer): string {
  return player.display_name || player.name || `#${String(player.player_id ?? '?')}`
}

/* ----------------------------------------------------------------- 赛程表 */

const blocks = computed(() => blocksOf(DEFAULT_BLOCK))
const strip = computed(() =>
  schedule.matches.map((match) => ({
    round: match.round,
    day: match.played_at.slice(5),
    phase: phaseOf(match, today),
    featured: match.round === featuredRound,
  })),
)

function prevRound(): void {
  selected.value = Math.max(1, selected.value - 1)
}
function nextRound(): void {
  selected.value = Math.min(totalRounds, selected.value + 1)
}

function shortDate(iso: string): string {
  return `${Number(iso.slice(5, 7))}月${Number(iso.slice(8, 10))}日`
}
</script>

<template>
  <div class="page">
    <!-- ============ 页头 ============ -->
    <div class="page-head">
      <div>
        <h2>赛程</h2>
        <p class="sub">
          {{ schedule.season }} · 8 队单循环 · 共 {{ totalRounds }} 轮 · 每轮 1 场。
          <strong>本轮打比赛的两队（{{ playingLabel }}）暂停交易</strong>，其余选手照常买卖。
        </p>
      </div>
      <div class="head-right">
        <span class="today num">今天 {{ shortDate(today) }} · 第 {{ todayRound }} 轮</span>
        <button
          type="button"
          class="ghost"
          :disabled="selected === todayRound"
          @click="selected = todayRound"
        >
          跳到本轮
        </button>
      </div>
    </div>

    <!-- ============ 轮次 ============ -->
    <section class="card">
      <div class="round-bar">
        <button
          type="button"
          class="step"
          :disabled="selected <= 1"
          aria-label="上一轮"
          @click="prevRound"
        >
          ‹
        </button>
        <div class="strip" role="group" aria-label="轮次选择">
          <button
            v-for="item in strip"
            :key="item.round"
            type="button"
            :class="['chip', item.phase, { on: item.round === selected }]"
            :aria-pressed="item.round === selected"
            @click="selected = item.round"
          >
            <span class="chip-r num">{{ item.round }}</span>
            <span class="chip-d num"
              >{{ item.day }}<i v-if="item.featured" title="焦点局">★</i></span
            >
          </button>
        </div>
        <button
          type="button"
          class="step"
          :disabled="selected >= totalRounds"
          aria-label="下一轮"
          @click="nextRound"
        >
          ›
        </button>
      </div>
      <p class="legend">
        <span class="dot played"></span>已结束 <span class="dot today"></span>今天
        <span class="dot upcoming"></span>未开始
        <span class="mini">★ 焦点局 · 点一轮，下面的名单立刻重算</span>
      </p>
    </section>

    <!-- ============ 本轮 ============ -->
    <section class="card">
      <div class="match">
        <div class="match-main num">
          <strong>{{ names.get(Number(selectedMatch.team_a)) }}</strong>
          <span class="vs">vs</span>
          <strong>{{ names.get(Number(selectedMatch.team_b)) }}</strong>
        </div>
        <div class="match-meta">
          <span :class="['phase', selectedPhase]">{{ phaseText[selectedPhase] }}</span>
          <span>第 {{ selected }} 轮</span>
          <span>{{ selectedMatch.played_at }} {{ weekdayCn(selectedMatch.played_at) }}</span>
          <span v-if="selected === featuredRound" class="star">★ 焦点局</span>
        </div>
      </div>

      <div class="roster">
        <div class="col halt">
          <h4>
            <em class="num">{{ suspendedCount }}</em> 人暂停交易
          </h4>
          <LoadingState v-if="rosterLoading">读取选手名单…</LoadingState>
          <ul v-else-if="players.length" class="list">
            <li v-for="p in suspended" :key="p.player_id">
              <RouterLink :to="`/players/${p.player_id}`">{{ displayName(p) }}</RouterLink>
              <span class="team">{{ p.team }}</span>
              <StatusBadge status="suspended" />
            </li>
          </ul>
          <p v-else class="mini">
            {{ rosterError }}：按赛程给结论——本轮 {{ playingLabel }} 两队整队停牌（每队
            {{ playersPerTeam }} 人，共 {{ suspendedCount }} 人）。
          </p>
          <p v-if="manualHalted.length" class="mini">
            另有 {{ manualHalted.length }} 人暂停（非赛程原因）：{{
              manualHalted.map(displayName).join('、')
            }}
          </p>
        </div>

        <div class="col">
          <h4>
            <em class="num">{{ tradableCount }}</em> 人可交易
          </h4>
          <LoadingState v-if="rosterLoading">读取选手名单…</LoadingState>
          <div v-else-if="players.length" class="chips">
            <RouterLink
              v-for="p in tradable"
              :key="p.player_id"
              class="pchip"
              :to="`/players/${p.player_id}`"
            >
              {{ displayName(p) }}<small>{{ p.team }}</small>
            </RouterLink>
          </div>
          <p v-else class="mini">{{ rosterError }}：其余选手照常交易，价格照常重算。</p>
        </div>
      </div>
    </section>

    <!-- ============ 全季 ============ -->
    <section class="card">
      <h3 class="card-title">全季赛程</h3>
      <table>
        <thead>
          <tr>
            <th>轮次</th>
            <th>对阵</th>
            <th>比赛日</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(group, index) in blocks" :key="index">
            <tr class="group-row">
              <td colspan="4">第 {{ group[0]?.round }}–{{ group[group.length - 1]?.round }} 轮</td>
            </tr>
            <tr
              v-for="match in group"
              :key="match.round"
              :class="['row', { on: match.round === selected }]"
              @click="selected = match.round"
            >
              <td data-label="轮次" class="num">
                {{ match.round }}<i v-if="match.round === featuredRound" class="star">★</i>
              </td>
              <td data-label="对阵" class="vs-cell num">
                <b>{{ teamOf(match, 'team_a') }}</b>
                <span class="vs-mini">vs</span>
                <b>{{ teamOf(match, 'team_b') }}</b>
              </td>
              <td data-label="比赛日" class="num">{{ shortDate(match.played_at) }}</td>
              <td data-label="状态">
                <span :class="['tag', phaseOf(match, today)]">{{
                  phaseText[phaseOf(match, today)]
                }}</span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ===== 页头 ===== */
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.page-head h2 {
  margin: 0;
  font-size: var(--fs-h2);
}
.sub {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: var(--fs-aux);
  max-width: 60ch;
}
.sub strong {
  color: var(--warn);
  font-weight: 600;
}
.head-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.today {
  font-size: var(--fs-aux);
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.ghost {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-aux);
  cursor: pointer;
}
.ghost:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}
.ghost:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ===== 卡片 ===== */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.card-title {
  margin: 0;
  font-size: var(--fs-h3);
}

/* ===== 轮次条 ===== */
.round-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.step {
  flex-shrink: 0;
  width: 28px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--text);
  font-size: var(--fs-body);
  cursor: pointer;
  line-height: 1;
}
.step:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.strip {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: thin;
}
.chip {
  flex: 0 0 auto;
  min-width: 52px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 5px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--muted);
  cursor: pointer;
}
.chip .chip-r {
  font-size: var(--fs-body);
  font-weight: 800;
  color: var(--text);
}
.chip .chip-d {
  font-size: 11px;
}
.chip.played {
  opacity: 0.6;
}
.chip.today .chip-d {
  color: var(--warn);
}
.chip:hover {
  border-color: var(--accent);
}
.chip.on {
  border-color: var(--accent);
  background: var(--up-bg);
}
.chip.on .chip-r,
.chip.on .chip-d {
  color: var(--accent);
}
.chip-d i {
  font-style: normal;
  color: var(--warn);
  margin-left: 2px;
}
.legend {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-cap);
  color: var(--muted);
  flex-wrap: wrap;
}
.legend .mini {
  margin-left: auto;
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.dot.played,
.dot.upcoming {
  background: var(--muted);
}
.dot.today {
  background: var(--warn);
}

/* ===== 本轮对阵 ===== */
.match {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.match-main {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  font-size: var(--fs-h1);
  font-weight: 800;
}
.match-main .vs {
  color: var(--accent);
  font-size: var(--fs-h3);
  font-weight: 700;
}
.match-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  color: var(--muted);
  flex-wrap: wrap;
}
.match-meta .star {
  color: var(--warn);
}
.phase {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-cap);
}
.phase.played {
  background: var(--neutral-bg);
  color: var(--muted);
}
.phase.today {
  background: var(--warn-bg);
  color: var(--warn);
}
.phase.upcoming {
  background: var(--down-bg);
  color: var(--down);
}

/* ===== 名单 ===== */
.roster {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--space-3);
}
.col {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  min-width: 0;
}
.col.halt {
  background: var(--warn-bg);
  border-color: transparent;
}
.col h4 {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-body);
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.col h4 em {
  font-style: normal;
  font-size: var(--fs-h2);
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.list li {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  flex-wrap: wrap;
}
.list a {
  font-weight: 700;
  text-decoration: none;
}
.list a:hover {
  text-decoration: underline;
}
.list .team {
  color: var(--muted);
  font-size: var(--fs-cap);
}
.list .badge {
  margin-left: auto;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.pchip {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--surface-2);
  font-size: var(--fs-cap);
  text-decoration: none;
  color: var(--text);
}
.pchip small {
  color: var(--muted);
}
.pchip:hover {
  border-color: var(--down);
}
.mini {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--muted);
  line-height: 1.5;
}

/* ===== 赛程表 ===== */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-aux);
}
th,
td {
  padding: 9px var(--space-3);
  border-bottom: 1px solid var(--border);
  text-align: left;
}
tbody tr:last-child td {
  border-bottom: none;
}
th {
  color: var(--muted);
  font-weight: 600;
  font-size: var(--fs-cap);
}
.num {
  font-variant-numeric: tabular-nums;
}
tr.row {
  cursor: pointer;
}
tr.row:hover {
  background: var(--surface-2);
}
tr.row.on {
  background: var(--up-bg);
}
tr.row.on td {
  color: var(--text);
}
.group-row td {
  background: var(--surface-2);
  color: var(--muted);
  font-weight: 700;
  font-size: var(--fs-cap);
  padding: 5px var(--space-3);
}
td .star {
  font-style: normal;
  color: var(--warn);
  margin-left: 3px;
}
.vs-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.vs-cell b {
  font-weight: 600;
}
.vs-mini {
  color: var(--muted);
  font-size: var(--fs-cap);
}
.tag {
  display: inline-block;
  padding: 1px 9px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-cap);
  white-space: nowrap;
}
.tag.played,
.tag.upcoming {
  background: var(--neutral-bg);
  color: var(--muted);
}
.tag.today {
  background: var(--warn-bg);
  color: var(--warn);
}

/* ===== 响应式：表格转卡片 ===== */
@media (max-width: 720px) {
  .card {
    padding: var(--space-3);
  }
  .match-main {
    font-size: var(--fs-h2);
  }
  table {
    display: block;
  }
  thead {
    display: none;
  }
  tbody {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  tr.row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px var(--space-3);
    background: var(--surface-2);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
  }
  tr.row td {
    border: none;
    padding: 2px 0;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
  }
  tr.row td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: var(--fs-cap);
    flex-shrink: 0;
  }
  tr.row td:first-child {
    grid-column: 1 / -1;
    font-weight: 700;
  }
  .group-row td {
    border-radius: var(--radius-sm);
  }
}
</style>
