<script setup lang="ts">
/**
 * 白话导读：单个选手的详情页（URL 形如 /players/3），本项目功能最集中的一页。
 *
 * 进页面时并发请求 4 个接口：选手详情 + 价格历史 + 持仓列表（取该选手股数）+ AI 建议；
 * 左列是"看"（行情、走势图、AI 理由），右列是"做"（交易面板常驻）。
 *
 * 两个值得注意的写法：
 *   - silent 刷新：交易成功后重新拉数据，但不清空旧内容、不显示骨架屏，
 *     否则刚填的数量会被重置、页面还会闪一下；
 *   - requestToken（请求令牌）：连续快速切换选手时，谁最后发起谁说了算，
 *     过期响应直接丢弃，防止前一个选手的数据盖到当前页面。
 *
 * 走势图与买卖分别拆在 components/PriceChart.vue 与 TradePanel.vue，这页只负责取数与布局。
 */
/**
 * 选手详情页（路由 /players/:id）：
 * - GET /api/players/{player_id}          详情（§4.3，含 latest_reason）
 * - GET /api/players/{player_id}/prices   价格历史（§4.4，升序，直接喂折线图）
 * - GET /api/analysis/{player_id}         AI 建议（§4.10，AI 故障= 200 + rule_fallback）
 * - GET /api/positions                    取该选手持仓数用于面板提示
 * 交易成功后：刷新行情、价格历史、持仓、余额（以数据库为准，不本地改数）。
 *
 * 界面设计层：左列"看"（行情/走势/AI 依据），右列"做"（交易面板常驻可见），
 * 决策所需信息在一屏内闭环，不必来回滚动。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ApiError } from '../api/client'
import type {
  AgentDecisionResponse,
  AgentPanelResponse,
  AgentPlan,
  AgentToolsResponse,
  AnalysisResponse,
  PlayerDetail,
  PricePoint,
  PositionItem,
} from '../api/types'
import { money, pct, trendClass } from '../utils/format'
import PriceChart from '../components/PriceChart.vue'
import TradePanel from '../components/TradePanel.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { currentRound, haltReason, withRoundStatus } from '../core/tradingStatus'
import { refreshAccount } from '../composables/useAccount'
import { checkBackendHealth } from '../composables/useBackendHealth'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const route = useRoute()
const playerId = computed(() => Number(route.params.id))

/** 路由参数非法（NaN / 非正整数）时不发请求，直接友好提示；
 *  day5 走查 P2：不再把后端 "请求参数不合法：path.player_id" 这种开发术语甩给用户 */
const invalidId = computed(() => !Number.isInteger(playerId.value) || playerId.value <= 0)

const player = ref<PlayerDetail | null>(null)

/**
 * 本轮停牌是赛程派生的（后端 status 只有初始/手动值），所以详情页要显示派生后的状态，
 * 并把同一份结论交给 TradePanel——否则会出现"徽章说能买、按钮却该禁用"这种自相矛盾。
 */
const round = currentRound()
const viewPlayer = computed(() => (player.value ? withRoundStatus(player.value, round) : null))
const halt = computed(() => (player.value ? haltReason(player.value, round) : null))
const points = ref<PricePoint[]>([])
const analysis = ref<AnalysisResponse | null>(null)
const held = ref<number | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
/** AI 是独立请求：单独维护加载态，卡片位显示"AI 分析中…"而不是空白（课件「等待可感知」） */
const analysisLoading = ref(false)

/* ---- 决策卡（第 8 轮）：建议之外的"可执行计划"与"人在环"记录 ---- */
const plan = ref<AgentPlan | null>(null)
const snapshot = ref<AgentDecisionResponse['snapshot'] | null>(null)
const traceId = ref(0)
const decisionSent = ref(false)
const decisionNotice = ref('')
/** 主卡理由是否已展开（默认显示"完整句子组成的简介"，展开后显示全文） */
const reasonExpanded = ref(false)

/* ---- 第二梯度：叙事归因 / 多角色纪要 / 工具取数（都按需加载，拿不到就隐藏） ---- */
const narrative = ref<string | null>(null)
const panel = ref<AgentPanelResponse | null>(null)
const panelLoading = ref(false)
const panelError = ref('')
const tools = ref<AgentToolsResponse | null>(null)
const toolsLoading = ref(false)

