/**
 * 10 个业务接口（契约 §3）。路径与字段以 docs/software/api_contract.md 为准，
 * 契约已冻结，改字段必须走 §6 变更流程。
 *
 * VITE_USE_MOCK=true 时全部切到 src/mock/players.ts 的内存模拟数据（开发兜底）；
 * 默认（false / 未设置）走真实后端接口。上线前必须确认为 false。
 */
import { request } from './client'
import { mockApi } from '../mock/players'
import type {
  Account,
  AnalysisResponse,
  HealthResponse,
  PlayerDetail,
  PlayerSummary,
  PositionItem,
  PriceHistoryResponse,
  TradeItem,
  TradeResponse,
} from './types'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

/** 同步 mock 结果包装成 Promise，保持与真实接口完全一致的调用形状 */
const fromMock = <T>(fn: () => T): Promise<T> => Promise.resolve().then(fn)

export const api = {
  /** §4.1 健康检查 */
  health: (): Promise<HealthResponse> =>
    USE_MOCK ? fromMock(mockApi.health) : request<HealthResponse>('/api/health'),

  /** §4.2 市场选手列表（8 名，无分页，按 player_id 升序） */
  listPlayers: (): Promise<PlayerSummary[]> =>
    USE_MOCK ? fromMock(mockApi.listPlayers) : request<PlayerSummary[]>('/api/players'),

  /** §4.3 单个选手详情（404 = PLAYER_NOT_FOUND） */
  getPlayer: (playerId: number): Promise<PlayerDetail> =>
    USE_MOCK
      ? fromMock(() => mockApi.getPlayer(playerId))
      : request<PlayerDetail>(`/api/players/${playerId}`),

  /** §4.4 价格历史（升序，空数据 points:[]，不 404） */
  getPriceHistory: (playerId: number): Promise<PriceHistoryResponse> =>
    USE_MOCK
      ? fromMock(() => mockApi.getPriceHistory(playerId))
      : request<PriceHistoryResponse>(`/api/players/${playerId}/prices`),

  /** §4.5 账户余额 */
  getAccount: (): Promise<Account> =>
    USE_MOCK ? fromMock(mockApi.getAccount) : request<Account>('/api/account'),

  /** §4.6 持仓列表（清仓选手不出现） */
  getPositions: (): Promise<PositionItem[]> =>
    USE_MOCK ? fromMock(mockApi.getPositions) : request<PositionItem[]>('/api/positions'),

  /** §4.7 买入：{player_id, quantity}，quantity 必须正整数 */
  buy: (playerId: number, quantity: number): Promise<TradeResponse> =>
    USE_MOCK
      ? fromMock(() => mockApi.buy(playerId, quantity))
      : request<TradeResponse>('/api/trades/buy', {
          method: 'POST',
          body: JSON.stringify({ player_id: playerId, quantity }),
        }),

  /** §4.8 卖出：失败 INSUFFICIENT_POSITION，不允许卖空 */
  sell: (playerId: number, quantity: number): Promise<TradeResponse> =>
    USE_MOCK
      ? fromMock(() => mockApi.sell(playerId, quantity))
      : request<TradeResponse>('/api/trades/sell', {
          method: 'POST',
          body: JSON.stringify({ player_id: playerId, quantity }),
        }),

  /** §4.9 交易流水（后端已按时间倒序） */
  listTrades: (): Promise<TradeItem[]> =>
    USE_MOCK ? fromMock(mockApi.listTrades) : request<TradeItem[]>('/api/trades'),

  /**
   * §4.10 AI 分析。
   * 成功返回裸对象（无 success 字段）；AI 故障一律 200 + source='rule_fallback'，
   * 所以这里不需要为 AI 失败写额外分支，只有 404（PLAYER_NOT_FOUND）走错误体。
   */
  getAnalysis: (playerId: number): Promise<AnalysisResponse> =>
    USE_MOCK
      ? fromMock(() => mockApi.getAnalysis(playerId))
      : request<AnalysisResponse>(`/api/analysis/${playerId}`),
}
