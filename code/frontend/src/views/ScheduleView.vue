<script setup lang="ts">
/**
 * 白话导读：赛程页（/schedule）——给交易者看的"这一轮谁在打比赛"。
 *
 * 页面只有三块，从上到下就是你要做的三个决定：
 *   1. 选轮次（默认停在今天这一轮，也能左右翻）；选中的那个 chip 会自动滚到条带正中间，
 *      于是“轮次 + 日期”始终在屏幕中央——翻到列表最底下点一行也不会丢掉当前定位；
 *   2. 看本轮：轮次卡底部那一行对阵——哪两队在场上（这两队整队停牌，页头那行字已经把
 *      结论说完了；名单两块按需求下线，具体是谁不能买去市场页看）；
 *   3. 看全季：一张“比赛列表”——**没比的按时间顺序在上面，比过的按时间逆序在下面**，
 *      打开先看到“接下来打谁”，往下翻才是历史；点任意一行就切到那一轮。
 *
 * 算法不在这里写：派生规则来自 `src/core/schedule.ts`（`core_engine/schedule.py` 的移植），
 * 赛程数据来自 `src/data/demoSchedule.ts`（`scripts/build_schedule.py` 生成的镜像）。
 *
 * 这页**不查选手名单**：原来那两块"N 人暂停交易 / M 人可交易"按需求删掉了，
 * 具体是谁不能买去市场页看（横幅 + 卡片状态），拦单规则在接口侧 `rules.ensure_tradable_now`。
 * 好处是赛程页变成纯静态派生：后端起没起都一个样，也不会出现"名单加载中"。
 *
 * 8 支队伍的队标（对阵大字与比赛列表里的小图标）来自 `src/data/teamLogos.ts`，
 * 图片文件在 `src/assets/teams/`（离线本地文件，来源与授权见该目录 SOURCES.md），
 * 渲染统一走 `src/components/TeamLogo.vue`：认不到队伍或图加载失败就退成队名首字母。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { money, pct, trendClass } from '../utils/format'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { PlayerSummary } from '../api/types'
import TeamLogo from '../components/TeamLogo.vue'
import {
  DEFAULT_BLOCK,
  blocksOf,
  liveRound,
  phaseOf,
  playingTeams,
  roundMatch,
  resolveTeamId,
  roundOfDate,
  rounds,
  schedule,
  teamNames,
  todayIso,
  weekdayCn,
  type ScheduleMatch,
} from '../core/schedule'

/* ------------------------------------------------------------------ 轮次定位 */

const today = todayIso()
const totalRounds = rounds()
/**
 * 今天是不是比赛日（口径与后端 `core_engine.current_round` 一致：按 UTC 比赛日查赛程）。
 * 休赛日不该假装"今天是第 1 轮"——市场页已经会显示"休赛日"，这里必须同一个说法。
 */
const liveRoundNo = liveRound()
const isRestDay = liveRoundNo === null
const lastPlayedAt = schedule.matches[totalRounds - 1]?.played_at ?? ''
/** 默认停在今天这一轮；休赛日停在"最近可看的一轮"（赛季结束后就停在最后一轮） */
const todayRound = liveRoundNo ?? (today > lastPlayedAt ? totalRounds : roundOfDate(today))

const SCHEDULE_ROUND_KEY = 'playerstock.schedule.round.v1'
/** 上次浏览到第几轮（从比赛详情/其它页返回时接着看，而不是跳回今天） */
function readSelectedRound(): number | null {
  try {
    const raw = sessionStorage.getItem(SCHEDULE_ROUND_KEY)
    const value = raw ? Number(JSON.parse(raw)) : NaN
    return Number.isInteger(value) && value >= 1 && value <= totalRounds ? value : null
  } catch {
    return null
  }
}
const selected = ref(readSelectedRound() ?? todayRound)

/* -------------------------------------------------------------- 选中轮次派生 */

const names = teamNames()
const featuredRound = schedule.featured_round ? Number(schedule.featured_round) : null
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

function teamOf(match: ScheduleMatch, side: 'team_a' | 'team_b'): string {
  const id = Number(match[side])
  return names.get(id) ?? String(id)
}

/* ----------------------------------------------------------------- 赛程表 */

