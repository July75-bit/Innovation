/**
 * 本地模拟数据（VITE_USE_MOCK=true 时启用）。
 *
 * 用途：B 的后端未就绪 / 断网演示时的开发兜底，让 4 个页面始终可看可点。
 * 数据源：逐字复制 data/seed_players.json（真实选手身份 + 项目模拟价格/评分）。
 * 业务规则与后端契约一致（§4.7 校验顺序、50 股上限、暂停交易、不允许卖空），
 * 但**只存在内存里**，刷新页面即重置；真实交易永远以数据库为准。
 */
import { ApiError } from '../api/client'
import type {
  Account,
  AnalysisResponse,
  HealthResponse,
  PlayerDetail,
  PlayerSummary,
  PositionItem,
  PriceHistoryResponse,
  PricePoint,
  TradeItem,
  TradeResponse,
} from '../api/types'

interface MockSeed {
  player_id: number
  name: string
  display_name: string
  team: string
  role: string
  initial_price: number
  prev_price: number
  current_price: number
  rating: number
  status: 'trading' | 'suspended'
}

const SEED: MockSeed[] = [
  {
    player_id: 1,
    name: 'ZywOo',
    display_name: 'ZywOo',
    team: 'Vitality',
    role: 'AWPer',
    initial_price: 120.0,
    prev_price: 120.0,
    current_price: 126.0,
    rating: 88,
    status: 'trading',
  },
  {
    player_id: 2,
    name: 'donk',
    display_name: 'donk',
    team: 'Spirit',
    role: 'Rifler',
    initial_price: 140.0,
    prev_price: 140.0,
    current_price: 143.5,
    rating: 90,
    status: 'trading',
  },
  {
    player_id: 3,
    name: 'm0NESY',
    display_name: 'm0NESY',
    team: 'G2',
    role: 'AWPer',
    initial_price: 96.0,
    prev_price: 96.0,
    current_price: 91.2,
    rating: 86,
    status: 'trading',
  },
  {
    player_id: 4,
    name: 'NiKo',
    display_name: 'NiKo',
    team: 'Falcons',
    role: 'Rifler',
    initial_price: 80.0,
    prev_price: 80.0,
    current_price: 74.4,
    rating: 80,
    status: 'trading',
  },
  {
    player_id: 5,
    name: 'ropz',
    display_name: 'ropz',
    team: 'FaZe Clan',
    role: 'Lurker',
    initial_price: 105.0,
    prev_price: 105.0,
    current_price: 105.0,
    rating: 78,
    status: 'trading',
  },
  {
    player_id: 6,
    name: 'jL',
    display_name: 'jL',
    team: 'NAVI',
    role: 'Rifler',
    initial_price: 88.0,
    prev_price: 88.0,
    current_price: 90.2,
    rating: 74,
    status: 'trading',
  },
  {
    player_id: 7,
    name: 'sh1ro',
    display_name: 'sh1ro',
    team: 'Spirit',
    role: 'AWPer',
    initial_price: 130.0,
    prev_price: 130.0,
    current_price: 136.5,
    rating: 85,
    status: 'suspended',
  },
  {
    player_id: 8,
    name: 'flameZ',
    display_name: 'flameZ',
    team: 'Vitality',
    role: 'Rifler',
    initial_price: 70.0,
    prev_price: 70.0,
    current_price: 63.0,
    rating: 66,
    status: 'trading',
  },
]

const round2 = (n: number) => Math.round(n * 100) / 100
const changePct = (cur: number, prev: number) =>
  prev > 0 ? round2(((cur - prev) / prev) * 100) : 0

function toSummary(s: MockSeed): PlayerSummary {
  return {
    player_id: s.player_id,
    name: s.name,
    display_name: s.display_name,
    team: s.team,
    role: s.role,
    current_price: s.current_price,
    prev_price: s.prev_price,
    change_pct: changePct(s.current_price, s.prev_price),
    rating: s.rating,
    status: s.status,
  }
}

/** 可变内存态（模拟数据库） */
const state = {
  balance: 5000.0,
  initialBalance: 5000.0,
  positions: new Map<number, { quantity: number; avgCost: number }>(),
  trades: [] as TradeItem[],
  tradeSeq: 0,
}

function pricePoints(s: MockSeed): PricePoint[] {
  const now = Date.now()
  const points: PricePoint[] = [
    { ts: new Date(now - 5 * 60_000).toISOString(), price: s.initial_price, reason: '初始价格' },
  ]
  if (s.current_price !== s.initial_price) {
    points.push({
      ts: new Date(now).toISOString(),
      price: s.current_price,
      reason: '模拟比赛表现调整（种子数据，待 C 的定价引擎接管）',
    })
  }
  return points
}

function account(): Account {
  let positionValue = 0
  for (const [pid, pos] of state.positions) {
    const seed = SEED.find((s) => s.player_id === pid)
    if (seed) positionValue += seed.current_price * pos.quantity
  }
  positionValue = round2(positionValue)
  return {
    user_id: 1,
    balance: round2(state.balance),
    initial_balance: state.initialBalance,
    position_value: positionValue,
    total_asset: round2(state.balance + positionValue),
  }
}