/** 多角色纪要：用户点开卡片才请求（一次三调用，别让人一进页面就白烧） */
async function loadPanel() {
  if (panel.value || panelLoading.value) return
  panelLoading.value = true
  panelError.value = ''
  try {
    panel.value = await api.getAgentPanel(playerId.value)
  } catch {
    // 后端可能抛出带类名的技术信息（如 LLMOutputError），界面上只说人话
    panelError.value = '纪要暂时不可用，不影响行情与交易'
  } finally {
    panelLoading.value = false
  }
}

function onPanelToggle(open: boolean) {
  if (open) void loadPanel()
}


/** 原生 <details> 的 toggle 事件给的是 Event，这里取出 open 再转成布尔值 */
function onDetailsToggle(event: Event) {
  onPanelToggle((event.target as HTMLDetailsElement).open)
}
/** 工具调用：让用户看到"模型自己查了什么"（只有名字与参数，没有账户隐私） */
async function loadTools() {
  if (tools.value || toolsLoading.value) return
  toolsLoading.value = true
  try {
    tools.value = await api.getAgentTools(playerId.value)
  } catch {
    tools.value = null
  } finally {
    toolsLoading.value = false
  }
}

const ROLE_LABEL: Record<string, string> = {
  analyst: '📊 分析师',
  risk: '🛡 风控',
  trader: '💼 交易员',
  system: '⚙️ 系统',
}

const ACTION_LABEL: Record<string, string> = { BUY: '买入', SELL: '卖出', HOLD: '持有' }
const RISK_LABEL: Record<string, string> = { LOW: '低', MEDIUM: '中', HIGH: '高' }

/**
 * 加载选手数据。
 * silent=true 用于交易成功后的刷新：不清旧数据、不进 loading 分支，
 * 避免 TradePanel 被卸载重挂（数量输入被重置 + 页面闪烁）。
 */
/** 请求令牌：快速切换选手时，丢弃上一个选手的过期响应，防止旧数据覆盖新页面 */
let requestToken = 0

async function loadCore(silent = false) {
  const token = ++requestToken
  if (!silent) {
    loading.value = true
    error.value = null
    player.value = null
    analysis.value = null
    analysisLoading.value = false
  }
  if (invalidId.value) {
    error.value = '选手编号无效，请从市场页选择选手'
    loading.value = false
    return
  }
  checkBackendHealth()
  try {
    const id = playerId.value
    const [detail, history, positions] = await Promise.all([
      api.getPlayer(id),
      api.getPriceHistory(id),
      api.getPositions(),
    ])
    if (token !== requestToken) return // 已切走，丢弃过期响应
    player.value = detail
    points.value = history.points
    held.value = positions.find((p: PositionItem) => p.player_id === id)?.quantity ?? 0
  } catch (err) {
    if (token !== requestToken) return
    if (!silent) {
      error.value = err instanceof ApiError ? err.message : '加载选手详情失败'
    }
    // silent 刷新失败时保留旧数据即可，交易结果本身已由面板展示
  } finally {
    if (token === requestToken) loading.value = false
  }
  // AI 分析单独加载：慢/降级都不阻塞行情展示
  analysisLoading.value = true
  plan.value = null
  decisionSent.value = false
  decisionNotice.value = ''
  reasonExpanded.value = false // 换选手时收起，避免上一个选手的展开状态带过来
  try {
    const a = await api.getAnalysis(playerId.value)
    if (token === requestToken) analysis.value = a
  } catch {
    if (token === requestToken) analysis.value = null // 仅 404/500 会失败；详情已展示，静默即可
  } finally {
    // 只有"当前这次请求"才有资格关掉加载态，避免快速切换选手时旧请求把新请求的占位关掉
    if (token === requestToken) analysisLoading.value = false
  }
  // 决策卡（仓位/止损/置信度）是"增强层"：拿不到就不显示，绝不影响建议本身
  try {
    const d = await api.getAgentDecision(playerId.value)
    if (token === requestToken) {
      plan.value = d.plan
      snapshot.value = d.snapshot
      traceId.value = d.trace_id
    }
  } catch {
    if (token === requestToken) plan.value = null
  }
  // 叙事归因：把规则 reason 讲成"为什么"，同样失败即静默
  narrative.value = null
  try {
    const n = await api.getAgentNarrative(playerId.value)
    if (token === requestToken) narrative.value = n.narrative
  } catch {
    if (token === requestToken) narrative.value = null
  }
  // 切选手时清掉上一个选手的纪要与工具记录，避免张冠李戴
  panel.value = null
  tools.value = null
  panelError.value = ''
}

