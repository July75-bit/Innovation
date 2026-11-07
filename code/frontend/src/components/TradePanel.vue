<script setup lang="ts">
/**
 * 交易面板（用户体验层）：
 * - 任务流最短：数量快捷档 + 实时"约需金额"预估，改一下数量立刻看到成本；
 * - 状态可见：提交中禁用并显示"提交中…"，成功后绿色横幅、失败红色横幅（含后端原文）；
 * - 容错：本地只做体验校验（正整数/上限），失败不清空输入，可直接改数量重试；
 * - 信任：余额/持仓实时回显，暂停交易给出明确拦截原因。
 *
 * 契约要点：
 * - quantity 必须正整数；持仓上限 50 股（前端只做体验校验，最终以接口返回为准）；
 * - 交易是否成功以后端数据库为准：本组件只展示后端返回的 message，绝不本地伪造成功；
 * - 业务失败（余额不足/持仓不足/超上限/暂停交易）按后端提示展示即可，禁止自动重试。
 */
import { computed, ref } from 'vue'
import { api } from '../api'
import { ApiError } from '../api/client'
import type { PlayerSummary, TradeResponse } from '../api/types'
import { money } from '../utils/format'

const props = defineProps<{
  player: PlayerSummary
  /** 当前持仓（无持仓为 0；未知传 null，不展示提示） */
  held?: number | null
}>()

const emit = defineEmits<{
  traded: [payload: TradeResponse]
}>()

const quantity = ref(1)
const submitting = ref(false)
const feedback = ref<{ kind: 'success' | 'error'; text: string } | null>(null)

const suspended = computed(() => props.player.status !== 'trading')

/** 数量快捷档：减少"输入"这一步，点一下即完成（任务流最短化） */
const quickQty = [1, 5, 10, 25]

/** 本地体验校验（正整数、1–50）；后端仍会按契约顺序校验，以接口结果为准 */
const invalidReason = computed(() => {
  const q = quantity.value
  if (!Number.isInteger(q) || q < 1) return '数量必须是正整数'
  if (q > 50) return '单选手持仓上限 50 股'
  return null
})

const estimated = computed(() => {
  const q = Number.isInteger(quantity.value) && quantity.value > 0 ? quantity.value : 0
  return props.player.current_price * q
})

const canSubmit = computed(() => !submitting.value && !suspended.value && !invalidReason.value)

async function submit(side: 'BUY' | 'SELL') {
  if (!canSubmit.value) return
  submitting.value = true
  feedback.value = null
  try {
    const res =
      side === 'BUY'
        ? await api.buy(props.player.player_id, quantity.value)
        : await api.sell(props.player.player_id, quantity.value)
    feedback.value = { kind: 'success', text: res.message }
    emit('traded', res)
  } catch (err) {
    // 直接展示后端中文 message（契约 §2），不写映射表、不重试
    feedback.value = {
      kind: 'error',
      text: err instanceof ApiError ? err.message : '交易失败，请稍后再试',
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="panel">
    <div class="cost-line num">
      <span class="cost-label">现价</span>
      <strong>{{ money(player.current_price) }}</strong>
      <span class="cost-aux">币/股</span>
    </div>

    <label class="qty-label" for="trade-qty">数量</label>
    <div class="row">
      <input
        id="trade-qty"
        v-model.number="quantity"
        type="number"
        min="1"
        step="1"
        :disabled="submitting || suspended"
        :aria-invalid="invalidReason ? 'true' : 'false'"
      />
      <div class="chips" role="group" aria-label="快捷数量">
        <button
          v-for="q in quickQty"
          :key="q"
          type="button"
          :class="['chip', { active: quantity === q }]"
          :disabled="submitting || suspended"
          @click="quantity = q"
        >
          {{ q }}
        </button>
      </div>
    </div>

    <p class="estimate num">
      约需 <strong>{{ money(estimated) }}</strong> 币
      <span class="hint">（以成交价实时计算）</span>
    </p>

    <p v-if="held != null" class="held-hint">当前持仓：{{ held }} 股 / 上限 50 股</p>

    <!-- 拦截态：暂停交易时明确说明原因，而不是只禁用按钮 -->
    <p v-if="suspended" class="suspended-hint" role="status">
      ⚠ 该选手比赛进行中，暂停交易（恢复后可正常下单）
    </p>
    <p v-else-if="invalidReason" class="invalid-hint" role="alert">{{ invalidReason }}</p>

    <div class="actions">
      <button class="buy" :disabled="!canSubmit" @click="submit('BUY')">
        {{ submitting ? '提交中…' : '买入' }}
      </button>
      <button class="sell" :disabled="!canSubmit" @click="submit('SELL')">
        {{ submitting ? '提交中…' : '卖出' }}
      </button>
    </div>

    <!-- 结果反馈：成功/失败都即时可见（aria-live 供读屏播报） -->
    <div v-if="feedback" :class="['feedback', feedback.kind]" role="status" aria-live="polite">
      <span class="fb-ico" aria-hidden="true">{{ feedback.kind === 'success' ? '✓' : '✕' }}</span>
      {{ feedback.text }}
    </div>

    <p class="virtual-note">虚拟币交易，不涉及真实资金；成交结果以后端账户数据为准。</p>
  </section>
</template>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.cost-line {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: var(--fs-aux);
  color: var(--muted);
}
.cost-line strong {
  color: var(--text);
  font-size: var(--fs-h2);
  font-variant-numeric: tabular-nums;
}
.qty-label {
  font-weight: 600;
  font-size: var(--fs-body);
}
.row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
input {
  width: 88px;
  padding: var(--space-2) 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px;
  background: var(--bg);
  color: var(--text);
}
input[aria-invalid='true'] {
  border-color: var(--warn);
}
.chips {
  display: inline-flex;
  gap: 6px;
}
.chip {
  min-width: 36px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-aux);
  font-variant-numeric: tabular-nums;
  cursor: pointer;
}
.chip:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}
.chip.active {
  background: var(--up-bg);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 700;
}
.chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.estimate {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--muted);
}
.estimate strong {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}
.hint {
  font-size: var(--fs-cap);
}
.held-hint {
  font-size: var(--fs-aux);
  margin: 0;
  color: var(--muted);
}
.suspended-hint {
  font-size: var(--fs-aux);
  margin: 0;
  color: var(--warn);
  background: var(--warn-bg);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}
.invalid-hint {
  font-size: var(--fs-aux);
  margin: 0;
  color: var(--warn);
}
.actions {
  display: flex;
  gap: var(--space-3);
}
button.buy,
button.sell {
  flex: 1;
  padding: 10px 0;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  color: #fff;
}
button.buy:disabled,
button.sell:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.buy {
  background: var(--up);
}
.sell {
  background: var(--down);
}
.feedback {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--fs-body);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.fb-ico {
  font-weight: 800;
}
.feedback.success {
  background: var(--down-bg);
  color: var(--down);
}
.feedback.error {
  background: var(--up-bg);
  color: var(--up);
}
.virtual-note {
  margin: 0;
  font-size: var(--fs-cap);
  color: var(--muted);
  border-top: 1px dashed var(--border);
  padding-top: var(--space-2);
}

/* ===== 窄屏：买卖按钮改为整行，避免误触与换行错位 ===== */
@media (max-width: 720px) {
  .actions {
    flex-direction: column;
  }
  input {
    width: 100%;
    max-width: 160px;
  }
}
</style>