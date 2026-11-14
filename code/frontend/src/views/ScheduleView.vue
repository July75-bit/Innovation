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
import TeamLogo from '../components/TeamLogo.vue'
import {
  DEFAULT_BLOCK,
  blocksOf,
  liveRound,
  phaseOf,
  playingTeams,
  roundMatch,
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

const selected = ref(todayRound)

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
watch(selected, () => void centerSelectedRound())
onMounted(() => {
  void centerSelectedRound('auto')
  window.addEventListener('resize', onViewportChange)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(resizeRaf)
  window.removeEventListener('resize', onViewportChange)
})

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
          <span class="sub-meta"
            >{{ schedule.season }} · 8 队单循环 · 共 {{ totalRounds }} 轮 · 每轮 1 场</span
          >
          <span class="sub-note"
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
          <span class="mini">点任意一行，上面就切到那一轮</span>
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
              @click="selected = match.round"
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
</style>
