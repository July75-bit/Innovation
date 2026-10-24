/**
 * 接口契约类型（docs/software/api_contract.md §4）
 *
 * 铁律：
 * - 字段一律 snake_case，与后端返回完全一致，不做驼峰转换；
 * - change_pct / profit 等由后端算好，前端不重算、不二次截断；
 * - rating 是 0-100 的项目**模拟**综合表现分，不是 HLTV Rating，UI 必须标注「模拟」。
 */

export type PlayerStatus = 'trading' | 'suspended'
export type TradeSide = 'BUY' | 'SELL'
export type AdviceAction = 'BUY' | 'SELL' | 'HOLD'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type AdviceSource = 'llm' | 'rule_fallback'

/** §4.2 市场选手列表项 */
export interface PlayerSummary {
  player_id: number
  name: string
  display_name: string | null
  team: string | null
  /** 选手真实位置：AWPer / Entry / Rifler / IGL / Support / Lurker */
  role: string | null
  current_price: number
  prev_price: number
  /** 后端算好的涨跌幅（%），前端不要自己算 */
  change_pct: number
  /** 0-100 模拟综合表现分（非官方统计） */
  rating: number
  status: PlayerStatus
}

/** §4.3 单个选手详情 */
export interface PlayerDetail extends PlayerSummary {
  latest_reason: string | null
}

/** §4.4 价格历史 */
export interface PricePoint {
  /** ISO 8601 UTC，如 2026-01-01T10:05:00Z */
  ts: string
  price: number
  reason: string
}

export interface PriceHistoryResponse {
  player_id: number
  /** 时间升序；无数据为空数组（不返回 404） */
  points: PricePoint[]
}

/** §4.5 账户 */
export interface Account {
  user_id: number
  balance: number
  initial_balance: number
  position_value: number
  total_asset: number
}

/** §4.6 持仓项（quantity 为 0 的选手不会出现） */
export interface PositionItem {
  player_id: number
  name: string
  quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  profit: number
  profit_pct: number
}

/** §4.7 / §4.8 买入、卖出成功响应（200） */
export interface TradeResponse {
  success: true
  message: string
  balance: number
  player_id: number
  quantity: number
  price: number
  trade_id: number
}

/** §4.9 交易流水项（后端已按时间倒序） */
export interface TradeItem {
  trade_id: number
  player_id: number
  name: string
  side: TradeSide
  quantity: number
  price: number
  amount: number
  balance_after: number
  created_at: string
}

/** §4.10 AI 分析：成功时是裸对象（无 success 字段） */
export interface AnalysisResponse {
  player_id: number
  action: AdviceAction
  reason: string
  risk_level: RiskLevel
  /** AI 故障时后端仍返回 200 并降级为 rule_fallback，前端只按此字段区分展示 */
  source: AdviceSource
  disclaimer: string
}

/** §1 健康检查 */
export interface HealthResponse {
  status: string
  service: string
}

/** §2 统一错误体（所有 4xx/5xx） */
export interface ApiErrorBody {
  success: false
  /** 可直接展示给用户的中文，前端不写映射表 */
  message: string
  /** 机器码，如 INSUFFICIENT_BALANCE */
  code: string
}