/* ---------------- 比赛列表：未比的按时间顺序在上，比过的按时间逆序在下 ---------------- */

/**
 * 排布口径参考 KPL 小助手的“比赛列表”：没比的（含今天开打）按时间升序放上面，
 * 比过的按时间降序放下面——打开页面第一眼是“接下来打谁”，往下翻才是历史。
 *
 * 分组仍跟着赛程算法的“每 4 轮一组”走（`blocksOf`），这样“每 4 轮 8 队各出场一次”
 * 在列表里依旧看得见；正好跨在“今天”的那一组会被拆成两截（比过的 1 轮 / 没比的 3 轮），
 * 各自归到对应区块，组头按实际轮次范围写，不会假装整组都打完了。
 */
function groupLabel(matches: ScheduleMatch[]): string {
  const numbers = matches.map((match) => match.round)
  const lo = Math.min(...numbers)
  const hi = Math.max(...numbers)
  return lo === hi ? `第 ${lo} 轮` : `第 ${lo}–${hi} 轮`
}

/** 一个区块 = 一组轮次 + 它在该区块里的比赛 */
interface ScheduleSection {
  key: string
  label: string
  tone: 'up' | 'down'
  matches: ScheduleMatch[]
}

function sectionOf(group: ScheduleMatch[], tone: 'up' | 'down'): ScheduleSection {
  const label = groupLabel(group)
  return {
    key: `${tone}-${label}`,
    label: `${label} · ${tone === 'up' ? '未开始' : '已结束'}`,
    tone,
    matches: group,
  }
}

const blocks = blocksOf(DEFAULT_BLOCK)

/** 未开始（含今天开打）：组内升序、组间升序 */
const upcomingSections: ScheduleSection[] = blocks
  .map((group) => group.filter((match) => phaseOf(match, today) !== 'played'))
  .filter((group) => group.length > 0)
  .map((group) => sectionOf(group, 'up'))

/** 已结束：组内降序（最近一场排最前），组间也降序 */
const playedSections: ScheduleSection[] = blocks
  .map((group) => group.filter((match) => phaseOf(match, today) === 'played').reverse())
  .filter((group) => group.length > 0)
  .reverse()
  .map((group) => sectionOf(group, 'down'))

const sections: ScheduleSection[] = [...upcomingSections, ...playedSections]
const upcomingCount = upcomingSections.reduce((sum, item) => sum + item.matches.length, 0)
const playedCount = playedSections.reduce((sum, item) => sum + item.matches.length, 0)
const strip = computed(() =>
  schedule.matches.map((match) => ({
    round: match.round,
    day: match.played_at.slice(5),
    phase: phaseOf(match, today),
    featured: match.round === featuredRound,
  })),
)

const stripEl = ref<HTMLElement | null>(null)

/** 滚动动效跟着系统的“减少动效”偏好走，录屏 / 答辩时不会晃眼 */
function scrollBehavior(): ScrollBehavior {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
}

/**
 * 把选中的那一轮滚到条带正中间（chip 上同时写着轮次和日期，居中一次就都稳住了）。
 *
 * 两个实现细节：
 * 1. 用 `getBoundingClientRect` 而不是 `offsetLeft`——后者相对 `offsetParent` 算，
 *    外层卡片有没有 `position` 会改变参照系，rect 不受这个影响；
 * 2. 整条都不在视野里时（点了比赛列表最底下那一行），先 `scrollIntoView` 把它带回来，
 *    否则“居中”是居在屏幕外的中间，没人看得见。
 */
async function centerSelectedRound(behavior: ScrollBehavior = scrollBehavior()): Promise<void> {
  await nextTick()
  const bar = stripEl.value
  if (!bar) return
  const chip = bar.querySelector<HTMLElement>('.chip.on')
  if (!chip) return

  const before = bar.getBoundingClientRect()
  const offscreen = before.bottom <= 0 || before.top >= window.innerHeight
  if (offscreen && typeof bar.scrollIntoView === 'function') {
    bar.scrollIntoView({ block: 'center', behavior })
  }

  const barBox = bar.getBoundingClientRect()
  const chipBox = chip.getBoundingClientRect()
  const left = bar.scrollLeft + (chipBox.left - barBox.left) - (bar.clientWidth - chipBox.width) / 2
  const next = Math.max(0, left)
  if (typeof bar.scrollTo === 'function') {
    bar.scrollTo({ left: next, behavior })
  } else {
    // jsdom / 老浏览器没有 Element.scrollTo，退回直接写 scrollLeft
    bar.scrollLeft = next
  }
}