/** 采纳/忽略这条建议：只写"人在环"记录，不触发交易（下单仍要用户自己点买卖） */
async function recordChoice(decision: 'accept' | 'ignore') {
  if (!analysis.value || decisionSent.value) return
  decisionSent.value = true
  try {
    await api.recordAgentDecision({
      player_id: analysis.value.player_id,
      advice_action: analysis.value.action,
      advice_source: analysis.value.source,
      decision,
      trace_id: traceId.value || null,
    })
    decisionNotice.value = decision === 'accept' ? '已记录：你采纳了这条建议' : '已记录：本次不采纳'
  } catch {
    decisionNotice.value = '记录失败（不影响交易）'
  }
}
const acceptAdvice = () => recordChoice('accept')
const ignoreAdvice = () => recordChoice('ignore')

/**
 * 重新分析（用户可控）：只重发 AI 请求，不动行情、不碰账户。
 * H3「用户对结果的控制权」：没有这个入口，用户想换个建议只能刷新整页。
 */
async function refreshAnalysis() {
  if (analysisLoading.value || invalidId.value) return
  const token = requestToken // 沿用当前页面的令牌：切走选手后丢弃本次响应
  analysisLoading.value = true
  try {
    const a = await api.getAnalysis(playerId.value)
    if (token === requestToken) analysis.value = a
  } catch {
    if (token === requestToken) analysis.value = null
  } finally {
    if (token === requestToken) analysisLoading.value = false
  }
}

/** 技术信息过滤：模型/后端异常类名、堆栈不该出现在用户界面 */
function isTechLeak(text: string): boolean {
  return /(Error|Exception|Traceback|不可用（|stack)/.test(text)
}

/** 理由清洗：去掉"（规则版建议）"这类内部术语，界面上只说人话 */
function cleanReason(text: string): string {
  return text.replace(/（规则版建议）/g, "").replace(/\(规则版建议\)/g, "").trim()
}

/**
 * 主卡"简介"（2026-11-14 用户要求：**不能说话说一半**）。
 *
 * 规则：只在**句末标点**处断开，把完整句子拼到不超过 ~46 字；
 * 如果第一句本身就比这长，就原样返回那一整句（宁可多一行，也不切半句）。
 * 剩下的内容由「展开全文」按钮与下方「为什么这么建议」承载。
 */
function summaryReason(text: string): string {
  const clean = cleanReason(text)
  if (!clean) return ''
  // 按句末标点切句，保留标点（"当前价 89.13 已连续三日下跌（…），较买" 这种半句不会出现）
  const sentences = clean.match(/[^。！？；]+[。！？；]?/g) || [clean]
  let out = ''
  for (const sentence of sentences) {
    const next = `${out}${sentence}`
    if (!out) {
      out = next
      continue
    }
    if (next.length > 46) break
    out = next
  }
  return out.trim()
}

/** 是否还有没显示的内容（决定要不要出现「展开全文」） */
function hasMoreReason(text: string): boolean {
  const clean = cleanReason(text)
  return clean.length > summaryReason(text).length
}

