<script setup lang="ts">
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
import type { AnalysisResponse, PlayerDetail, PricePoint, PositionItem } from '../api/types'
import { money, pct, trendClass } from '../utils/format'
import PriceChart from '../components/PriceChart.vue'
import TradePanel from '../components/TradePanel.vue'
import StatusBadge from '../components/StatusBadge.vue'
import CollapsibleCard from '../components/CollapsibleCard.vue'
import { refreshAccount } from '../composables/useAccount'
import { checkBackendHealth } from '../composables/useBackendHealth'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const route = useRoute()
const playerId = computed(() => Number(route.params.id))

/** 路由参数非法（NaN / 非正整数）时不发请求，直接友好提示；
 *  day5 走查 P2：不再把后端 "请求参数不合法：path.player_id" 这种开发术语甩给用户 */
const invalidId = computed(() => !Number.isInteger(playerId.value) || playerId.value <= 0)

const player = ref<PlayerDetail | null>(null)
const points = ref<PricePoint[]>([])
const analysis = ref<AnalysisResponse | null>(null)
const held = ref<number | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
/** AI 是独立请求：单独维护加载态，卡片位显示"AI 分析中…"而不是空白（课件「等待可感知」） */
const analysisLoading = ref(false)

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
  try {
    const a = await api.getAnalysis(playerId.value)
    if (token === requestToken) analysis.value = a
  } catch {
    if (token === requestToken) analysis.value = null // 仅 404/500 会失败；详情已展示，静默即可
  } finally {
    // 只有"当前这次请求"才有资格关掉加载态，避免快速切换选手时旧请求把新请求的占位关掉
    if (token === requestToken) analysisLoading.value = false
  }
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
            <StatusBadge :status="player.status" />
          </p>
          <p class="rating-line">
            模拟表现分 <strong>{{ player.rating }}</strong> / 100
            <span class="sim-tag">模拟数据，非官方统计</span>
          </p>
        </div>
        <div class="price-box num">
          <div class="price">{{ money(player.current_price) }}</div>
          <div :class="['change', trendClass(player.change_pct)]">{{ pct(player.change_pct) }}</div>
        </div>
      </header>

      <p v-if="player.latest_reason" class="reason">最近变动：{{ player.latest_reason }}</p>

      <div class="cols">
        <!-- 左列：看 —— 走势 + AI 依据（折叠卡片，想细看才展开） -->
        <div class="col-main">
          <h3>价格历史</h3>
          <PriceChart :points="points" />

          <CollapsibleCard title="AI 建议" :open="true">
            <template #meta>
              <template v-if="analysis">
                <span :class="['advice', analysis.action.toLowerCase()]">{{
                  ACTION_LABEL[analysis.action] ?? analysis.action
                }}</span>
                <span :class="['risk', analysis.risk_level.toLowerCase()]"
                  >风险：{{ RISK_LABEL[analysis.risk_level] ?? analysis.risk_level }}</span
                >
              </template>
              <span v-else-if="!analysisLoading" class="src">暂不可用</span>
            </template>

            <!-- AI 请求中的占位：不空白、不跳动，告知"正在分析" -->
            <section v-if="analysisLoading" class="ai-loading" aria-busy="true" aria-live="polite">
              <span class="dots" aria-hidden="true"><i></i><i></i><i></i></span>
              <span>AI 分析中…（行情与交易不受影响）</span>
            </section>
            <section v-else-if="analysis">
              <p class="ai-src-line">
                依据来源：{{ analysis.source === 'llm' ? 'AI 模型' : '规则兜底（AI 暂不可用）' }}
              </p>
              <p class="ai-reason">{{ analysis.reason }}</p>
              <p class="disclaimer">{{ analysis.disclaimer }}</p>
            </section>
            <EmptyState v-else>AI 建议暂不可用（不影响交易）。</EmptyState>
          </CollapsibleCard>
        </div>

        <!-- 右列：做 —— 交易面板常驻可见 -->
        <aside class="col-side">
          <h3>交易</h3>
          <TradePanel
            :player="player"
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
.rating-line {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-aux);
  color: var(--muted);
}
.sim-tag {
  font-size: var(--fs-cap);
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--neutral-bg);
  margin-left: 6px;
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
.disclaimer {
  margin: var(--space-2) 0 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}

/* 交易列在长页面中保持可见 */
@media (min-width: 961px) {
  .col-side {
    position: sticky;
    top: var(--space-5);
  }
}

/* ===== 窄屏：双列转单列，标题与价格上下排 ===== */
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
</style>