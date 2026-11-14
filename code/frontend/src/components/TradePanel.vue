<script setup lang="ts">
/**
 * 白话导读：买入/卖出小表单，详情页右侧那块面板就是它（1/5/10/25 + 最大 + 清仓 快捷数量（最大 = 余额与剩余仓位取小） + 实时约需金额）。
 *
 * 组件之间怎么沟通（Vue 核心两句话）：
 *   - props：父页面传下来的只读数据（这里传 player 现价信息、held 当前持仓）；
 *   - emit("traded", res)：子组件不改父组件，只喊一声"成交了"，父页面收到后去刷新行情和余额。
 *
 * 本地校验（正整数、不超过 50 股）只为少点一次失败按钮，最终结果永远以接口返回为准；
 * 失败时直接显示后端中文 message，而且绝不自动重试——重试就变成第二笔真实交易了。
 */
/**
 * 交易面板（用户体验层）：
 * - 任务流最短：数量快捷档（1/5/10/25 + 最大可买 + 清仓全卖）+ 实时"约需金额"预估，改一下数量立刻看到成本；
 *   其中「最大」= min(余额÷现价, 50 − 已持有)，一点就超仓的情况根本不会出现；
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
import { useAccount } from '../composables/useAccount'

const props = defineProps<{
  player: PlayerSummary
  /** 当前持仓（无持仓为 0；未知传 null，不展示提示） */
  held?: number | null
  /** 停牌原因（赛程派生或手动冻结），由父页按本轮赛程算好传进来 */
  haltReason?: string | null
}>()

const emit = defineEmits<{
  traded: [payload: TradeResponse]
}>()

const quantity = ref(1)
const submitting = ref(false)
const feedback = ref<{ kind: 'success' | 'error'; text: string } | null>(null)

/** 余额读 useAccount 的共享状态（App.vue 首屏拉、每次交易后各页刷新），这里不额外发请求 */
const { account } = useAccount()

const suspended = computed(() => props.player.status !== 'trading')

/** 提示优先用父页给的原因（如"Vitality vs Spirit 比赛中，暂停交易"），没传再退回通用说法 */
const haltHint = computed(() => props.haltReason ?? '该选手比赛进行中，暂停交易')

/** 单选手持仓上限（契约 §4.7：前端只做体验校验，最终以接口返回为准） */
const MAX_HOLD = 50

/** 数量快捷档：1/5/10/25 是固定档；「最大」不是固定数，每次实时算（见 maxQty） */
const quickQty = [1, 5, 10, 25]

/** 已持有股数：未知（null/undefined）按 0 算，不让"不知道"把上限压得更小 */
const heldNow = computed(() => props.held ?? 0)

/**
 * 「最大」档 = min( 剩余信用点 ÷ 现价 向下取整 , 50 股仓位上限 − 已持有 )。
 * 两个数取小的那个：既不会花超余额，也不会一点下去就把仓位顶过 50 股。
 * 余额还没拉到时不瞎猜数字：返回 0 并让这颗键不可点，原因写在 maxBlockReason。
 */
const maxQty = computed(() => {
  const price = props.player.current_price
  if (!Number.isFinite(price) || price <= 0) return 0
  if (account.value === null) return 0
  const byBalance = Math.floor(account.value.balance / price)
  return Math.max(0, Math.min(byBalance, MAX_HOLD - heldNow.value))
})

/** 「最大」暂时不能点的原因；null = 可以点 */
const maxBlockReason = computed(() => {
  if (account.value === null) return '余额还没拉到，暂时算不出最大可买数量'
  if (heldNow.value >= MAX_HOLD)
    return '已持有 ' + heldNow.value + ' 股，到 ' + MAX_HOLD + ' 股上限了'
  if (maxQty.value < 1)
    return (
      '余额 ' +
      money(account.value.balance) +
      ' 不够按现价 ' +
      money(props.player.current_price) +
      ' 买 1 股'
    )
  return null
})

/**
 * 清仓档 = 当前持仓股数，一键把这只选手卖空。
 * 持仓还没拉到（null）或本来就是 0 股时不给点，原因写在 sellAllBlockReason。
 */
const sellAllBlockReason = computed(() => {
  if (props.held == null) return '持仓数还没拉到，算不出可卖数量'
  if (props.held < 1) return '当前没有持仓，卖不出'
  return null
})

const sellAllNote = computed(
  () => sellAllBlockReason.value ?? '清仓 = 一次卖出全部 ' + props.held + ' 股',
)

/** 悬停 title 和面板上的说明行共用这一句，避免两处各说一套 */
const maxNote = computed(() => {
  const blocked = maxBlockReason.value
  if (blocked !== null) return blocked
  const heldPart = heldNow.value > 0 ? ' / 已持有 ' + heldNow.value + ' 股' : ''
  const base =
    '最大可买 ' +
    maxQty.value +
    ' 股（余额 ' +
    money(account.value?.balance ?? 0) +
    ' / 现价 ' +
    money(props.player.current_price) +
    heldPart +
    '）'
  return base
})

