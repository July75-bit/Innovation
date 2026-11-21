/**
 * 白话导读：「最大」和「清仓」两颗快捷键的回归测试，钉住口径：
 *   1) 最大 = min( floor(剩余信用点 ÷ 现价) , 50 − 已持有 )：既不会花超余额，也不会一点就超仓位；
 *      满 50 股时这颗键直接禁用并说明原因（而不是填个 0 或让人点了没反应）；
 *   2) 清仓 = 当前持仓股数，只看持仓、不看余额，所以余额没拉到时它照样能用。
 * vi.mock 把 src/api 换成可控假货：余额想设多少设多少，不会真下单、也不需要后端在跑。
 * 注意 useAccount 的状态是模块级的（整个文件共享一份），所以"余额还没拉到"必须排在第一个用例。
 */
import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import TradePanel from '../TradePanel.vue'
import { refreshAccount } from '../../composables/useAccount'
import type { PlayerSummary } from '../../api/types'

const h = vi.hoisted(() => {
  const state = { balance: 1000 }
  return {
    state,
    api: {
      getAccount: () =>
        Promise.resolve({
          user_id: 1,
          balance: state.balance,
          initial_balance: 5000,
          position_value: 0,
          total_asset: state.balance,
        }),
      buy: (player_id: number, quantity: number) =>
        Promise.resolve({
          success: true as const,
          message: '买入成功',
          balance: state.balance,
          player_id,
          quantity,
          price: 120,
          trade_id: 1,
        }),
      sell: (player_id: number, quantity: number) =>
        Promise.resolve({
          success: true as const,
          message: '卖出成功',
          balance: state.balance,
          player_id,
          quantity,
          price: 120,
          trade_id: 2,
        }),
    },
  }
})

vi.mock('../../api', () => ({ api: h.api }))

function makePlayer(
  over: Partial<Pick<PlayerSummary, 'current_price' | 'status'>> = {},
): PlayerSummary {
  return {
    player_id: 1,
    name: 'ZywOo',
    display_name: 'ZywOo',
    team: 'Vitality',
    role: 'AWPer',
    current_price: 120,
    prev_price: 118,
    change_pct: 1.69,
    rating: 88,
    status: 'trading',
    ...over,
  }
}

async function panel(held: number | null, player: PlayerSummary = makePlayer()) {
  const w = mount(TradePanel, { props: { player, held } })
  await flushPromises()
  return w
}

/** 读数量输入框里的值（v-model.number 之后 DOM 上仍是字符串） */
function qtyInput(w: ReturnType<typeof mount>) {
  return (w.get('#trade-qty').element as HTMLInputElement).value
}

