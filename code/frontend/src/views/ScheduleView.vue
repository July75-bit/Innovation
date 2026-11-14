<script setup lang="ts">
/**
 * 白话导读：赛程页（/schedule）——把"这一轮谁在比赛 → 谁因此暂停交易 → 该拿几点"这套算法摆到界面上。
 *
 * 页面结构（自上而下 = 先看结论，再看证据，最后看原理）：
 *   1. 概览：28 轮 / 每轮 1 场 / 每轮暂停 4 人 / 焦点局 / 点数公式；
 *   2. 轮次选择条：点任意一轮，下面所有区块跟着重算（状态是"现算"的，不是存出来的）；
 *   3. 本轮派生结果：对阵 → 暂停名单 / 可交易名单 + 与后端同源的暂停原因；
 *   4. 点数核对表：截至本轮每队出场几次、可交易几轮、应有几点（= 2 种子点 + 可交易轮数）；
 *   5. 全赛季赛程表：每 4 轮一组，组内 8 队各出场 1 次；
 *   6. 折叠区：圆桌法怎么生成赛程（现场重算一遍与仓库赛程比对）、派生规则、结构自检 validate()。
 *
 * 算法本体在 `src/core/schedule.ts`（`core_engine/schedule.py` 的 TypeScript 移植），
 * 数据在 `src/data/demoSchedule.ts`（`scripts/build_schedule.py` 生成的镜像）——本页不复制任何规则。
 * 选手名单走 GET /api/players（契约 §4.2）；后端没起时降级为"只按队伍给结论"，赛程与算法照常可演示。
 */
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import CollapsibleCard from '../components/CollapsibleCard.vue'
import LoadingState from '../components/LoadingState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import {
  DEFAULT_BLOCK,
  SEED_POINTS,
  TRADING,
  blockCoversAllTeams,
  blockIndexOf,
  blocksOf,
  buildSchedule,
  effectiveRound,
  expectedPoints,
  injectSelfMatch,
  matchLabel,
  matchesOfTeam,
  phaseOf,
  playingTeams,
  roundMatch,
  roundOfDate,
  roundRobin,
  rounds,
  schedule,
  suspendedPlayers,
  suspensionReason,
  teamNames,
  todayIso,
  tradablePlayers,
  validate,
  weekdayCn,
  type Pair,
  type ScheduleMatch,
  type SchedulePlayer,
} from '../core/schedule'

/* ------------------------------------------------------------------ 数据装载 */

/** 今天（本地时区）与"今天该打第几轮"——决定默认选中哪一轮 */
const today = todayIso()
const totalRounds = rounds()
const todayRound = roundOfDate(today)

const selected = ref(todayRound)
const players = ref<SchedulePlayer[]>([])
const rosterLoading = ref(true)
const rosterError = ref<string | null>(null)

/** 演示名单是 8 队 × 2 人；后端没连上时用同一个口径给结论 */
const seedRosterSize = 16

async function loadRoster(): Promise<void> {
  rosterLoading.value = true
  rosterError.value = null
  try {
    players.value = await api.listPlayers()
  } catch (err) {
    // 赛程本身不依赖后端：只把"名单"这一块降级，页面其余部分照常演示算法
    rosterError.value = err instanceof ApiError ? err.message : '选手名单加载失败（后端未连接）'
    players.value = []
  } finally {
    rosterLoading.value = false
  }
}

onMounted(loadRoster)

/* -------------------------------------------------------------- 选中轮次派生 */

const names = teamNames()
const teamCount = names.size
const rules = schedule.rules ?? {}
const playersPerTeam = Number(rules.suspended_players_per_round ?? 4) / 2

const selectedMatch = computed(() => roundMatch(selected.value))
const selectedLabel = computed(() => matchLabel(selectedMatch.value))
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
/**
 * 可交易 = 赛程派生没被停 且 没有被手动冻结。
 * 少了后半句就会出现"手动停掉的选手还挂在可交易列表里"（后端 recalc 会 skip 他，界面却让人点）。
 */
