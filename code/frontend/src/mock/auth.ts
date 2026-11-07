/**
 * 白话导读：VITE_USE_MOCK=true 时的假登录（内存里演一遍，不发请求）。
 *
 * 为什么要单独做一份 mock：mock 开关的约定是"全部接口切本地模拟数据"，
 * 如果只有 auth 四个接口偷偷打真后端，mock 模式下就会出现
 * "行情是假的、登录是真的"这种半吊子状态，比全假更难解释。
 *
 * 与后端的差异（只在 mock 里，别当真）：口令明文存内存、令牌是假串、刷新即重置。
 * 校验规则与后端 app/core/security.py 一致，这样切回真接口时行为不变。
 */
import type { AuthResponse, AuthUser } from '../api/types'

interface MockAccount {
  user_id: number
  nickname: string
  password: string
  balance: number
  initial_balance: number
  created_at: string
}

const accounts: MockAccount[] = []
const tokens = new Map<string, number>()
let nextId = 100

const USERNAME_PATTERN = /^[A-Za-z0-9_]{3,20}$/

/** mock 也照契约 §2 抛 {message, code, status}，页面的错误分支才能共用一套 */
function apiError(message: string, code: string, status: number): Error {
  const err = new Error(message) as Error & { code: string; status: number }
  err.code = code
  err.status = status
  return err
}

function checkRules(username: string, password: string): string {
  const name = username.trim()
  if (!USERNAME_PATTERN.test(name)) return '用户名只能用字母、数字和下划线，长度 3–20'
  if (name.toLowerCase() === 'demo') return '用户名 demo 是公共演示账户，换一个名字'
  if (password.length < 8) return '密码至少 8 位'
  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) return '密码需同时包含字母和数字'
  return ''
}

function toUser(account: MockAccount): AuthUser {
  return {
    user_id: account.user_id,
    nickname: account.nickname,
    balance: account.balance,
    initial_balance: account.initial_balance,
    created_at: account.created_at,
    account_type: 'private',
  }
}

function issue(account: MockAccount): AuthResponse {
  const token = `mock-token-${account.user_id}-${tokens.size + 1}`
  tokens.set(token, account.user_id)
  return {
    token,
    expires_at: new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString(),
    user: toUser(account),
  }
}

export const mockAuth = {
  register(username: string, password: string): AuthResponse {
    const message = checkRules(username, password)
    if (message) throw apiError(message, 'INVALID_INPUT', 422)
    const name = username.trim()
    if (accounts.some((a) => a.nickname.toLowerCase() === name.toLowerCase())) {
      throw apiError(`用户名 ${name} 已被注册`, 'USERNAME_TAKEN', 409)
    }
    const account: MockAccount = {
      user_id: nextId++,
      nickname: name,
      password,
      balance: 5000,
      initial_balance: 5000,
      created_at: new Date().toISOString(),
    }
    accounts.push(account)
    return issue(account)
  },

  login(username: string, password: string): AuthResponse {
    const account = accounts.find((a) => a.nickname.toLowerCase() === username.trim().toLowerCase())
    // 与后端一致：账号不存在和口令错都是同一句话，不给枚举账号名留口子
    if (!account || account.password !== password) {
      throw apiError('用户名或密码不正确', 'INVALID_CREDENTIALS', 401)
    }
    return issue(account)
  },

  me(token: string | null) {
    const id = token ? tokens.get(token) : undefined
    const account = id === undefined ? undefined : accounts.find((a) => a.user_id === id)
    if (!account) throw apiError('登录状态已失效，请重新登录', 'UNAUTHORIZED', 401)
    return { authenticated: true, user: toUser(account) }
  },

  logout(token: string | null): { success: boolean; message: string; revoked: boolean } {
    const had = token ? tokens.delete(token) : false
    return { success: true, message: '已退出登录', revoked: had }
  },

  /**
   * §4.16 删除账号（mock 版）。与后端同规则：没令牌 / 口令不对 / 令牌认不出人，一律不删。
   * mock 没有持仓与流水（那是 players.ts 的内存账），所以行数只回报令牌一条。
   */
  deleteAccount(token: string | null, password: string) {
    if (!token) throw apiError('公共演示账户不能删除：请先登录自己的账号', 'UNAUTHORIZED', 401)
    const id = tokens.get(token)
    const account = id === undefined ? undefined : accounts.find((a) => a.user_id === id)
    if (!account) throw apiError('登录状态已失效，请重新登录', 'UNAUTHORIZED', 401)
    if (account.password !== password) {
      throw apiError('密码不正确，未能删除账号', 'INVALID_CREDENTIALS', 401)
    }
    tokens.delete(token)
    accounts.splice(accounts.indexOf(account), 1)
    return {
      success: true,
      message: '账号已删除',
      deleted_positions: 0,
      deleted_trades: 0,
      deleted_tokens: 1,
    }
  },
}