/* 视口一变（转屏、改窗口大小、手机地址栏收起）条带宽度就变了，原来算好的居中会偏，
   所以 resize 之后按当前宽度重算一次；用 rAF 合并连续 resize，别一帧里滚十几回。 */
let resizeRaf = 0
function onViewportChange(): void {
  cancelAnimationFrame(resizeRaf)
  resizeRaf = requestAnimationFrame(() => void centerSelectedRound('auto'))
}

/** 换轮次就重新居中：左右翻页、点 chip、点列表行、回到今日，全走同一个 `selected` */
watch(selected, (value) => {
  try {
    sessionStorage.setItem(SCHEDULE_ROUND_KEY, JSON.stringify(value))
  } catch {
    /* 隐私模式存不下：只影响「回来时接不接着看」，不影响当前操作 */
  }
  void centerSelectedRound()
})
onMounted(() => {
  void centerSelectedRound('auto')
  window.addEventListener('resize', onViewportChange)
  window.addEventListener('keydown', onDrawerKeydown)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(resizeRaf)
  window.removeEventListener('resize', onViewportChange)
  window.removeEventListener('keydown', onDrawerKeydown)
  document.body.style.overflow = ''
})

function prevRound(): void {
  selected.value = Math.max(1, selected.value - 1)
}
function nextRound(): void {
  selected.value = Math.min(totalRounds, selected.value + 1)
}

/* ------------------------------------------------------------ 比赛详情抽屉 */

/**
 * 点任意一行比赛 → 右侧抽屉显示这场两队 4 名选手（名字/位置/现价/涨跌/交易状态），
 * 点选手进详情页看图表、AI 建议并下单（赛程页只做"看人"，不做交易，避免误操作）。
 *
 * 数据懒加载：赛程本身是纯静态派生（离线也能看），只有真正点开时才请求 /api/players；
 * 成功后缓存，反复点不同场次不再重复请求；失败给"重试"，不影响赛程本身。
 */
const drawerRound = ref<number | null>(null)
const drawerMatch = computed(() =>
  drawerRound.value === null ? null : roundMatch(drawerRound.value),
)
const drawerPhase = computed(() =>
  drawerMatch.value ? phaseOf(drawerMatch.value, today) : null,
)
/** 只有"正在打的那一轮"这两队才是此刻停牌；看历史/未来场次不能误标成停牌 */
const drawerHalted = computed(
  () => drawerRound.value !== null && drawerRound.value === liveRoundNo,
)
const drawerNote = computed(() => {
  if (drawerPhase.value === 'played') return '这场比赛已结束；选手现在可正常交易。'
  if (drawerHalted.value) return '这两支队伍本轮停牌（比赛期间不可交易），其余选手照常买卖。'
  return '这场比赛还没打；到这一轮时，这两队选手会暂停交易。'
})

const drawerTeamIds = computed(() => {
  const m = drawerMatch.value
  return m ? [Number(m.team_a), Number(m.team_b)] : []
})
const players = ref<PlayerSummary[]>([])
const playersLoading = ref(false)
const playersError = ref<string | null>(null)
let playersLoaded = false

const drawerTeams = computed(() =>
  drawerTeamIds.value.map((id) => ({
    id,
    name: names.get(id) ?? String(id),
    players: players.value.filter((p) => resolveTeamId(p.team ?? '') === id),
  })),
)

async function loadPlayers(force = false): Promise<void> {
  if (playersLoading.value || (playersLoaded && !force)) return
  playersLoading.value = true
  playersError.value = null
  try {
    players.value = await api.listPlayers()
    playersLoaded = true
  } catch (err) {
    playersError.value = err instanceof ApiError ? err.message : '选手数据加载失败'
  } finally {
    playersLoading.value = false
  }
}

const closeBtn = ref<HTMLButtonElement | null>(null)