const tradable = computed(() =>
  tradablePlayers(players.value, selected.value).filter(
    (player) => String(player.status ?? TRADING) === TRADING,
  ),
)

/** 名单没拿到时按规则给结论：每轮 2 队 × 每队 playersPerTeam 人 */
const suspendedCount = computed(() =>
  players.value.length ? suspended.value.length : 2 * playersPerTeam,
)
const tradableCount = computed(() =>
  players.value.length ? tradable.value.length : Math.max(seedRosterSize - 2 * playersPerTeam, 0),
)

/**
 * 在册名单与赛程的差集：演示库里只有部分选手（当前 6 队 8 人），
 * 完整种子名单才是 8 队 × 2 人。人数一律按"在册"算，并把差额讲明白，免得界面像算错了。
 */
const totalPlayers = computed(() => players.value.length)
const rosterTeams = computed(() => new Set(players.value.map((player) => player.team)))
const teamsWithoutPlayers = computed(() =>
  [...names.values()].filter((name) => !rosterTeams.value.has(name)),
)

/**
 * 暂停原因：直接问算法 `suspensionReason()`（与后端 `suspension_reason()` 同一条规则、同一句文案），
 * 名单没加载时退回"对阵 + 比赛中，暂停交易"。
 */
const selectedReason = computed(() => {
  const sample = suspended.value[0]
  const reason = sample ? suspensionReason(sample, selected.value) : null
  return reason ?? `${selectedLabel.value} 比赛中，暂停交易`
})

/** 是否被运维手动冻结（status ≠ trading）：这类选手后端结算时按"手动优先"跳过 */
function isManual(player: SchedulePlayer): boolean {
  return String(player.status ?? TRADING) !== TRADING
}

const manualHalted = computed(() => players.value.filter(isManual))

/**
 * 手动冻结中"没有被赛程停掉"的那部分才需要单独解释（"另有 N 人"）。
 * 已经在暂停名单里的人再写一句"另有"就自相矛盾了（实测踩过：sh1ro 同时出现在两处）。
 */
const manualExtra = computed(() => {
  const haltedIds = new Set(suspended.value.map((player) => player.player_id))
  return manualHalted.value.filter((player) => !haltedIds.has(player.player_id))
})

function displayName(player: SchedulePlayer): string {
  return player.display_name || player.name || `#${String(player.player_id ?? '?')}`
}

/* -------------------------------------------------- 点数核对（截至选中轮次） */

const teamStats = computed(() =>
  [...names.entries()].map(([id, name]) => {
    const played = matchesOfTeam(id, selected.value)
    return {
      id,
      name,
      played,
      tradableRounds: selected.value - played,
      points: expectedPoints(id, selected.value),
      playing: playingIds.value.includes(id),
    }
  }),
)

/* --------------------------------------------------------------- 赛程表分组 */

const blocks = computed(() => blocksOf(DEFAULT_BLOCK))
const featuredRound = schedule.featured_round ? Number(schedule.featured_round) : null
const featuredLabel = computed(() =>
  featuredRound === null ? '未设置' : matchLabel(roundMatch(featuredRound)),
)

const strip = computed(() =>
  schedule.matches.map((match) => ({
    round: match.round,
    day: match.played_at.slice(5),
    phase: phaseOf(match, today),
    featured: match.round === featuredRound,
  })),
)

function roundState(match: ScheduleMatch): string {
  return phaseText[phaseOf(match, today)] ?? '—'
}

function prevRound(): void {
  selected.value = Math.max(1, selected.value - 1)
}
function nextRound(): void {
  selected.value = Math.min(totalRounds, selected.value + 1)
}

/* ------------------------------------------- 循环轮次换算（超长回测也有对手） */

const probeRaw = ref(30)
const probeRound = computed(() => {
  const value = Math.trunc(Number(probeRaw.value) || 1)
  return Math.min(999, Math.max(1, value))
})
const probeEffective = computed(() => effectiveRound(probeRound.value))
const probeMatch = computed(() => roundMatch(probeRound.value))

