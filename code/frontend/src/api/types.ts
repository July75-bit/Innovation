/**
 * 白话导读：后端返回数据的"形状说明书"（TypeScript 类型定义），只有类型、没有一行运行代码。
 *
 * TypeScript 编译后这些 interface 会被完全删掉，它的作用是：
 *   - 写代码时编辑器能提示"PlayerSummary 里有 current_price 这个字段"；
 *   - 字段名写错 / 少写，保存时就报错，而不是运行时 undefined 白屏。
 *
 * 注意字段全是下划线（snake_case），和后端 JSON 一字不差——故意的，方便两边对照排查。
 * 想知道某个字段是什么业务含义 → 看接口契约 docs/software/api_contract.md。
 */

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

/* ---------------- 第 7 轮：私人账号（契约 §4.11~§4.14） ---------------- */

/** 账户身份：private = 注册出来的私人账户，public_demo = 未登录时共用的演示账户 */
export type AccountType = 'private' | 'public_demo'

/** 注册 / 登录响应里的账户信息（后端不回任何口令相关字段） */
export interface AuthUser {
  user_id: number
  nickname: string
  balance: number
  initial_balance: number
  created_at: string
  account_type: AccountType
}

/** §4.11 / §4.12：注册与登录成功都直接给令牌，前端不用再发一次登录 */
export interface AuthResponse {
  /** 原文只在这一次响应里出现，库里只存它的 SHA-256 */
  token: string
  expires_at: string
  user: AuthUser
}

/** §4.13：当前身份。authenticated=false 表示这一请求没带令牌，用的是公共演示账户 */
export interface MeResponse {
  authenticated: boolean
  user: AuthUser
}

/** §4.14：退出。revoked=false 表示本来就没带令牌（幂等成功，不是错误） */
export interface LogoutResponse {
  success: boolean
  message: string
  revoked: boolean
}