/** 与后端 §4.7 相同的校验顺序：存在 → 数量 → 暂停 → 余额/持仓 → 上限 */
function trade(side: 'BUY' | 'SELL', playerId: number, quantity: number): TradeResponse {
  const seed = SEED.find((s) => s.player_id === playerId)
  if (!seed) throw new ApiError('选手不存在', 'PLAYER_NOT_FOUND', 404)
  if (!Number.isInteger(quantity) || quantity < 1)
    throw new ApiError('请求参数不合法：quantity', 'VALIDATION_ERROR', 422)
  if (seed.status !== 'trading')
    throw new ApiError(
      '该选手比赛进行中，暂停交易，请等结算完成后重试',
      'PLAYER_TRADING_SUSPENDED',
      400,
    )

  const held = state.positions.get(playerId)?.quantity ?? 0
  const price = seed.current_price
  const cost = round2(price * quantity)

  if (side === 'BUY') {
    if (cost > state.balance)
      throw new ApiError(
        `余额不足，当前余额 ${state.balance.toFixed(2)}，需要 ${cost.toFixed(2)}`,
        'INSUFFICIENT_BALANCE',
        400,
      )
    if (held + quantity > 50)
      throw new ApiError('超过单选手 50 股持仓上限', 'POSITION_LIMIT_EXCEEDED', 400)
    const prevAvg = state.positions.get(playerId)?.avgCost ?? 0
    state.positions.set(playerId, {
      quantity: held + quantity,
      avgCost: round2((prevAvg * held + cost) / (held + quantity)),
    })
    state.balance = round2(state.balance - cost)
  } else {
    if (held < quantity)
      throw new ApiError(
        `持仓不足，当前持有 ${held} 股，本次卖出 ${quantity} 股`,
        'INSUFFICIENT_POSITION',
        400,
      )
    const left = held - quantity
    if (left === 0) state.positions.delete(playerId)
    else state.positions.set(playerId, { quantity: left, avgCost: prevAvgCost(playerId) })
    state.balance = round2(state.balance + cost)
  }

  state.tradeSeq += 1
  const item: TradeItem = {
    trade_id: state.tradeSeq,
    player_id: seed.player_id,
    name: seed.name,
    side,
    quantity,
    price,
    amount: cost,
    balance_after: round2(state.balance),
    created_at: new Date().toISOString(),
  }
  state.trades.unshift(item)
  return {
    success: true,
    message: side === 'BUY' ? '买入成功' : '卖出成功',
    balance: item.balance_after,
    player_id: seed.player_id,
    quantity,
    price,
    trade_id: item.trade_id,
  }
}

function prevAvgCost(playerId: number): number {
  return state.positions.get(playerId)?.avgCost ?? 0
}

export const mockApi = {
  health: (): HealthResponse => ({ status: 'ok', service: 'playerstock-mock' }),
  listPlayers: (): PlayerSummary[] => SEED.map(toSummary),
  getPlayer: (id: number): PlayerDetail => {
    const seed = SEED.find((s) => s.player_id === id)
    if (!seed) throw new ApiError('选手不存在', 'PLAYER_NOT_FOUND', 404)
    return {
      ...toSummary(seed),
      latest_reason: '模拟比赛表现调整（种子数据，mock 模式）',
    }
  },
  getPriceHistory: (id: number): PriceHistoryResponse => {
    const seed = SEED.find((s) => s.player_id === id)
    if (!seed) throw new ApiError('选手不存在', 'PLAYER_NOT_FOUND', 404)
    return { player_id: id, points: pricePoints(seed) }
  },
  getAccount: account,
  getPositions: (): PositionItem[] => {
    const list: PositionItem[] = []
    for (const [pid, pos] of state.positions) {
      const seed = SEED.find((s) => s.player_id === pid)
      if (!seed || pos.quantity <= 0) continue
      const marketValue = round2(seed.current_price * pos.quantity)
      const cost = round2(pos.avgCost * pos.quantity)
      list.push({
        player_id: pid,
        name: seed.name,
        quantity: pos.quantity,
        avg_cost: pos.avgCost,
        current_price: seed.current_price,
        market_value: marketValue,
        profit: round2(marketValue - cost),
        profit_pct: cost > 0 ? round2(((marketValue - cost) / cost) * 100) : 0,
      })
    }
    return list
  },
  buy: (playerId: number, quantity: number) => trade('BUY', playerId, quantity),
  sell: (playerId: number, quantity: number) => trade('SELL', playerId, quantity),
  listTrades: (): TradeItem[] => [...state.trades],
  getAnalysis: (id: number): AnalysisResponse => {
    const seed = SEED.find((s) => s.player_id === id)
    if (!seed) throw new ApiError('选手不存在', 'PLAYER_NOT_FOUND', 404)
    const chg = changePct(seed.current_price, seed.prev_price)
    const action = chg >= 4 ? 'HOLD' : chg <= -5 ? 'BUY' : 'HOLD'
    return {
      player_id: id,
      action,
      reason: `（mock）近两点变动 ${chg}%，模拟表现分 ${seed.rating}，仅供前端开发演示`,
      risk_level: 'LOW',
      source: 'rule_fallback',
      disclaimer: '仅为分析建议，不构成投资建议；AI 不会自动交易',
    }
  },
}