/* ------------------------------------------------ 圆桌法：现场重算并比对 */

const featuredPair = computed<Pair | null>(() => {
  if (featuredRound === null) return null
  const match = roundMatch(featuredRound)
  const a = Number(match.team_a)
  const b = Number(match.team_b)
  return a <= b ? [a, b] : [b, a]
})

const sameAsRepo = (built: ScheduleMatch, index: number): boolean => {
  const repo = schedule.matches[index]
  return (
    !!repo &&
    built.round === repo.round &&
    built.played_at === repo.played_at &&
    built.team_a === repo.team_a &&
    built.team_b === repo.team_b
  )
}

const regenerated = computed(() => {
  const first = schedule.matches[0]
  const built = buildSchedule(schedule.teams, {
    start: first ? first.played_at : '2026-11-01',
    featured: featuredPair.value,
    featuredRound: featuredRound ?? 1,
    playersPerTeam,
  })
  const diff = built.matches.findIndex((match, index) => !sameAsRepo(match, index))
  return {
    built,
    same: diff === -1 && built.matches.length === totalRounds,
    diff,
    rawFirstBlock: roundRobin(schedule.teams.map((team) => Number(team.team_id)))[0] ?? [],
    featuredBlock: featuredRound === null ? 0 : blockIndexOf(featuredRound),
  }
})

/* ------------------------------------------------------ 结构自检（validate） */

/** 勾选后只在校验用的副本上注入错误，页面真正使用的 schedule 不受影响 */
const injectBroken = ref(false)
const checkedSchedule = computed(() => (injectBroken.value ? injectSelfMatch() : schedule))
const problems = computed(() => validate(checkedSchedule.value, DEFAULT_BLOCK))
const checklist = [
  `轮次连续：1 → ${totalRounds}`,
  '每轮 2 支不同队伍（不允许自己打自己）',
  `对局不重复：8 队单循环 = C(8,2) = ${totalRounds} 场`,
  `每 ${DEFAULT_BLOCK} 轮覆盖全部 8 队一次（保证每人被暂停的轮数一致，点数才能用公式算）`,
  '焦点局轮次落在赛程范围内',
]
</script>