function openMatchDrawer(round: number): void {
  selected.value = round
  drawerRound.value = round
  void loadPlayers()
}
function closeMatchDrawer(): void {
  drawerRound.value = null
}

function onDrawerKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && drawerRound.value !== null) closeMatchDrawer()
}

watch(drawerRound, async (value) => {
  document.body.style.overflow = value === null ? '' : 'hidden'
  if (value !== null) {
    await nextTick()
    closeBtn.value?.focus()
  } else {
    document.body.style.overflow = ''
  }
})

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
          <span class="sub-meta"
            >{{ schedule.season }} · 8 队单循环 · 共 {{ totalRounds }} 轮 · 每轮 1 场</span
          >
          <span
            class="sub-note"
            :title="`第 ${selected} 轮：${playingLabel} 比赛中暂停交易，其余选手照常买卖`"
          ><strong class="sub-halt"
              >第 {{ selected }} 轮打比赛的两队（{{ playingLabel }}）暂停交易</strong
            >，其余选手照常买卖。</span
          >
        </p>
      </div>
      <div class="head-right">
        <span class="today num">
          今天 {{ shortDate(today) }} ·
          <template v-if="isRestDay">休赛日（浏览第 {{ todayRound }} 轮）</template>
          <template v-else>第 {{ todayRound }} 轮</template>
        </span>
        <button
          type="button"
          class="ghost"
          :disabled="selected === todayRound"
          @click="selected = todayRound"
        >
          回到今日
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
        <div ref="stripEl" class="strip" role="group" aria-label="轮次选择">
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
        <span class="lg"><span class="dot played"></span>已结束</span>
        <span class="lg"><span class="dot today"></span>今天</span>
        <span class="lg"><span class="dot upcoming"></span>未开始</span>
        <span class="mini">★ 焦点局 · 点一轮，对阵与列表高亮跟着切换</span>
      </p>
      <div class="match">
        <div class="match-main num">
          <span class="side">
            <TeamLogo
              :team="Number(selectedMatch.team_a)"
              :name="teamOf(selectedMatch, 'team_a')"
              size="md"
            />
            <strong>{{ teamOf(selectedMatch, 'team_a') }}</strong>
          </span>
          <span class="vs">vs</span>
          <span class="side">
            <TeamLogo
              :team="Number(selectedMatch.team_b)"
              :name="teamOf(selectedMatch, 'team_b')"
              size="md"
            />
            <strong>{{ teamOf(selectedMatch, 'team_b') }}</strong>
          </span>
        </div>
        <div class="match-meta">
          <span :class="['phase', selectedPhase]">{{ phaseText[selectedPhase] }}</span>
          <span>第 {{ selected }} 轮</span>
          <span>{{ selectedMatch.played_at }} {{ weekdayCn(selectedMatch.played_at) }}</span>
          <span v-if="selected === featuredRound" class="star">★ 焦点局</span>
        </div>
      </div>
    </section>

    <!-- ====== 比赛列表：未比的在上（时间顺序）· 比过的在下（时间逆序） ====== -->
    <section class="card">
      <div class="list-head">
        <h3 class="card-title">比赛列表</h3>
        <p class="legend">
          <span class="lg"
            ><span class="dot upcoming"></span>未开始 {{ upcomingCount }} 场 · 时间顺序在上</span
          >
          <span class="lg"
            ><span class="dot played"></span>已结束 {{ playedCount }} 场 · 时间逆序在下</span
          >
          <span class="mini">点任意一行，展开这场比赛的选手</span>
        </p>
      </div>
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
          <template v-for="section in sections" :key="section.key">
            <tr :class="['group-row', section.tone]">
              <td colspan="4">{{ section.label }}</td>
            </tr>
            <tr
              v-for="match in section.matches"
              :key="match.round"
              :class="['row', { on: match.round === selected }]"
              tabindex="0"
              role="button"
              :aria-label="`第 ${match.round} 轮：查看这场比赛的选手`"
              @click="openMatchDrawer(match.round)"
              @keydown.enter.prevent="openMatchDrawer(match.round)"
              @keydown.space.prevent="openMatchDrawer(match.round)"
            >
              <td data-label="轮次" class="num c-round">
                {{ match.round }}<i v-if="match.round === featuredRound" class="star">★</i>
              </td>
              <td data-label="对阵" class="vs-cell num c-teams">
                <span class="side">
                  <TeamLogo
                    :team="Number(match.team_a)"
                    :name="teamOf(match, 'team_a')"
                    size="xs"
                  />
                  <b>{{ teamOf(match, 'team_a') }}</b>
                </span>
                <span class="vs-mini">vs</span>
                <span class="side">
                  <b>{{ teamOf(match, 'team_b') }}</b>
                  <TeamLogo
                    :team="Number(match.team_b)"
                    :name="teamOf(match, 'team_b')"
                    size="xs"
                  />
                </span>
              </td>
              <td data-label="比赛日" class="num c-date">
                {{ shortDate(match.played_at)
                }}<small class="weekday">{{ weekdayCn(match.played_at) }}</small>
              </td>
              <td data-label="状态" class="c-status">
                <span :class="['tag', phaseOf(match, today)]">{{
                  phaseText[phaseOf(match, today)]
                }}</span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>

    <!-- ====== 比赛抽屉：两队 4 名选手 + 进详情页入口 ====== -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="drawerMatch" class="drawer-scrim" @click="closeMatchDrawer"></div>
      </Transition>
      <Transition name="drawer">
        <aside
          v-if="drawerMatch && drawerPhase"
          class="match-drawer"
          role="dialog"
          aria-modal="true"
          :aria-label="`第 ${drawerRound} 轮比赛选手`"
        >
          <header class="drawer-head">
            <div>
              <p class="drawer-kicker num">
                第 {{ drawerRound }} 轮
                <span :class="['tag', drawerPhase]">{{ phaseText[drawerPhase] }}</span>
              </p>
              <h3 class="drawer-title num">
                <TeamLogo
                  :team="drawerTeams[0]?.id"
                  :name="drawerTeams[0]?.name"
                  size="xs"
                />
                {{ drawerTeams[0]?.name }}
                <span class="vs">vs</span>
                {{ drawerTeams[1]?.name }}
                <TeamLogo
                  :team="drawerTeams[1]?.id"
                  :name="drawerTeams[1]?.name"
                  size="xs"
                />
              </h3>
            </div>
            <button
              ref="closeBtn"
              type="button"
              class="drawer-close"
              aria-label="关闭"
              @click="closeMatchDrawer"
            >
              ✕
            </button>
          </header>

          <p class="drawer-note">{{ drawerNote }}</p>

          <div v-if="playersLoading" class="drawer-skeleton" aria-busy="true" aria-label="加载选手">
            <div v-for="i in 4" :key="i" class="sk-row">
              <span class="sk sk-name"></span><span class="sk sk-mid"></span
              ><span class="sk sk-num"></span>
            </div>
          </div>
          <div v-else-if="playersError" class="drawer-error">
            <p>{{ playersError }}</p>
            <button type="button" @click="loadPlayers(true)">重试</button>
          </div>
          <div v-else class="drawer-body">
            <section v-for="team in drawerTeams" :key="team.id" class="drawer-team">
              <h4 class="drawer-team-name num">
                <TeamLogo :team="team.id" :name="team.name" size="xs" />{{ team.name }}
              </h4>
              <ul class="p-list">
                <li
                  v-for="p in team.players"
                  :key="p.player_id"
                  :class="['p-row', { 'is-halted': drawerHalted }]"
                >
                  <RouterLink class="p-link" :to="`/players/${p.player_id}`">
                    <span class="p-name">{{ p.display_name || p.name }}</span>
                    <span class="p-role">{{ p.role || '—' }}</span>
                    <span class="p-price num">{{ money(p.current_price) }}</span>
                    <span :class="['p-chg', 'num', trendClass(p.change_pct)]">{{
                      pct(p.change_pct)
                    }}</span>
                    <span class="p-go" aria-hidden="true">→</span>
                  </RouterLink>
                </li>
                <li v-if="!team.players.length" class="p-empty">这队暂无在册选手</li>
              </ul>
            </section>
            <p class="drawer-foot">点选手进入详情页：看价格历史、AI 建议，并下单。</p>
          </div>
        </aside>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: var(--space-5); /* P1：区块间距 16→24 */
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
.sub {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 6px;
}
.sub-meta {
  white-space: nowrap;
}
.sub-note {
  /* 允许内部折行，但整句和"，其余…"不会被拆成两个 flex 单位 */
  min-width: 0;
  /* 固定两行高度（2026-11-14）：队伍名长短不同会导致 1 行 / 2 行切换，
     下方对决卡片跟着上下跳。这里锁死 2 行并省略超出部分，切换轮次时布局不再位移。 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: calc(1.6em * 2);
}
.sub-halt {
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
  border-color: var(--accent-text);
  color: var(--accent-text);
}
.ghost:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ===== 卡片 ===== */
.card {
  padding: var(--space-5); /* P1：卡片留白 16→24 */
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
  font-size: var(--fs-cap);
}
.chip.played {
  opacity: 0.6;
}
.chip.today .chip-d {
  color: var(--warn);
}
.chip:hover {
  border-color: var(--accent-text);
}
.chip.on {
  border-color: var(--accent-text);
  background: var(--up-bg);
}
.chip.on .chip-r,
.chip.on .chip-d {
  color: var(--accent-text);
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
/* 一个圆点 + 一个词 = 一个不换行的整体，窄屏不会把"● 未开"和"始"分到两行 */
.lg {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
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
  align-items: center;
  gap: var(--space-4);
  font-size: var(--fs-h1);
  font-weight: 800;
}
/* 一队一行内横排：队标贴着队名，整块对阵只占一行高（名单下线后没必要再竖着摆） */
.match-main .side {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 220px;
}
.match-main .vs {
  color: var(--accent-text);
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

/* ===== 注脚文字（图例、列表说明共用） ===== */
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
/* 区块底色区分两个口径：未开始（暖色，往前看）/ 已结束（冷灰，历史） */
.group-row.up td {
  background: var(--warn-bg);
  color: var(--warn);
}
.group-row.down td {
  background: var(--neutral-bg);
  color: var(--muted);
}
.list-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}
/* 列表头的两个圆点跟着区块底色走：未开始=暖色，已结束=冷灰 */
.list-head .dot.upcoming {
  background: var(--warn);
}
.list-head .dot.played {
  background: var(--muted);
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
/* 参考页的镜像排布：左边“标+名”、右边“名+标”，队标永远贴在外侧。
   一队包成一个 .side，窄屏换行时只会"整队换行"，不会把队名劈成两半 */
.vs-cell .side {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
/* 比赛日后面的星期，弱化成注脚 */
td .weekday {
  margin-left: 6px;
  color: var(--muted);
  font-weight: 400;
  font-size: var(--fs-cap);
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

/* ===== 响应式（≤720px：手机）=====
   这一段的思路：桌面上是"表格"，窄屏不做"表格硬缩"，而是换成三行一卡的清单——
   第一行轮次 + 状态、第二行整条对阵、第三行日期；图例与页头按语义单位换行。 */
@media (max-width: 720px) {
  .card {
  padding: var(--space-5); /* P1：卡片留白 16→24 */
    padding: var(--space-3);
  }
  /* 页头第一句（赛季 · 赛制 · 轮数）在 320px 上放不进一行，允许它自己折行，
     否则 .sub-meta 的 nowrap 会把整块页头撑出横向溢出 */
  .sub-meta {
    white-space: normal;
  }

  /* --- 轮次条：少占宽度，滚动条交给 ‹ › 按钮 --- */
  .strip {
    gap: 5px;
    scrollbar-width: none; /* Firefox */
  }
  .strip::-webkit-scrollbar {
    display: none;
  }
  .chip {
    min-width: 46px;
    padding: 4px 6px;
  }
  .step {
    width: 26px;
  }

  /* --- 本轮对阵：一行放得下（队标降到 30px、字号降一档） --- */
  .match {
    gap: var(--space-2);
  }
  .match-main {
    font-size: var(--fs-h3);
    gap: var(--space-2);
  }
  .match-main :deep(.team-logo.md) {
    width: 30px;
    height: 30px;
    padding: 2px;
  }
  .match-meta {
    gap: 6px 10px;
    font-size: var(--fs-cap);
  }

  /* --- 图例：按语义单位换行，说明文字单独一行 --- */
  .legend {
    gap: 6px 12px;
  }
  .legend .mini {
    flex-basis: 100%;
    margin-left: 0;
  }
  .list-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  /* --- 比赛列表：表格 → 三行卡片 --- */
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
    grid-template-columns: 1fr auto;
    grid-template-areas:
      'round  status'
      'teams  teams'
      'date   date';
    gap: 6px var(--space-2);
    background: var(--surface-2);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
  }
  tr.row td {
    border: none;
    padding: 0;
    display: block;
  }
  /* 卡片里不再需要"轮次/对阵/比赛日"这类字段名前缀：位置本身就说明了一切 */
  tr.row td::before {
    content: none;
  }
  tr.row td.c-round {
    grid-area: round;
    font-weight: 700;
    font-size: var(--fs-aux);
    color: var(--muted);
  }
  tr.row td.c-status {
    grid-area: status;
    justify-self: end;
  }
  tr.row td.c-teams {
    grid-area: teams;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px 10px;
    font-size: var(--fs-body);
  }
  tr.row td.c-date {
    grid-area: date;
    display: flex;
    align-items: baseline;
    gap: 6px;
    color: var(--muted);
    font-size: var(--fs-cap);
  }
  .group-row td {
    border-radius: var(--radius-sm);
  }
}

/* ============================================================
 * 纸感覆盖（2026-11-18）：只调视觉重量，不动轮次逻辑与结构
 * ============================================================ */
.page {
  gap: var(--space-6);
}
.page-head h2 {
  font-size: var(--fs-h1);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.sub {
  color: var(--faint);
  max-width: 68ch;
}
.sub-halt {
  color: var(--halt);
  font-weight: 500;
}
.ghost {
  border: 0;
  background: none;
  padding: var(--space-2) 0;
  color: var(--muted);
}
.ghost:hover:not(:disabled) {
  color: var(--text);
}
.page-head .today {
  color: var(--faint);
}

/* 卡片：一个容器 + 大留白，不再是"卡片里套卡片" */
.card {
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  gap: var(--space-4);
}
.card-title {
  font-size: var(--fs-h3);
  font-weight: 600;
}

/* 轮次条：去掉底色，只留细边与文字 */
.chip .chip-d {
  color: var(--muted);
}
.chip.played {
  opacity: 0.78;
}
.step {
  border: 0;
  background: none;
  color: var(--faint);
  width: 24px;
}
.step:hover:not(:disabled) {
  color: var(--text);
}
.chip {
  background: transparent;
  border-color: var(--color-border);
  padding: 6px 10px;
}
.chip:hover {
  border-color: var(--color-border-strong);
}
.chip.on {
  background: var(--neutral-bg);
  border-color: var(--color-border-strong);
}
.chip.on .chip-r,
.chip.on .chip-d {
  color: var(--text);
}
.chip.today .chip-d {
  color: var(--halt);
}
.chip-d i {
  color: var(--halt);
}
.legend {
  color: var(--faint);
}
.legend .mini {
  display: none;
}
.dot.played,
.dot.upcoming {
  background: var(--faint);
}
.dot.today {
  background: var(--halt);
}

/* 对阵：字号降一档，vs 用弱化颜色 */
.match-main {
  font-size: var(--fs-h2);
  font-weight: 600;
}
.match-main .vs {
  color: var(--faint);
  font-size: var(--fs-aux);
  font-weight: 400;
}
.phase {
  padding: 0;
  border-radius: 0;
  background: none;
  font-size: var(--fs-cap);
}
.phase.played {
  color: var(--faint);
}
.phase.today {
  background: none;
  color: var(--halt);
}
.phase.upcoming {
  background: none;
  color: var(--down);
}

/* 表：行高加大、分组行不抢眼 */
th,
td {
  padding: var(--space-4) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}
th {
  padding-top: 0;
  color: var(--faint);
  font-weight: 400;
}
tr.row:hover {
  background: transparent;
}
tr.row.on {
  background: var(--neutral-bg);
}
.group-row td {
  background: transparent;
  padding-top: var(--space-5);
  color: var(--faint);
  font-weight: 400;
}
.mini {
  color: var(--faint);
}

/* 轮次条：隐藏滚动条但保留横向滚动 */
.strip {
  scrollbar-width: none;
}
.strip::-webkit-scrollbar {
  display: none;
}

/* 分组行与状态标签：去掉底色，只留文字 */
.group-row td,
.group-row.up td,
.group-row.down td {
  background: transparent;
  color: var(--faint);
  font-weight: 400;
}
.tag {
  padding: 0;
  border-radius: 0;
  background: none;
  font-size: var(--fs-cap);
}
.tag.played {
  background: none;
  color: var(--faint);
}
.tag.today {
  background: none;
  color: var(--halt);
}
.tag.upcoming {
  background: none;
  color: var(--down);
}
.row.on td,
.row.on .c-round {
  color: var(--text);
}
.row.on .star {
  color: var(--halt);
}

/* ==================== 比赛抽屉（右侧滑出） ==================== */
.drawer-scrim {
  position: fixed;
  inset: 0;
  z-index: var(--z-overlay);
  background: rgba(0, 0, 0, 0.38);
}
.match-drawer {
  position: fixed;
  top: 0;
  right: 0;
  z-index: calc(var(--z-overlay) + 1);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  width: min(420px, 100vw);
  height: 100dvh;
  padding: var(--space-5);
  overflow-y: auto;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  box-shadow: var(--shadow-overlay);
}
.drawer-enter-active,
.drawer-leave-active {
  transition: transform 260ms cubic-bezier(0.22, 1, 0.36, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  transform: translateX(100%);
}
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}
.drawer-kicker {
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-cap);
  color: var(--faint);
}
.drawer-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: var(--fs-h2);
  font-weight: 600;
  line-height: 1.3;
}
.drawer-title .vs {
  font-size: var(--fs-cap);
  color: var(--faint);
}
.drawer-close {
  flex: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: none;
  color: var(--muted);
  font-size: var(--fs-aux);
  cursor: pointer;
}
.drawer-close:hover {
  color: var(--text);
  background: var(--neutral-bg);
}
.drawer-note {
  margin: 0;
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--fs-cap);
  line-height: 1.6;
  color: var(--muted);
}
.drawer-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.drawer-team-name {
  margin: 0 0 var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  font-weight: 600;
  color: var(--text);
}
.p-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.p-row + .p-row {
  border-top: 1px solid var(--color-border);
}
.p-link {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto 14px;
  align-items: baseline;
  gap: var(--space-3);
  padding: 10px 2px;
  color: inherit;
  text-decoration: none;
}
.p-link:hover .p-name {
  text-decoration: underline;
  text-underline-offset: 3px;
}
.p-name {
  font-size: var(--fs-body);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.p-role {
  grid-column: 1;
  grid-row: 2;
  font-size: var(--fs-cap);
  color: var(--faint);
}
.p-row .p-link {
  grid-template-rows: auto auto;
  row-gap: 0;
}
.p-price,
.p-chg {
  font-size: var(--fs-aux);
  align-self: center;
}
.p-chg.up {
  color: var(--up-text);
}
.p-chg.down {
  color: var(--color-down);
}
.p-chg.flat {
  color: var(--faint);
}
.p-go {
  color: var(--faint);
  font-size: var(--fs-cap);
}
.p-row.is-halted .p-name::after {
  content: '停牌';
  margin-left: 6px;
  padding: 1px 6px;
  border: 1px solid var(--halt);
  border-radius: var(--radius-pill);
  color: var(--halt);
  font-size: var(--fs-cap);
  font-weight: 500;
  vertical-align: 1px;
}
.p-empty {
  padding: 10px 2px;
  font-size: var(--fs-cap);
  color: var(--faint);
}
.drawer-foot {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--faint);
}
.drawer-error {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  color: var(--muted);
  font-size: var(--fs-aux);
}
.drawer-error p {
  margin: 0;
}
.drawer-error button {
  padding: 6px 16px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text);
  cursor: pointer;
}
.drawer-skeleton .sk-row:last-child {
  border-bottom: 0;
}
@media (prefers-reduced-motion: reduce) {
  .drawer-enter-active,
  .drawer-leave-active {
    transition: none;
  }
}

</style>
