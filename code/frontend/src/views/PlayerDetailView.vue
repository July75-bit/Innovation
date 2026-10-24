<script setup lang="ts">
/**
 * 选手详情页（路由 /players/:id）：
 * - GET /api/players/{player_id}          详情（§4.3，含 latest_reason）
 * - GET /api/players/{player_id}/prices   价格历史（§4.4，升序，直接喂折线图）
 * - GET /api/analysis/{player_id}         AI 建议（§4.10，AI 故障= 200 + rule_fallback）
 * - GET /api/positions                    取该选手持仓数用于面板提示
 * 交易成功后：刷新行情、价格历史、持仓、余额（以数据库为准，不本地改数）。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { AnalysisResponse, PlayerDetail, PricePoint, PositionItem } from '../api/types'
import { money, pct, trendClass } from '../utils/format'
import PriceChart from '../components/PriceChart.vue'
import TradePanel from '../components/TradePanel.vue'
import { refreshAccount } from '../composables/useAccount'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LoadingState from '../components/LoadingState.vue'

const route = useRoute()
const playerId = computed(() => Number(route.params.id))

const player = ref<PlayerDetail | null>(null)
const points = ref<PricePoint[]>([])
const analysis = ref<AnalysisResponse | null>(null)
const held = ref<number | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const ACTION_LABEL: Record<string, string> = { BUY: '买入', SELL: '卖出', HOLD: '持有' }
const RISK_LABEL: Record<string, string> = { LOW: '低', MEDIUM: '中', HIGH: '高' }

/**
 * 加载选手数据。
 * silent=true 用于交易成功后的刷新：不清旧数据、不进 loading 分支，
 * 避免 TradePanel 被卸载重挂（数量输入被重置 + 页面闪烁）。
 */
async function loadCore(silent = false) {
  if (!silent) {
    loading.value = true
    error.value = null
    player.value = null
    analysis.value = null
  }
  try {
    const id = playerId.value
    const [detail, history, positions] = await Promise.all([
      api.getPlayer(id),
      api.getPriceHistory(id),
      api.getPositions(),
    ])
    player.value = detail
    points.value = history.points
    held.value = positions.find((p: PositionItem) => p.player_id === id)?.quantity ?? 0
  } catch (err) {
    if (!silent) {
      error.value = err instanceof ApiError ? err.message : '加载选手详情失败'
    }
    // silent 刷新失败时保留旧数据即可，交易结果本身已由面板展示
  } finally {
    loading.value = false
  }
  // AI 分析单独加载：慢/降级都不阻塞行情展示
  try {
    analysis.value = await api.getAnalysis(playerId.value)
  } catch {
    analysis.value = null // 仅 404/500 会失败；详情已展示，静默即可
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
      <header class="head">
        <div>
          <h2>{{ player.display_name || player.name }}</h2>
          <p class="meta">
            {{ player.team ?? '—' }} · {{ player.role ?? '—' }}
            <span :class="['status', player.status === 'trading' ? 'ok' : 'halt']">
              {{ player.status === 'trading' ? '交易中' : '暂停交易' }}
            </span>
          </p>
        </div>
        <div class="price-box">
          <div class="price">{{ money(player.current_price) }}</div>
          <div :class="['change', trendClass(player.change_pct)]">
            {{ pct(player.change_pct) }}（前价 {{ money(player.prev_price) }}）
          </div>
        </div>
      </header>

      <p class="rating-line">
        模拟表现分 <strong>{{ player.rating }}</strong> / 100
        <span class="sim-tag">模拟数据，非官方统计</span>
      </p>
      <p v-if="player.latest_reason" class="reason">最近变动：{{ player.latest_reason }}</p>

      <h3>价格历史</h3>
      <PriceChart :points="points" />

      <h3>AI 建议</h3>
      <section v-if="analysis" class="ai-card">
        <div class="ai-head">
          <span :class="['advice', analysis.action.toLowerCase()]">{{
            ACTION_LABEL[analysis.action] ?? analysis.action
          }}</span>
          <span :class="['risk', analysis.risk_level.toLowerCase()]"
            >风险：{{ RISK_LABEL[analysis.risk_level] ?? analysis.risk_level }}</span
          >
          <span class="src">{{
            analysis.source === 'llm' ? 'AI 模型' : '规则兜底（AI 暂不可用）'
          }}</span>
        </div>
        <p class="ai-reason">{{ analysis.reason }}</p>
        <p class="disclaimer">{{ analysis.disclaimer }}</p>
      </section>
      <EmptyState v-else>AI 建议暂不可用（不影响交易）。</EmptyState>

      <h3>交易</h3>
      <TradePanel
        :player="player"
        :held="held"
        @traded="
          async () => {
            await loadCore(true)
            await refreshAccount()
          }
        "
      />
    </template>
  </div>
</template>

<style scoped>
.back {
  color: var(--muted);
  text-decoration: none;
  font-size: 14px;
}
.back:hover {
  color: var(--text);
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-top: 12px;
  gap: 16px;
  flex-wrap: wrap;
}
.head h2 {
  margin: 0;
  font-size: 26px;
}
.meta {
  color: var(--muted);
  margin: 4px 0 0;
  display: flex;
  align-items: center;
  gap: 8px;
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
.price-box {
  text-align: right;
}
.price {
  font-size: 30px;
  font-weight: 800;
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
.rating-line {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--muted);
}
.sim-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(127, 127, 127, 0.16);
  margin-left: 6px;
}
.reason {
  font-size: 13px;
  color: var(--muted);
  margin: 6px 0 0;
}
h3 {
  margin: 22px 0 10px;
  font-size: 16px;
}
.ai-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}
.ai-head {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.advice {
  font-weight: 800;
  padding: 4px 14px;
  border-radius: 8px;
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
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
}
.risk.low {
  color: var(--down);
}
.risk.medium {
  color: #b26a00;
}
.risk.high {
  color: var(--up);
}
.src {
  font-size: 12px;
  color: var(--muted);
}
.ai-reason {
  margin: 10px 0 0;
  font-size: 14px;
}
.disclaimer {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--muted);
}
</style>