<template>
  <div class="page">
    <!-- ============ 页头 ============ -->
    <div class="page-head">
      <div>
        <h2>赛程</h2>
        <p class="sub">
          {{ schedule.season }} · 8 队单循环 · 每轮 1 场 · 共 {{ totalRounds }} 轮 ·
          由圆桌法生成。交易状态不入库，全部由这张表<strong>现算</strong>。
        </p>
      </div>
      <div class="head-right">
        <span class="today num"
          >今天 {{ today }}<br /><strong>第 {{ todayRound }} 轮</strong></span
        >
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

    <!-- ============ 概览 ============ -->
    <div class="summary num">
      <div class="stat">
        <span>总轮数</span><strong>{{ totalRounds }}</strong>
      </div>
      <div class="stat">
        <span>本轮暂停交易</span><strong>{{ suspendedCount }} 人</strong>
      </div>
      <div class="stat">
        <span>本轮可交易</span><strong>{{ tradableCount }} 人</strong>
      </div>
      <div class="stat" :title="featuredLabel">
        <span>焦点局</span
        ><strong>{{ featuredRound === null ? '—' : `第 ${featuredRound} 轮` }}</strong>
      </div>
      <div class="stat">
        <span>每人点数公式</span><strong class="formula">{{ SEED_POINTS }} + 3k</strong>
      </div>
    </div>
    <p class="note">
      {{ rules.note }}<br />
      人数按后端<strong>在册名单</strong>统计：当前 {{ totalPlayers || '—' }} 人 /
      {{ rosterTeams.size || '—' }} 队（完整种子名单为 {{ names.size }} 队 × {{ playersPerTeam }} 人
      = {{ seedRosterSize }} 人）。
    </p>

    <!-- ============ 轮次选择 ============ -->
    <section class="card">
      <header class="card-head">
        <h3>选一轮看看</h3>
        <div class="stepper">
          <button type="button" :disabled="selected <= 1" aria-label="上一轮" @click="prevRound">
            ←
          </button>
          <span class="cur num">第 {{ selected }} 轮</span>
          <button
            type="button"
            :disabled="selected >= totalRounds"
            aria-label="下一轮"
            @click="nextRound"
          >
            →
          </button>
        </div>
      </header>
      <div class="strip" role="group" aria-label="轮次选择">
        <button
          v-for="item in strip"
          :key="item.round"
          type="button"
          :class="['chip', item.phase, { on: item.round === selected }]"
          :aria-pressed="item.round === selected"
          @click="selected = item.round"
        >
          <span class="chip-r">第 {{ item.round }} 轮</span>
          <span class="chip-d num">{{ item.day }}<i v-if="item.featured" title="焦点局">★</i></span>
        </button>
      </div>
      <p class="legend">
        <span class="tag played">已结束</span><span class="tag today">今天</span
        ><span class="tag upcoming">未开始</span
        ><span class="mini">★ 焦点局 · 点任意一轮，下面全部重算</span>
      </p>
    </section>

    <!-- ============ 本轮派生结果 ============ -->
    <section class="card">
      <header class="card-head">
        <h3>第 {{ selected }} 轮 · 派生结果</h3>
        <span :class="['phase', selectedPhase]">{{ phaseText[selectedPhase] }}</span>
      </header>

      <div class="vs num">
        <div class="side">
          <strong>{{ names.get(Number(selectedMatch.team_a)) }}</strong>
          <small>team_id {{ selectedMatch.team_a }}</small>
        </div>
        <span class="vs-mark">VS</span>
        <div class="side right">
          <strong>{{ names.get(Number(selectedMatch.team_b)) }}</strong>
          <small>team_id {{ selectedMatch.team_b }}</small>
        </div>
      </div>

      <p class="kv">
        <span>比赛日</span>
        <b>{{ selectedMatch.played_at }}（{{ weekdayCn(selectedMatch.played_at) }}）</b>
        <span>所在组</span>
        <b
          >第 {{ blockIndexOf(selected) }} 组 · 第
          {{ (blockIndexOf(selected) - 1) * DEFAULT_BLOCK + 1 }}–{{
            blockIndexOf(selected) * DEFAULT_BLOCK
          }}
          轮</b
        >
        <span>暂停队伍</span><b class="warn">{{ playingLabel }}</b> <span>暂停原因</span
        ><b class="warn">{{ selectedReason }}</b>
      </p>

      <div class="roster">
        <div class="col">
          <h4>
            <em class="num">{{ suspendedCount }}</em> 人暂停交易
            <small>本队在第 {{ selected }} 轮有比赛 → 整队停牌</small>
          </h4>
          <LoadingState v-if="rosterLoading">读取选手名单…</LoadingState>
          <template v-else-if="players.length">
            <ul class="list halt">
              <li v-for="p in suspended" :key="p.player_id">
                <RouterLink :to="`/players/${p.player_id}`">{{ displayName(p) }}</RouterLink>
                <span class="team">{{ p.team }}</span>
                <span v-if="isManual(p)" class="tag halt">手动冻结</span>
                <StatusBadge status="suspended" />
              </li>
            </ul>
            <p v-if="manualExtra.length" class="mini">
              另有 {{ manualExtra.length }} 人是<strong>手动冻结</strong>（status ≠
              trading），优先级高于赛程：{{ manualExtra.map(displayName).join('、') }}
            </p>
            <p v-else-if="manualHalted.length" class="mini">
              其中 {{ manualHalted.length }} 人同时被<strong>手动冻结</strong>（status ≠ trading），
              结算时按"手动优先"跳过：{{ manualHalted.map(displayName).join('、') }}
            </p>
          </template>
          <p v-else class="mini">
            {{ rosterError }}：按规则给结论——本轮 {{ playingLabel }} 两队整队暂停（每队
            {{ playersPerTeam }} 人，共 {{ suspendedCount }} 人）。
          </p>
        </div>

        <div class="col">
          <h4>
            <em class="num">{{ tradableCount }}</em> 人可交易
            <small>其余 {{ teamCount - 2 }} 支队伍正常定价</small>
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
          <p v-else class="mini">
            {{ rosterError }}：其余 {{ teamCount - 2 }} 支队伍共
            {{ tradableCount }} 名选手照常交易，价格照常重算。
          </p>
          <p v-if="players.length && teamsWithoutPlayers.length" class="mini">
            在册名单里没有这几支队伍的选手（不影响暂停规则，只是这一侧没人可点）：
            {{ teamsWithoutPlayers.join('、') }}
          </p>
        </div>
      </div>

      <!-- 循环轮次换算器：证明"第 29 轮 = 第 1 轮"不是口号 -->
      <div class="probe">
        <label for="probe-round">轮次换算器（试一个超出赛程的轮次，回测常跑到 30+ 轮）</label>
        <div class="probe-row">
          <input id="probe-round" v-model.number="probeRaw" type="number" min="1" max="999" />
          <p class="probe-out num">
            第 {{ probeRound }} 轮 →
            <code>({{ probeRound }} − 1) % {{ totalRounds }} + 1 = {{ probeEffective }}</code> →
            <strong>{{ matchLabel(probeMatch) }}</strong>
            <span v-if="probeRound !== probeEffective" class="mini"
              >（循环回落，不会出现"没人比赛"）</span
            >
          </p>
        </div>
      </div>
    </section>

    <!-- ============ 点数核对 ============ -->
    <section class="card">
      <header class="card-head">
        <h3>截至第 {{ selected }} 轮：每队应有几点</h3>
        <span class="hint"
          >点数 = {{ SEED_POINTS }}（种子点）+ 可交易轮数；出场即暂停，该轮不加分</span
        >
      </header>
      <table>
        <thead>
          <tr>
            <th>队伍</th>
            <th class="num">出场（暂停）次数</th>
            <th class="num">可交易轮数</th>
            <th class="num">应有点数</th>
            <th>本轮</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in teamStats" :key="row.id" :class="{ playing: row.playing }">
            <td data-label="队伍" class="team-cell">{{ row.name }}</td>
            <td data-label="出场次数" class="num">{{ row.played }}</td>
            <td data-label="可交易轮数" class="num">{{ row.tradableRounds }}</td>
            <td data-label="应有点数" class="num">
              <strong>{{ row.points }}</strong>
            </td>
            <td data-label="本轮">
              <span :class="['tag', row.playing ? 'halt' : 'ok']">{{
                row.playing ? '比赛中' : '可交易'
              }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="mini">
        验收口径：选中每组末尾（4 / 8 / 12 / … 轮）时各队出场次数完全相同，点数可口算为
        {{ SEED_POINTS }} + 3k。例如第 12 轮（k = 3）= {{ SEED_POINTS + 3 * 3 }} 点，第
        {{ totalRounds }} 轮（k = 7）= {{ SEED_POINTS + 3 * 7 }} 点。
      </p>
    </section>

    <!-- ============ 全赛季赛程 ============ -->
    <section class="card">
      <header class="card-head">
        <h3>全赛季赛程</h3>
        <span class="hint"
          >每 {{ DEFAULT_BLOCK }} 轮一组，组内 8 队各出场 1 次 · 点行切换上方结果</span
        >
      </header>
      <table>
        <thead>
          <tr>
            <th>轮次</th>
            <th>比赛日</th>
            <th>对阵</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(group, index) in blocks" :key="index">
            <tr class="group-row">
              <td colspan="4">
                第 {{ group[0]?.round }}–{{ group[group.length - 1]?.round }} 轮 ·
                {{ group.length }} 场
                <span :class="['tag', blockCoversAllTeams(group) ? 'ok' : 'bad']">
                  {{ blockCoversAllTeams(group) ? '8 队全部出场' : '覆盖不完整' }}
                </span>
              </td>
            </tr>
            <tr
              v-for="match in group"
              :key="match.round"
              :class="['row', phaseOf(match, today), { on: match.round === selected }]"
              @click="selected = match.round"
            >
              <td data-label="轮次">
                <button type="button" class="row-btn num" @click.stop="selected = match.round">
                  第 {{ match.round }} 轮<i v-if="match.round === featuredRound" title="焦点局"
                    >★</i
                  >
                </button>
              </td>
              <td data-label="比赛日" class="num">
                {{ match.played_at }} <small>{{ weekdayCn(match.played_at) }}</small>
              </td>
              <td data-label="对阵" class="vs-cell">
                <b>{{ names.get(Number(match.team_a)) }}</b>
                <span class="vs-mini">vs</span>
                <b>{{ names.get(Number(match.team_b)) }}</b>
              </td>
              <td data-label="状态">
                <span :class="['tag', phaseOf(match, today)]">{{ roundState(match) }}</span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>

    <!-- ============ 原理一：圆桌法 ============ -->
    <CollapsibleCard title="赛程怎么来的：圆桌法（可复现、不用随机数）" :open="false">
      <template #meta>同输入必得同输出</template>
      <p class="body-text">
        8 支队伍围成"圆桌"：<strong>1 号固定不动</strong>，其余 7 支每轮顺时针轮转一位，
        于是每轮正好 {{ DEFAULT_BLOCK }} 场、8 队全部出场一次；转满 {{ DEFAULT_BLOCK }} 组 =
        {{ totalRounds }} 场 = 单循环全部对局 C(8,2)，一场不多、一场不少。
      </p>
      <p class="body-text">
        现场生成的第 1 组：<span class="mono">{{
          regenerated.rawFirstBlock.map((pair) => `${pair[0]}v${pair[1]}`).join(' · ')
        }}</span>
      </p>
      <p class="body-text">
        焦点局处理：先把含
        <span class="mono">{{ featuredPair ? `${featuredPair[0]}v${featuredPair[1]}` : '—' }}</span>
        的<strong>整组</strong>挪到第
        {{ regenerated.featuredBlock }} 组，再把这场对局换到组内最后一轮 （= 第
        {{ featuredRound }} 轮）。整组挪动与组内换序都不破坏"每组覆盖全部队伍"。
      </p>
      <p :class="['verify', regenerated.same ? 'ok' : 'bad']">
        <strong>现场重算：</strong>
        <template v-if="regenerated.same"
          >浏览器里用同一套算法重算 {{ totalRounds }} 轮，与仓库赛程
          <code>data/match_schedule.json</code> 逐轮一致 ✅（轮次、日期、对阵全同）</template
        >
        <template v-else
          >第 {{ regenerated.diff + 1 }} 轮起与仓库赛程不一致 → 重跑
          <code>python scripts/build_schedule.py</code> 同步三份镜像</template
        >
      </p>
      <p class="mini">
        为什么不用随机抽签：① 可复现——同一轮永远同一场比赛，演示 / 回测 / 截图都对得上； ② 均衡——每
        4 轮各队出场一次，每人被暂停的轮数完全一致，点数能用公式直接算； ③
        可解释——真实赛程本来就是确定的。
      </p>
    </CollapsibleCard>

    <!-- ============ 原理二：状态派生 ============ -->
    <CollapsibleCard title="为什么不把状态写进数据库：派生规则" :open="false">
      <template #meta>round_match / status_for / suspension_reason</template>
      <ul class="rules">
        <li>
          <code>round_match(r) = matches[(r − 1) % {{ totalRounds }}]</code>
          —— 轮次超过赛程长度就循环，回测到 32 轮也有确定对手。
        </li>
        <li>
          <code>status_for(p, r) = p.team ∈ playing_teams(r) ? 'suspended' : 'trading'</code>
          —— 参赛两队（每队 {{ playersPerTeam }} 人）整队停牌，其余 {{ tradableCount }} 人照常定价。
        </li>
        <li>
          <code>suspension_reason(p, r)</code> 两类来源、<strong>手动 status 优先</strong>：先看
          <code>status ≠ trading</code>（运维临时冻结），再看"本队这一轮有比赛"。当前示例：{{
            selectedReason
          }}
        </li>
        <li>
          结算去重键 <code>(player_id, round)</code>：轮次由
          <code>played_at</code> 体现，同一轮重复提交只记
          <code>skipped</code>，不会多写一行价格历史。
        </li>
      </ul>
      <p class="mini">
        三份镜像同源：生成脚本 <code>scripts/build_schedule.py</code> 一次写出
        <code>data/match_schedule.json</code>（回测）、后端
        <code>app/core/demo_schedule.py</code>（<code>POST /api/prices/recalc</code> 判断停牌）、
        前端 <code>src/data/demoSchedule.ts</code>（本页）。所以界面结论与后端真实生效规则不会打架。
      </p>
    </CollapsibleCard>

    <!-- ============ 原理三：结构自检 ============ -->
    <CollapsibleCard title="赛程结构自检 validate()" :open="false">
      <template #meta>{{ problems.length ? `${problems.length} 项不通过` : '全部通过' }}</template>
      <p :class="['verify', problems.length ? 'bad' : 'ok']">
        <template v-if="!problems.length"
          >✅ 当前赛程通过全部 {{ checklist.length }} 项检查</template
        >
        <template v-else
          >❌ 检出 {{ problems.length }} 个问题：<span class="mono">{{
            problems.join('；')
          }}</span></template
        >
      </p>
      <ul class="checklist">
        <li v-for="item in checklist" :key="item">{{ item }}</li>
      </ul>
      <label class="inject">
        <input v-model="injectBroken" type="checkbox" />
        故意把第 1 轮的客队改成同一支队（自己打自己），看校验器抓不抓得到
      </label>
    </CollapsibleCard>
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
  max-width: 64ch;
}
.head-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.today {
  font-size: var(--fs-cap);
  color: var(--muted);
  text-align: right;
  line-height: 1.4;
}
.today strong {
  color: var(--text);
  font-size: var(--fs-h3);
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
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== 概览 ===== */
.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: var(--space-3);
}
.stat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat span {
  font-size: var(--fs-cap);
  color: var(--muted);
}
.stat strong {
  font-size: var(--fs-h2);
  font-variant-numeric: tabular-nums;
}
.stat strong.formula {
  font-size: var(--fs-h3);
  color: var(--accent);
}
.note {
  margin: calc(var(--space-2) * -1) 0 0;
  font-size: var(--fs-cap);
  color: var(--muted);
  line-height: 1.5;
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
.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.card-head h3 {
  margin: 0;
  font-size: var(--fs-h3);
}
.hint {
  font-size: var(--fs-cap);
  color: var(--muted);
}

/* ===== 轮次条 ===== */
.stepper {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.stepper button {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--text);
  cursor: pointer;
  line-height: 1;
}
.stepper button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.cur {
  font-size: var(--fs-aux);
  color: var(--muted);
  min-width: 7ch;
  text-align: center;
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
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--muted);
  cursor: pointer;
  font-size: var(--fs-cap);
  text-align: left;
}
.chip .chip-r {
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
}
.chip.played {
  opacity: 0.72;
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
.chip.on .chip-r {
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
  gap: var(--space-2);
  flex-wrap: wrap;
}

/* ===== 对阵 ===== */
.vs {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface-2);
}
.side {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.side.right {
  text-align: right;
}
.side strong {
  font-size: var(--fs-h2);
}
.side small {
  color: var(--muted);
  font-size: var(--fs-cap);
}
.vs-mark {
  color: var(--accent);
  font-weight: 800;
  font-size: var(--fs-h3);
  letter-spacing: 1px;
}
.kv {
  margin: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 4px var(--space-3);
  font-size: var(--fs-aux);
}
.kv span {
  color: var(--muted);
  white-space: nowrap;
}
.kv b {
  font-weight: 600;
}
.kv b.warn {
  color: var(--warn);
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
.col h4 {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-body);
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}
.col h4 em {
  font-style: normal;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}
.col h4 small {
  color: var(--muted);
  font-size: var(--fs-cap);
  font-weight: 400;
  flex-basis: 100%;
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
  padding: 3px 9px;
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
.kv .mini,
.legend .mini {
  margin: 0;
}

/* ===== 轮次换算器 ===== */
.probe {
  border-top: 1px dashed var(--border);
  padding-top: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.probe label {
  font-size: var(--fs-aux);
  color: var(--muted);
}
.probe-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.probe input {
  width: 96px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  color: var(--text);
  font: inherit;
  font-variant-numeric: tabular-nums;
}
.probe-out {
  margin: 0;
  font-size: var(--fs-aux);
}
.probe-out code {
  background: var(--neutral-bg);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
}

/* ===== 表格 ===== */
table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
th,
td {
  padding: 10px var(--space-4);
  border-bottom: 1px solid var(--border);
  text-align: left;
  font-size: var(--fs-aux);
}
tbody tr:last-child td {
  border-bottom: none;
}
th {
  color: var(--muted);
  font-weight: 600;
  background: var(--surface-2);
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
tr.row.played > td > *:not(b) {
  color: inherit;
}
.group-row td {
  background: var(--surface-2);
  font-weight: 700;
  font-size: var(--fs-cap);
  padding: 6px var(--space-4);
}
.row-btn {
  border: none;
  background: none;
  color: inherit;
  font: inherit;
  font-weight: 700;
  padding: 0;
  cursor: pointer;
}
.row-btn i {
  font-style: normal;
  color: var(--warn);
  margin-left: 3px;
}
.team-cell {
  font-weight: 700;
}
tr.playing {
  background: var(--warn-bg);
}
.vs-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
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
  font-weight: 400;
  white-space: nowrap;
}
.tag.ok {
  background: var(--down-bg);
  color: var(--down);
}
.tag.halt,
.tag.today {
  background: var(--warn-bg);
  color: var(--warn);
}
.tag.played,
.tag.upcoming {
  background: var(--neutral-bg);
  color: var(--muted);
}
.tag.bad {
  background: var(--up-bg);
  color: var(--up);
}
.phase {
  font-size: var(--fs-cap);
  padding: 2px 10px;
  border-radius: var(--radius-pill);
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

/* ===== 折叠区文字 ===== */
.body-text {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-aux);
  line-height: 1.6;
}
.mono {
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.verify {
  margin: var(--space-2) 0;
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-aux);
  line-height: 1.6;
}
.verify.ok {
  background: var(--down-bg);
  color: var(--down);
}
.verify.bad {
  background: var(--up-bg);
  color: var(--up);
}
.verify code {
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--fs-cap);
}
.rules,
.checklist {
  margin: 0 0 var(--space-2);
  padding-left: 20px;
  font-size: var(--fs-aux);
  line-height: 1.7;
}
.rules code {
  font-family: ui-monospace, Consolas, monospace;
  font-size: var(--fs-cap);
  background: var(--neutral-bg);
  padding: 1px 5px;
  border-radius: 4px;
}
.checklist {
  color: var(--muted);
}
.inject {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-aux);
  color: var(--muted);
  cursor: pointer;
}
.inject input {
  accent-color: var(--accent);
}

/* ===== 响应式：表格转卡片 ===== */
@media (max-width: 720px) {
  .card {
    padding: var(--space-3);
  }
  .vs {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .side.right {
    text-align: center;
  }
  table {
    display: block;
    background: transparent;
    border: none;
  }
  thead {
    display: none;
  }
  tbody {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  tr.row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px var(--space-3);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: var(--space-3);
  }
  tr.row td {
    border: none;
    padding: 3px 0;
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
    padding-bottom: 6px;
  }
  .group-row td {
    border-radius: var(--radius-sm);
  }
}
</style>