/** 点「最大」：把可买上限填进数量框，约需金额随之实时刷新 */
function applyMax(): void {
  if (maxBlockReason.value !== null) return
  quantity.value = maxQty.value
}

/** 点「清仓」：把数量填成当前持仓，配合右边的"卖出"按钮一次卖空 */
function applySellAll(): void {
  if (sellAllBlockReason.value !== null) return
  quantity.value = props.held ?? 0
}

/** 本地体验校验（正整数、1–50）；后端仍会按契约顺序校验，以接口结果为准 */
const invalidReason = computed(() => {
  const q = quantity.value
  if (!Number.isInteger(q) || q < 1) return '数量必须是正整数'
  if (q > MAX_HOLD) return '单选手持仓上限 ' + MAX_HOLD + ' 股'
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
        :title="suspended ? haltHint : '按 Enter 直接买入'"
        @keyup.enter="submit('BUY')"
      />
      <span class="qty-unit" aria-hidden="true">股</span>
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
        <!-- 第 5 档「最大」：算不出原因时禁用并说明，而不是点了没反应 -->
        <button
          type="button"
          :class="['chip', 'chip-max', { active: maxQty > 0 && quantity === maxQty }]"
          :disabled="submitting || suspended || maxBlockReason !== null"
          :title="maxNote"
          @click="applyMax"
        >
          最大
        </button>
        <!-- 第 6 档「清仓」：一次卖掉当前全部持仓；没有持仓或还没拉到就不给点 -->
        <button
          type="button"
          :class="['chip', 'chip-sell', { active: held != null && held > 0 && quantity === held }]"
          :disabled="submitting || suspended || sellAllBlockReason !== null"
          :title="sellAllNote"
          @click="applySellAll"
        >
          清仓
        </button>
      </div>
    </div>

    <p class="estimate num">
      约需 <strong>{{ money(estimated) }}</strong> 币
      <span class="hint">（以成交价实时计算）</span>
    </p>

    <p v-if="held != null" class="held-hint">当前持仓：{{ held }} 股 / 上限 50 股</p>

    <!-- 把「最大 / 清仓」的算法结果直接写出来：窄屏没有鼠标悬停，也得看得懂这两颗键怎么算的 -->
    <p :class="['max-hint', { blocked: maxBlockReason !== null }]" role="status">
      {{ maxNote }}
    </p>
    <p :class="['sell-hint', { blocked: sellAllBlockReason !== null }]" role="status">
      {{ sellAllNote }}
    </p>

    <!-- 拦截态：暂停交易时明确说明原因，而不是只禁用按钮 -->
    <p v-if="suspended" class="suspended-hint" role="status">
      ⚠ {{ haltHint }}（恢复后可正常下单）
    </p>
    <p v-else-if="invalidReason" class="invalid-hint" role="alert">{{ invalidReason }}</p>

    <div class="actions">
      <button class="buy" :disabled="!canSubmit" @click="submit('BUY')">
        {{ suspended ? '暂停交易中' : submitting ? '提交中…' : '买入' }}
      </button>
      <button class="sell" :disabled="!canSubmit" @click="submit('SELL')">
        {{ suspended ? '暂停交易中' : submitting ? '提交中…' : '卖出' }}
      </button>
    </div>
    <p v-if="!suspended" class="kbd-hint">提示：在数量框按 <kbd>Enter</kbd> 直接买入</p>

    <!-- 结果反馈：成功/失败都即时可见（aria-live 供读屏播报） -->
    <div v-if="feedback" :class="['feedback', feedback.kind]" role="status" aria-live="polite">
      <span class="fb-ico" aria-hidden="true">{{ feedback.kind === 'success' ? '✓' : '✕' }}</span>
      {{ feedback.text }}
    </div>

    <p class="virtual-note">信用点交易，不涉及真实资金；成交结果以后端账户数据为准。</p>
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
  flex-wrap: wrap;
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
/* 「最大 / 清仓」都是两字中文，比数字档宽一点，避免窄屏挤成换行 */
.chip-max,
.chip-sell {
  min-width: 48px;
}
.max-hint,
.sell-hint {
  margin: 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.max-hint.blocked,
.sell-hint.blocked {
  color: var(--warn);
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

/* 数量单位后缀（「股」）：让输入框含义自解释，无需猜测单位 */
.qty-unit {
  font-size: var(--fs-aux);
  color: var(--muted);
}

/* 键盘提示：告诉用户 Enter 可以直接买入（H7 高效） */
.kbd-hint {
  margin: 0;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.kbd-hint kbd {
  padding: 1px 5px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface-2);
  font-family: inherit;
  font-size: var(--fs-cap);
}
</style>
