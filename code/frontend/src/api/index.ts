/**
 * 白话导读：后端接口的"总机"——页面上所有请求都从这里发，一共 10 个函数。
 *
 * 页面里的典型写法： import { api } from '../api'  →  await api.listPlayers()
 * 每个函数都只做两件事：拼好 URL 交给 client.ts 的 request()，并声明返回值的类型。
 *
 * 如果后端接口改名/加字段，只改这个文件和 types.ts，页面基本不用动（分层的好处）。
 * VITE_USE_MOCK=true 时这里会整体切到 src/mock/players.ts 的假数据，页面代码完全不用改。
 */

/**
 * 10 个业务接口（契约 §3）。路径与字段以 docs/software/api_contract.md 为准，
 * 契约已冻结，改字段必须走 §6 变更流程。
 *
 * VITE_USE_MOCK=true 时全部切到 src/mock/players.ts 的内存模拟数据（开发兜底）；
 * 默认（false / 未设置）走真实后端接口。上线前必须确认为 false。
 */
import { request } from './client'
import { getToken } from './token'
import { mockApi } from '../mock/players'
import { mockAuth } from '../mock/auth'
import type {
  Account,
  AccountRebuildResponse,
  AgentBriefResponse,
  AgentDecisionLogResponse,
  AgentDecisionResponse,
  AgentNarrativeResponse,
  AgentPanelResponse,
  AgentToolsResponse,
  AnalysisResponse,
  AuthResponse,
  DeleteAccountResponse,
  HealthResponse,
  LogoutResponse,
  MeResponse,
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

  /** §4.2 市场选手列表（16 名，无分页，按 player_id 升序） */
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

  /* ---------------- 第 7 轮：私人账号 ---------------- */

  /**
   * §4.11 注册（成功即登录，201）。
   * 失败码：INVALID_INPUT(422) / USERNAME_TAKEN(409) / USERNAME_RESERVED(409)。
   */
  register: (username: string, password: string): Promise<AuthResponse> =>
    USE_MOCK
      ? fromMock(() => mockAuth.register(username, password))
      : request<AuthResponse>('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        }),

  /** §4.12 登录。账号不存在与口令错都是 INVALID_CREDENTIALS(401)，同一句话 */
  login: (username: string, password: string): Promise<AuthResponse> =>
    USE_MOCK
      ? fromMock(() => mockAuth.login(username, password))
      : request<AuthResponse>('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        }),

  /**
   * §4.13 当前身份。只在本地已有令牌时调用（启动时校验令牌还管不管用）。
   * 401 = 令牌过期/被撤销 → useAuth 清会话把用户送回登录页。
   */
  me: (): Promise<MeResponse> =>
    USE_MOCK ? fromMock(() => mockAuth.me(getToken())) : request<MeResponse>('/api/auth/me'),

  /** §4.14 退出（撤销令牌）。网络失败不阻塞前端清本地状态，见 useAuth.logout */
  logout: (): Promise<LogoutResponse> =>
    USE_MOCK
      ? fromMock(() => mockAuth.logout(getToken()))
      : request<LogoutResponse>('/api/auth/logout', { method: 'POST' }),

  /**
   * §4.16 删除账号（不可恢复）。必须带口令，后端四道闸见契约。
   *
   * 用 DELETE + 请求体而不是 POST：语义上这是"删除资源"，而且后端 allow_methods=["*"]
   * 已放开，preflight 一次就够。注意 starlette 的 TestClient.delete() 不收 json=，
   * 后端测试里走的是 client.request('DELETE', …)，浏览器 fetch 没有这个限制。
   */
  deleteAccount: (password: string): Promise<DeleteAccountResponse> =>
    USE_MOCK
      ? fromMock(() => mockAuth.deleteAccount(getToken(), password))
      : request<DeleteAccountResponse>('/api/auth/account', {
          method: 'DELETE',
          body: JSON.stringify({ password }),
        }),

  /**
   * §4.17 余额重建：把自己这个账户恢复成刚注册的样子（余额回 5000、清空本账户持仓与流水）。
   * 重置行情（/api/debug/reseed）不会动账号余额与流水（它们跟着账号走），
   * 所以"我想重新开始"必须用户自己按这个按钮。
   */
  rebuildAccount: (): Promise<AccountRebuildResponse> =>
    USE_MOCK
      ? fromMock(() => ({
          user_id: 1,
          balance: 5000,
          cleared_positions: 0,
          cleared_trades: 0,
          note: 'mock',
        }))
      : request<AccountRebuildResponse>('/api/account/rebuild?confirm=true', { method: 'POST' }),

  /** §4.18 智能体决策卡：建议 + 仓位 + 止损 + 置信度（只读，不下单） */
  getAgentDecision: (playerId: number): Promise<AgentDecisionResponse> =>
    USE_MOCK
      ? fromMock(() => ({
          advice: {
            player_id: playerId,
            action: 'HOLD',
            reason: 'mock 建议',
            risk_level: 'MEDIUM',
            source: 'rule_fallback',
            disclaimer: 'mock',
          },
          plan: {
            suggested_quantity: 0,
            stop_loss_price: null,
            confidence: 0.55,
            risk_budget_ratio: 0.06,
            rationale: ['mock'],
            note: 'mock',
          },
          trace_id: 0,
          snapshot: {
            balance: 5000,
            held_quantity: 0,
            current_price: 100,
            change_pct: 0,
            rating: 80,
          },
          latency_ms: 0,
          disclaimer: 'mock',
        }))
      : request<AgentDecisionResponse>(`/api/agent/decision/${playerId}`),

  /** §4.19 今日智能体简报（后端缓存 10 分钟） */
  getAgentBrief: (): Promise<AgentBriefResponse> =>
    USE_MOCK
      ? fromMock(() => ({
          generated_at: new Date().toISOString(),
          ttl_seconds: 600,
          items: [
            { title: '今日最该看一眼', detail: 'mock 标的' },
            { title: '低价区标的', detail: 'mock' },
            { title: '停牌提醒', detail: '无' },
          ],
          summary: 'mock 简报',
          source: 'rule_fallback' as const,
          latency_ms: 0,
          cached: false,
        }))
      : request<AgentBriefResponse>('/api/agent/brief'),

  /** §4.20 人在环：记录采纳/忽略（不触发交易） */
  recordAgentDecision: (payload: {
    player_id: number
    advice_action: string
    advice_source: string
    decision: 'accept' | 'ignore'
    trace_id?: number | null
  }): Promise<AgentDecisionLogResponse> =>
    USE_MOCK
      ? fromMock(() => ({ success: true, decision_id: 0, message: 'mock' }))
      : request<AgentDecisionLogResponse>('/api/agent/decisions', {
          method: 'POST',
          body: JSON.stringify(payload),
        }),

  /** §4.22 多角色协作纪要（分析师→风控→交易员），用户点开卡片才请求 */
  getAgentPanel: (playerId: number): Promise<AgentPanelResponse> =>
    USE_MOCK
      ? fromMock(() => ({
          player_id: playerId,
          trace_id: 0,
          latency_ms: 0,
          source: 'rule_fallback' as const,
          minutes: [{ role: 'system', content: 'mock 纪要' }],
          final: { action: 'HOLD', risk_level: 'MEDIUM', reason: 'mock' },
          note: 'mock',
        }))
      : request<AgentPanelResponse>(`/api/agent/panel/${playerId}`),

  /** §4.23 叙事归因（把规则 reason 扩写成因果解释） */
  getAgentNarrative: (playerId: number): Promise<AgentNarrativeResponse> =>
    USE_MOCK
      ? fromMock(() => ({
          player_id: playerId,
          ts: new Date().toISOString(),
          narrative: 'mock 归因',
          source: 'rule_fallback' as const,
          change_pct: 0,
          big_move: false,
          cached: false,
        }))
      : request<AgentNarrativeResponse>(`/api/agent/narrative/${playerId}`),

  /** §4.24 工具调用演示：模型自己调只读工具取数 */
  getAgentTools: (playerId: number): Promise<AgentToolsResponse> =>
    USE_MOCK
      ? fromMock(() => ({
          player_id: playerId,
          answer: 'mock',
          rounds: 0,
          source: 'rule_fallback' as const,
          tool_calls: [],
        }))
      : request<AgentToolsResponse>(`/api/agent/tools/${playerId}`),
}