/** 防御：模型/缓存里万一把 JSON 漏到页面上，这里取其中的 reason/summary 展示 */
function humanizeText(text: string | null | undefined): string {
  const raw = (text || '').trim()
  if (!raw) return ''
  if (!raw.startsWith('{')) return raw
  const m = raw.match(/"(?:reason|summary|text|narrative)"\s*:\s*"((?:[^"\\]|\\.)*)/)
  if (m) return (m[1] ?? '').replace(/\\"/g, '"').replace(/\\n/g, ' ').trim()
  return raw.replace(/[{}"]/g, '').replace(/\b(action|risk_level|reason|summary|text)\s*[:：]\s*/g, '')
}

/** 把握档位：把 48% 这种精确数字翻成"较高/一般/较低"（用户不需要两位小数的置信度） */
function confidenceLabel(value: number): string {
  if (value >= 0.75) return '较高'
  if (value >= 0.55) return '一般'
  return '较低'
}

/** 工具调用翻译：模型调了什么 → 一句人话（不再显示函数名与 JSON 参数） */
const TOOL_LABELS: Record<string, (args: Record<string, unknown>) => string> = {
  get_price_history: (args) => `查了最近 ${Math.min(Number(args.limit ?? 6) || 6, 12)} 个价格点`,
  get_account_snapshot: () => '看了你的余额与持仓',
  calc_position_size: () => '按风险算了一次可买股数',
}

function humanizeTool(call: { name: string; args?: Record<string, unknown> }): string {
  const render = TOOL_LABELS[call.name]
  return render ? render(call.args ?? {}) : '调用了一次只读数据工具'
}

onMounted(() => loadCore())
watch(playerId, () => loadCore())
</script>

<template>
  <div>
    <RouterLink to="/" class="back">← 返回市场</RouterLink>
    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="loadCore()" />

    <template v-else-if="player">
      <!-- 行情头部：名称/状态 + 大字价格 -->
      <header class="head card">
        <div class="head-left">
          <h2>{{ player.display_name || player.name }}</h2>
          <p class="meta">
            {{ player.team ?? '—' }} · {{ player.role ?? '—' }}
            <StatusBadge :status="viewPlayer?.status ?? player.status" />
            <span v-if="halt" class="halt-note">{{ halt }}</span>
          </p>
          <p class="rating-line">
            模拟表现分 <strong>{{ player.rating }}</strong> / 100
          </p>
        </div>
        <div class="price-box num">
          <div class="price">{{ money(player.current_price) }}</div>
          <div :class="['change', trendClass(player.change_pct)]">{{ pct(player.change_pct) }}</div>
        </div>
      </header>

      <div class="cols">
        <!-- 左列：看 —— 走势 + AI 依据（折叠卡片，想细看才展开） -->
        <div class="col-main">
          <h3>价格历史</h3>
          <PriceChart :points="points" />

          <!-- ══ 智能体结论：一眼看结论，细节按需展开 ══ -->
          <section class="ai-card" aria-label="AI 建议">
            <!-- 第一层：结论 + 风险/把握 -->
            <div class="ai-top">
              <div class="ai-verdict">
                <template v-if="analysis">
                  <span :class="['advice-pill', analysis.action.toLowerCase()]">{{
                    ACTION_LABEL[analysis.action] ?? analysis.action
                  }}</span>
                  <!-- 文字与「展开」竖排：按钮永远在正文下方左侧，不会被挤成竖排字 -->
                  <div class="ai-text">
                    <p :class="['ai-line', { 'is-expanded': reasonExpanded }]">
                      {{ reasonExpanded ? cleanReason(analysis.reason) : summaryReason(analysis.reason) }}
                    </p>
                    <button
                      v-if="hasMoreReason(analysis.reason)"
                      type="button"
                      class="ai-expand"
                      :aria-expanded="reasonExpanded"
                      @click="reasonExpanded = !reasonExpanded"
                    >
                      <span aria-hidden="true">{{ reasonExpanded ? '▴' : '▾' }}</span>
                      {{ reasonExpanded ? '收起' : '展开全文' }}
                    </button>
                  </div>
                </template>
                <template v-else-if="analysisLoading">
                  <span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>
                  <p class="ai-line muted">AI 分析中…（行情与交易不受影响）</p>
                </template>
                <p v-else class="ai-line muted">AI 建议暂不可用（不影响交易）。</p>
              </div>
              <div class="ai-side">
                <template v-if="analysis">
                  <span :class="['chip', 'risk', analysis.risk_level.toLowerCase()]"
                    >风险 {{ RISK_LABEL[analysis.risk_level] ?? analysis.risk_level }}</span
                  >
                  <span v-if="plan" class="chip">把握 {{ confidenceLabel(plan.confidence) }}</span>
                </template>
                <button
                  v-if="analysis || analysisLoading"
                  type="button"
                  class="ghost-btn"
                  :disabled="analysisLoading"
                  @click="refreshAnalysis"
                >
                  {{ analysisLoading ? '分析中…' : '重新分析' }}
                </button>
              </div>
            </div>

            <!-- 第二层：只留两个下单真正用得上的数字 -->
            <div v-if="analysis && plan" class="ai-facts">
              <span
                ><em>若采纳可买</em><b>{{ plan.suggested_quantity }}</b> 股</span
              >
              <span
                ><em>参考止损</em
                ><b>{{ plan.stop_loss_price ? money(plan.stop_loss_price) : '—' }}</b></span
              >
              <span class="ai-mode">{{
                analysis.source === 'llm' ? 'AI 生成' : '简化模式（模型未连接）'
              }}</span>
            </div>

            <!-- 第三层：三块折叠，默认全收起 -->
            <template v-if="analysis">
              <details class="ai-more">
                <summary>为什么这么建议</summary>
                <div class="ai-more-body">
                  <!-- 主卡只显示前 3 行（CSS 裁切），这里给**完整理由**，避免"截断感" -->
                  <p v-if="analysis" class="ai-full">
                    <strong>完整理由：</strong>{{ cleanReason(analysis.reason) }}
                  </p>
                  <p v-if="narrative" class="ai-quote">{{ humanizeText(narrative) }}</p>
                  <ul v-if="plan && plan.rationale.length" class="ai-why">
                    <li v-for="(line, i) in plan.rationale" :key="i">{{ line }}</li>
                  </ul>
                  <p v-if="plan" class="ai-note">{{ plan.note }}</p>
                </div>
              </details>

              <details class="ai-more" @toggle="onDetailsToggle">
                <summary>三个角色怎么看</summary>
                <div class="ai-more-body">
                  <p v-if="panelLoading" class="ai-line muted">
                    <span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>
                    三个角色正在依次思考…
                  </p>
                  <p v-else-if="panelError" class="ai-line muted">{{ panelError }}</p>
                  <template v-else-if="panel">
                    <ul class="role-list">
                      <template v-for="(m, i) in panel.minutes" :key="i">
                        <li v-if="!isTechLeak(m.content)">
                          <em>{{ ROLE_LABEL[m.role] ?? m.role }}</em>
                          <span :title="m.content">{{ m.content }}</span>
                        </li>
                      </template>
                    </ul>
                    <p
                      v-if="panel.minutes.every((m) => isTechLeak(m.content))"
                      class="ai-line muted"
                    >
                      三个角色本次未能给出纪要（不影响行情与交易）。
                    </p>
                    <p v-if="panel.minutes.some((m) => !isTechLeak(m.content))" class="role-final">
                      综合结论：<b>{{ ACTION_LABEL[panel.final.action] ?? panel.final.action }}</b>
                      · 风险 {{ RISK_LABEL[panel.final.risk_level] ?? panel.final.risk_level }}
                    </p>
                  </template>
                  <p v-else class="ai-line muted">展开后自动生成纪要（需要几秒）。</p>
                </div>
              </details>

              <details class="ai-more">
                <summary>它查了哪些数据</summary>
                <div class="ai-more-body">
                  <button
                    type="button"
                    class="ghost-btn"
                    :disabled="toolsLoading"
                    @click="loadTools"
                  >
                    {{ toolsLoading ? '取数中…' : '查看取数过程' }}
                  </button>
                  <ul v-if="tools && tools.tool_calls.length" class="tool-list">
                    <li v-for="(c, i) in tools.tool_calls" :key="i">{{ humanizeTool(c) }}</li>
                  </ul>
                  <p v-else-if="tools" class="ai-line muted">
                    {{
                      tools.source === 'llm'
                        ? '本次模型直接作答，未调用工具。'
                        : '本次使用简化模式。'
                    }}
                  </p>
                </div>
              </details>
            </template>

            <!-- 底部：免责 + 人在环（次级按钮，不抢「买入」主按钮） -->
            <footer v-if="analysis" class="ai-foot">
              <span class="ai-disclaimer">{{ analysis.disclaimer }}</span>
              <div class="ai-actions">
                <button
                  type="button"
                  class="ghost-btn"
                  :disabled="decisionSent"
                  @click="acceptAdvice"
                >
                  {{ decisionSent ? '已记录' : '采纳建议' }}
                </button>
                <button
                  type="button"
                  class="ghost-btn"
                  :disabled="decisionSent"
                  @click="ignoreAdvice"
                >
                  忽略
                </button>
                <span v-if="decisionNotice" class="ai-note">{{ decisionNotice }}</span>
              </div>
            </footer>
          </section>
        </div>

        <!-- 右列：做 —— 交易面板常驻可见 -->
        <aside class="col-side">
          <h3>交易</h3>
          <TradePanel
            v-if="viewPlayer"
            :player="viewPlayer"
            :halt-reason="halt"
            :held="held"
            @traded="
              async () => {
                await loadCore(true)
                await refreshAccount().catch(() => {}) // 余额刷新失败不影响交易结果展示
              }
            "
          />
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.back {
  color: var(--muted);
  text-decoration: none;
  font-size: var(--fs-aux);
}
.back:hover {
  color: var(--text);
}

/* 行情头部卡片 */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-top: var(--space-3);
  gap: var(--space-4);
  flex-wrap: wrap;
  padding: var(--space-4) var(--space-5);
}
.head h2 {
  margin: 0;
  font-size: var(--fs-h1);
}
.meta {
  color: var(--muted);
  margin: var(--space-1) 0 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.price-box {
  text-align: right;
}
.price {
  font-size: 30px;
  font-weight: 800;
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
.halt-note {
  margin-left: 8px;
  font-size: var(--fs-cap);
  color: var(--warn);
}

.rating-line {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-aux);
  color: var(--muted);
}
.reason {
  font-size: var(--fs-aux);
  color: var(--muted);
  margin: var(--space-3) 0 0;
}

/* 双列：左"看"右"做" */
.cols {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr);
  gap: var(--space-5);
  align-items: start;
  margin-top: var(--space-2);
}
h3 {
  margin: var(--space-5) 0 var(--space-3);
  font-size: var(--fs-h3);
}

/* AI 折叠卡片与走势图拉开间距 */
.col-main > details {
  margin-top: var(--space-4);
}

/* AI 卡片内部 */
.ai-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: var(--fs-body);
}
.ai-loading .dots {
  display: inline-flex;
  gap: 4px;
}
.ai-loading .dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--warn);
  animation: ai-blink 1.2s infinite ease-in-out;
}
.ai-loading .dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.ai-loading .dots i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes ai-blink {
  0%,
  80%,
  100% {
    opacity: 0.25;
  }
  40% {
    opacity: 1;
  }
}
.advice {
  font-weight: 800;
  font-size: var(--fs-cap);
  padding: 3px 12px;
  border-radius: var(--radius-pill);
  color: #fff;
}
.advice.buy {
  background: var(--up);
}
.advice.sell {
  background: var(--down);
}
.advice.hold {
  background: #6b7280;
}
.risk {
  font-size: var(--fs-cap);
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border);
}
.risk.low {
  color: var(--down);
}
.risk.medium {
  color: var(--warn);
}
.risk.high {
  color: var(--up);
}
.src {
  font-size: var(--fs-cap);
  color: var(--muted);
}
.ai-src-line {
  margin: 0 0 var(--space-2);
  font-size: var(--fs-cap);
  color: var(--muted);
}
.ai-reason {
  margin: 0;
  font-size: var(--fs-body);
}

