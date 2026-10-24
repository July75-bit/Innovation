<script setup lang="ts">
/**
 * 交易面板：数量输入 + 买入 / 卖出。
 *
 * 契约要点：
 * - quantity 必须正整数；持仓上限 50 股（前端只做体验校验，最终以接口返回为准）；
 * - 交易是否成功以后端数据库为准：本组件只展示后端返回的 message，绝不本地伪造成功；
 * - 业务失败（余额不足/持仓不足/超上限/暂停交易）按后端提示展示即可，禁止自动重试；
 * - 提交中禁用按钮防连点；成功后由父组件刷新余额、持仓、流水、行情。
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

/** 本地体验校验（正整数、1–50）；后端仍会按契约顺序校验，以接口结果为准 */
const invalidReason = computed(() => {
  const q = quantity.value
  if (!Number.isInteger(q) || q < 1) return '数量必须是正整数'
  if (q > 50) return '单选手持仓上限 50 股'
  return null
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
    <div class="row">
      <label class="qty-label" for="trade-qty">数量</label>
      <input
        id="trade-qty"
        v-model.number="quantity"
        type="number"
        min="1"
        step="1"
        :disabled="submitting || suspended"
      />
      <span class="price-hint"
        >现价 {{ money(player.current_price) }} 币，约需
        {{
          money(player.current_price * (Number.isInteger(quantity) && quantity > 0 ? quantity : 0))
        }}
        币</span
      >
    </div>

    <p v-if="held != null" class="held-hint">当前持仓：{{ held }} 股</p>
    <p v-if="suspended" class="suspended-hint">该选手比赛进行中，暂停交易</p>
    <p v-else-if="invalidReason" class="invalid-hint">{{ invalidReason }}</p>

    <div class="actions">
      <button class="buy" :disabled="!canSubmit" @click="submit('BUY')">买入</button>
      <button class="sell" :disabled="!canSubmit" @click="submit('SELL')">卖出</button>
    </div>

    <p v-if="feedback" :class="['feedback', feedback.kind]">{{ feedback.text }}</p>
  </section>
</template>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
}
.row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.qty-label {
  font-weight: 600;
}
input {
  width: 90px;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 15px;
  background: var(--bg);
  color: var(--text);
}
.price-hint {
  color: var(--muted);
  font-size: 13px;
}
.held-hint,
.suspended-hint,
.invalid-hint {
  font-size: 13px;
  margin: 8px 0 0;
}
.held-hint {
  color: var(--muted);
}
.suspended-hint {
  color: #b26a00;
}
.invalid-hint {
  color: var(--down);
}
.actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
}
button {
  padding: 10px 26px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  color: #fff;
}
button:disabled {
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
  margin: 12px 0 0;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
}
.feedback.success {
  background: rgba(10, 143, 74, 0.1);
  color: var(--down);
}
.feedback.error {
  background: rgba(211, 47, 47, 0.1);
  color: var(--up);
}
</style>