describe('TradePanel「最大」快捷档', () => {
  it('余额还没拉到：「最大」禁用并说明原因（不是点了没反应），但「清仓」照样能用', async () => {
    const w = await panel(0)
    expect(w.get('.chip-max').attributes('disabled')).toBeDefined()
    expect(w.get('.max-hint').text()).toContain('余额还没拉到，暂时算不出最大可买数量')
    // 数字档不受影响，后端没起来之前也能照常填数量
    expect(w.get('.chip').attributes('disabled')).toBeUndefined()

    // 清仓只依赖持仓数，余额未知时也允许点（这是两颗键的分工）
    const w3 = await panel(3)
    expect(w3.get('.chip-sell').attributes('disabled')).toBeUndefined()
    await w3.get('.chip-sell').trigger('click')
    expect(qtyInput(w3)).toBe('3')
  })

  it('按余额算：1000 币 ÷ 现价 120 → 最大 8 股，点一下填入并把约需金额算成 960.00', async () => {
    h.state.balance = 1000
    await refreshAccount()
    const w = await panel(0)
    expect(w.get('.chip-max').text()).toBe('最大')
    expect(w.get('.max-hint').text()).toContain('最大可买 8 股')
    await w.get('.chip-max').trigger('click')
    expect(qtyInput(w)).toBe('8')
    expect(w.get('.estimate').text()).toContain('960.00')
  })

  it('最大会扣已持有：余额够买 8 股、已持有 45 股 → 只给 5 股（一点就超仓的情况不会出现）', async () => {
    h.state.balance = 1000
    await refreshAccount()
    const w = await panel(45)
    expect(w.get('.max-hint').text()).toContain('最大可买 5 股')
    expect(w.get('.max-hint').text()).toContain('已持有 45 股')
    await w.get('.chip-max').trigger('click')
    expect(qtyInput(w)).toBe('5')
    expect(w.get('.estimate').text()).toContain('600.00') // 5 × 120
  })

  it('余额远大于 50 股时，「最大」封顶在 50（无持仓时仓位余量就是 50）', async () => {
    h.state.balance = 100000
    await refreshAccount()
    const w = await panel(0)
    expect(w.get('.max-hint').text()).toContain('最大可买 50 股')
    await w.get('.chip-max').trigger('click')
    expect(qtyInput(w)).toBe('50')
    expect(w.find('.invalid-hint').exists()).toBe(false) // 50 本身不触发本地校验
  })

  it('清仓 = 一次卖掉全部持仓，约需金额按持仓数实时算', async () => {
    h.state.balance = 1000
    await refreshAccount()
    const w = await panel(10)
    expect(w.get('.sell-hint').text()).toContain('清仓 = 一次卖出全部 10 股')
    await w.get('.chip-sell').trigger('click')
    expect(qtyInput(w)).toBe('10')
  })

  it('没有持仓时清仓禁用并说明，而不是默默填个 0', async () => {
    h.state.balance = 1000
    await refreshAccount()
    const w = await panel(0)
    expect(w.get('.chip-sell').attributes('disabled')).toBeDefined()
    expect(w.get('.sell-hint').text()).toContain('当前没有持仓，卖不出')
    await w.get('.chip-sell').trigger('click')
    expect(qtyInput(w)).toBe('1') // 点了无效，输入框保持原值
  })

  it('余额连 1 股都买不起 → 禁用 + 提示差额原因', async () => {
    h.state.balance = 50
    await refreshAccount()
    const w = await panel(0)
    expect(w.get('.chip-max').attributes('disabled')).toBeDefined()
    expect(w.get('.max-hint').text()).toContain('不够按现价 120.00 买 1 股')
  })

  it('已经满 50 股 → 「最大」禁用并说明到上限了（余额很足也一样）', async () => {
    h.state.balance = 5000
    await refreshAccount()
    const w = await panel(50)
    expect(w.get('.chip-max').attributes('disabled')).toBeDefined()
    expect(w.get('.max-hint').text()).toContain('到 50 股上限了')
    await w.get('.chip-max').trigger('click')
    expect(qtyInput(w)).toBe('1') // 点了无效，不会把数量改成 0
  })

  it('暂停交易时「最大」和其它档一起禁用（拦截原因由面板上方说明）', async () => {
    h.state.balance = 5000
    await refreshAccount()
    const w = await panel(10, makePlayer({ status: 'suspended' }))
    expect(w.get('.chip-max').attributes('disabled')).toBeDefined()
    expect(w.get('.chip-sell').attributes('disabled')).toBeDefined()
    expect(w.text()).toContain('暂停交易')
  })

  it('点「最大」填出来的数量不会被本地校验拦掉（始终在 1–50 之间）', async () => {
    h.state.balance = 1000
    await refreshAccount()
    const w = await panel(10)
    await w.get('.chip-max').trigger('click')
    expect(qtyInput(w)).toBe('8')
    expect(w.find('.invalid-hint').exists()).toBe(false)
    expect(w.get('button.buy').attributes('disabled')).toBeUndefined()
  })

  it('现价异常（0 或负数）时「最大」禁用，不会算出 Infinity', async () => {
    h.state.balance = 1000
    await refreshAccount()
    const w = await panel(0, makePlayer({ current_price: 0 }))
    expect(w.get('.chip-max').attributes('disabled')).toBeDefined()
    expect(w.text()).not.toContain('Infinity')
    expect(w.text()).not.toContain('NaN')
  })
})