/* ---- 决策卡（第一梯度） ---- */
.plan {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px dashed var(--border);
}
.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: var(--space-2);
}
.plan-grid > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg, transparent);
}
.plan-grid span {
  font-size: var(--fs-cap);
  color: var(--muted);
}
.plan-grid strong {
  font-size: var(--fs-body);
}
.plan-why {
  margin: var(--space-2) 0 0;
  padding-left: 1.1em;
  font-size: var(--fs-cap);
  color: var(--muted);
  display: grid;
  gap: 2px;
}
.plan-note {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.plan-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-2);
}
.plan-accept,
.plan-ignore,
.tools-btn {
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-cap);
  cursor: pointer;
}
.plan-accept {
  border-color: var(--accent);
  color: var(--accent);
}
.plan-accept:disabled,
.plan-ignore:disabled,
.tools-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.plan-notice {
  font-size: var(--fs-cap);
  color: var(--muted);
}

/* ---- 叙事归因（第二梯度） ---- */
.ai-narrative {
  margin: var(--space-2) 0 0;
  padding: var(--space-2) var(--space-3);
  border-left: 2px solid var(--accent);
  background: var(--surface);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.ai-narrative-tag {
  display: inline-block;
  margin-right: 6px;
  color: var(--accent);
  font-weight: 600;
}

/* ---- 多角色纪要（第二梯度） ---- */
.minutes {
  margin: var(--space-2) 0 0;
  padding-left: 1.1em;
  display: grid;
  gap: var(--space-2);
  font-size: var(--fs-cap);
}
.minutes li {
  display: grid;
  gap: 2px;
}
.minutes strong {
  color: var(--text);
}
.minutes span {
  color: var(--muted);
  line-height: 1.6;
}
.panel-final {
  margin: var(--space-3) 0 0;
  font-size: var(--fs-body);
}
.panel-note {
  display: block;
  margin-top: 4px;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.tools-box {
  margin-top: var(--space-3);
  padding-top: var(--space-2);
  border-top: 1px dashed var(--border);
}
.tools-list {
  margin: var(--space-2) 0 0;
  padding-left: 1.1em;
  font-size: var(--fs-cap);
  color: var(--muted);
  display: grid;
  gap: 2px;
}
.tools-list code {
  color: var(--accent);
}
.tools-args {
  margin-left: 6px;
  opacity: 0.85;
}
.disclaimer {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
/* 高风险时把免责声明提到理由之前，并用警示色强调（A4 风险分级） */
.disclaimer-strong {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--warn);
  border-radius: var(--radius-sm);
  background: var(--warn-bg);
  color: var(--text);
}
/* 「仅基于本站模拟数据」的边界说明（A1 边界声明） */
.ai-scope {
  opacity: 0.85;
}
/* 「重新分析」按钮：轻量次级按钮，不抢交易面板主操作（H3 用户可控） */
.ai-refresh {
  margin-left: auto;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-cap);
  cursor: pointer;
}
.ai-refresh:hover:not(:disabled) {
  color: var(--text);
  border-color: var(--muted);
}
.ai-refresh:disabled {
  cursor: default;
  opacity: 0.7;
}

/* 交易列在长页面中保持可见 */
@media (min-width: 961px) {
  .col-side {
    position: sticky;
    top: var(--space-5);
  }
}

/* ===== 窄屏：双列转单列，标题与价格上下排 ===== */
/* 窄屏：AI 卡头部（建议/风险/重新分析）允许换行，避免挤成一行溢出 */
@media (max-width: 720px) {
  :deep(.meta) {
    flex-wrap: wrap;
    row-gap: 6px;
  }
}
@media (max-width: 960px) {
  .cols {
    grid-template-columns: minmax(0, 1fr);
    gap: 0;
  }
  .head {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
    padding: var(--space-4);
  }
  .head h2 {
    font-size: 22px;
  }
  .price {
    font-size: 28px;
  }
  .price-box {
    text-align: left;
  }
}

/* ══════════ 智能体结论卡（改版：结论优先，细节折叠） ══════════ */
.ai-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.ai-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}
.ai-verdict {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  min-width: 0;
}
/* 正文 + 「展开全文」：竖向排列，按钮在正文左下角（不再被 flex 挤成竖排字） */
.ai-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  min-width: 0;
  flex: 1 1 auto;
}
.advice-pill {
  flex: none;
  padding: 2px 12px;
  border-radius: var(--radius-pill);
  font-weight: 800;
  font-size: var(--fs-body);
  line-height: 22px;
}
.advice-pill.buy {
  background: var(--up-bg);
  color: var(--up);
}
.advice-pill.sell {
  background: var(--down-bg);
  color: var(--down);
}
.advice-pill.hold {
  background: var(--neutral-bg);
  color: var(--text);
}
.ai-line {
  margin: 0;
  font-size: var(--fs-body);
  line-height: 1.65;
  color: var(--text);
  /* 简介默认最多 2 行；点「展开全文」后取消限制（.is-expanded） */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.ai-line.is-expanded {
  display: block;
  -webkit-line-clamp: unset;
  line-clamp: unset;
  overflow: visible;
}
/*
 * 「展开全文 / 收起」：安静的胶囊按钮（不是强调色大字，也不抢"卖出/持有"的视觉）。
 * 关键：white-space: nowrap —— 上一版就是被 flex 挤到只剩一个字宽，变成竖排"展开全文"。
 */
.ai-expand {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex: none;
  margin: 0;
  padding: 2px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-cap);
  line-height: 18px;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.ai-expand:hover {
  color: var(--accent);
  border-color: var(--accent);
}
.ai-expand:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.ai-line.muted {
  color: var(--muted);
  font-size: var(--fs-aux);
}
.ai-side {
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.chip {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-cap);
  background: var(--neutral-bg);
  color: var(--muted);
  white-space: nowrap;
}
.chip.risk.low {
  color: var(--down);
  background: var(--down-bg);
}
.chip.risk.medium {
  color: var(--warn);
  background: var(--warn-bg);
}
.chip.risk.high {
  color: var(--up);
  background: var(--up-bg);
}
.ai-facts {
  display: flex;
  align-items: baseline;
  gap: var(--space-5);
  padding: var(--space-2) 0;
  border-top: 1px dashed var(--border);
  border-bottom: 1px dashed var(--border);
  font-size: var(--fs-aux);
  color: var(--muted);
}
.ai-facts b {
  color: var(--text);
  font-size: var(--fs-h3);
  font-variant-numeric: tabular-nums;
}
.ai-facts em {
  font-style: normal;
  margin-right: 6px;
}
.ai-mode {
  margin-left: auto;
  font-size: var(--fs-cap);
  opacity: 0.85;
}
.ai-more {
  border-top: 1px solid var(--border);
}
.ai-more:first-of-type {
  border-top: 0;
}
.ai-more > summary {
  cursor: pointer;
  list-style: none;
  padding: 7px 0;
  font-size: var(--fs-aux);
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 6px;
}
.ai-more > summary::-webkit-details-marker {
  display: none;
}
.ai-more > summary::before {
  content: '▸';
  transition: transform 0.15s;
}
.ai-more[open] > summary::before {
  transform: rotate(90deg);
}
.ai-more > summary:hover {
  color: var(--text);
}
.ai-more-body {
  padding: 0 0 var(--space-3) 18px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.ai-quote {
  margin: 0;
  padding: var(--space-2) var(--space-3);
  border-left: 2px solid var(--border);
  color: var(--muted);
  font-size: var(--fs-aux);
  line-height: 1.7;
}
/* 折叠区里的「完整理由」：不裁切，主卡 3 行之外的文字在这里能看全 */
.ai-full {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--text);
  line-height: 1.7;
}
.ai-full strong {
  color: var(--muted);
  font-weight: 600;
}
.ai-why {
  margin: 0;
  padding-left: 18px;
  font-size: var(--fs-aux);
  color: var(--text);
  line-height: 1.7;
}
.ai-note {
  margin: 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.role-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.role-list li {
  display: flex;
  gap: var(--space-2);
  font-size: var(--fs-aux);
  line-height: 1.6;
}
.role-list em {
  flex: none;
  font-style: normal;
  color: var(--muted);
  min-width: 42px;
}
.role-list span {
  color: var(--text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.role-final {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--muted);
}
.role-final b {
  color: var(--text);
}
.tool-list {
  margin: 0;
  padding-left: 18px;
  font-size: var(--fs-aux);
  color: var(--text);
  line-height: 1.8;
}
.ai-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  border-top: 1px solid var(--border);
  padding-top: var(--space-2);
}
.ai-disclaimer {
  font-size: var(--fs-cap);
  color: var(--muted);
}
.ai-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.ghost-btn {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-cap);
  cursor: pointer;
}
.ghost-btn:hover:not(:disabled) {
  color: var(--text);
  border-color: var(--muted);
}
.ghost-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

/* 窄屏：AI 卡片从「左右两栏」改为「上下堆叠」，避免理由被挤成窄条 */
@media (max-width: 720px) {
  .ai-top {
    flex-direction: column;
    gap: var(--space-2);
  }
  .ai-verdict {
    flex-wrap: wrap;
  }
  .ai-side {
    width: 100%;
    flex-wrap: wrap;
  }
  .ai-facts {
    flex-wrap: wrap;
    gap: var(--space-2) var(--space-4);
  }
  .ai-mode {
    margin-left: 0;
  }
  .ai-foot {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
  .ai-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
}
</style>
