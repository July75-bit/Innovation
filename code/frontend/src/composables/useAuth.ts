/**
 * 白话导读：注册 / 登录的全部前端逻辑——**现在是真鉴权**（第 7 轮私人账号）。
 *
 * 和上一版的区别：上一版账号只写浏览器 localStorage（后端没有 /api/auth，只能本地演）；
 * 这一版调后端四个接口（契约 §4.11~§4.14），口令散列、令牌签发、退出撤销都在服务端，
 * 余额 / 持仓 / 流水因此按账号隔离。界面代码没动：导出的还是那六个名字
 * （currentUser、isAuthenticated、register、login、logout、enterAsGuest）。
 *
 * 三种身份，别搞混：
 *   private      = 注册/登录出来的私人账户，数据独立；
 *   public_demo  = 未登录时后端共用的演示账户 demo（历史数据都在它身上）；
 *   anonymous    = 还没决定身份（首屏守卫会先把这一屏送去 /auth）。
 * "先随便逛逛（访客）"就是**故意不带令牌**用 public_demo，不是伪造的登录态。
 */
import { computed, readonly, ref } from 'vue'

import { api } from '../api'
import { ApiError } from '../api/client'
import { clearToken, getToken, restoreToken, setToken } from '../api/token'
import type { AccountType, AuthUser } from '../api/types'

/** 访客选择的存储键：只活于当前标签页，关标签页就回到"未登录"状态 */
const GUEST_CHOICE_KEY = 'playerstock.auth.guest.v1'

export interface RegisterInput {
  username: string
  password: string
  confirm: string
  remember: boolean
}

export interface LoginInput {
  username: string
  password: string
  remember: boolean
}

export interface AuthResult {
  ok: boolean
  message: string
}

/**
 * 界面关心的两份状态。
 * `token` 是"有没有登录"的唯一凭据（由后端签发）；`user` 是"登录的是谁"的快照，
 * 由 /api/auth/me 或注册/登录响应填。两者分开是因为后端可能暂时问不通：
 * 那时令牌还在，身份细节只是暂时不知道，不该把人踢回登录页。
 */
const token = ref<string | null>(restoreToken())
const user = ref<AuthUser | null>(null)
const accountType = ref<AccountType | 'anonymous'>('anonymous')
const guestChosen = ref(readGuestChoice())

/** 已经为哪一枚令牌确认过身份；令牌换了（登录、另一个标签页换号）就重新确认 */
let validatedToken: string | null = null

function readGuestChoice(): boolean {
  try {
    return sessionStorage.getItem(GUEST_CHOICE_KEY) === '1'
  } catch {
    return false
  }
}

function writeGuestChoice(chosen: boolean): void {
  try {
    if (chosen) sessionStorage.setItem(GUEST_CHOICE_KEY, '1')
    else sessionStorage.removeItem(GUEST_CHOICE_KEY)
  } catch {
    /* 隐私模式存不下：访客态只在当前这一屏有效，不影响正确性 */
  }
}

/** 清掉一切身份痕迹：令牌 + 内存用户 + 访客选择 */
function forgetSession(): void {
  clearToken()
  token.value = null
  user.value = null
  accountType.value = 'anonymous'
  guestChosen.value = false
  writeGuestChoice(false)
  validatedToken = null
}

function adopt(res: { user: AuthUser; token: string }, remember: boolean): void {
  setToken(res.token, remember ? 'remember' : 'session')
  token.value = res.token
  user.value = res.user
  accountType.value = res.user.account_type
  guestChosen.value = false
  writeGuestChoice(false)
  // 注册/登录响应本身就带回了身份，不必再打一次 /me
  validatedToken = res.token
}

/* ------------------------------ 表单校验 ------------------------------ */

/**
 * 前端先挡一道是为了少发一次请求、少闪一次错误；
 * 但**后端 app/core/security.py 有同一套规则**，谁也不能绕过谁（改规则要两边一起改）。
 */
export const USERNAME_PATTERN = /^[A-Za-z0-9_]{3,20}$/

export function validateUsername(value: string): string | null {
  const v = value.trim()
  if (!v) return '请填写用户名'
  if (v.length < 3) return '用户名至少 3 个字符'
  if (v.length > 20) return '用户名最多 20 个字符'
  if (!USERNAME_PATTERN.test(v)) return '用户名只能用字母、数字和下划线'
  return null
}

export function validatePassword(value: string): string | null {
  if (!value) return '请填写密码'
  if (value.length < 8) return '密码至少 8 位'
  if (!/[A-Za-z]/.test(value) || !/[0-9]/.test(value)) return '密码需同时包含字母和数字'
  return null
}

export interface PasswordStrength {
  score: 0 | 1 | 2 | 3
  label: string
}

/** 强度条只做提示，不做拦截：拦太死的表单在演示时只会添乱 */
export function passwordStrength(value: string): PasswordStrength {
  if (!value) return { score: 0, label: '' }
  let hits = 0
  if (value.length >= 8) hits += 1
  if (/[A-Za-z]/.test(value) && /[0-9]/.test(value)) hits += 1
  if (/[^A-Za-z0-9]/.test(value) || value.length >= 12) hits += 1
  if (hits <= 1) return { score: 1, label: '弱' }
  if (hits === 2) return { score: 2, label: '中' }
  return { score: 3, label: '较强' }
}

/* ------------------------------ 状态（具名导出，界面与守卫共用） ------------------------------ */

export const currentUser = computed<AuthUser | null>(() => user.value)

/** 有令牌 = 已登录私人账户（身份细节可能还没拿到，但"登录着"这件事是确定的） */
export const isLoggedIn = computed(() => token.value !== null)

/** 明确选了"先随便逛逛"= 用公共演示账户，不算登录 */
export const isGuest = computed(() => guestChosen.value && token.value === null)

/** 路由守卫的放行条件：私人账号或访客都算"可以进主界面" */
export const isAuthenticated = computed(() => isLoggedIn.value || isGuest.value)

/** 侧栏那行小字：私人账户 / 公共演示账户 / 未登录 */
export const accountLabel = computed(() => {
  if (isLoggedIn.value) return '私人账户'
  if (guestChosen.value) return '公共演示账户'
  return '未登录'
})

/* ------------------------------ 动作 ------------------------------ */

/**
 * 首屏 / 每次导航前确认身份：本地有令牌就问一次 /api/auth/me。
 *
 * 三条容易做错的地方，都在这里堵住了：
 * 1. 必须**先于**守卫判断完成，否则刷新后第一屏会被误判成未登录、闪一下弹回登录页；
 * 2. 只有 401（过期 / 被撤销）才清会话；后端没起、网络错误都保留令牌——
 *    不然本地重启一次后端就要全员重新登录；
 * 3. 同一枚令牌只确认一次（validatedToken），避免每次导航都多打一个请求。
 */
export async function bootstrap(): Promise<void> {
  const current = restoreToken()
  token.value = current
  if (current === validatedToken) return

  if (!current) {
    user.value = null
    accountType.value = 'anonymous'
    return
  }

  try {
    const res = await api.me()
    user.value = res.user
    accountType.value = res.user.account_type
    validatedToken = current
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) forgetSession()
  }
}

export async function register(input: RegisterInput): Promise<AuthResult> {
  const invalid = validateUsername(input.username) ?? validatePassword(input.password)
  if (invalid) return { ok: false, message: invalid }
  if (input.confirm !== input.password) return { ok: false, message: '两次输入的密码不一致' }

  try {
    const res = await api.register(input.username.trim(), input.password)
    adopt(res, input.remember)
    return { ok: true, message: `注册成功，欢迎 ${res.user.nickname}` }
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : '注册失败，请稍后重试' }
  }
}

export async function login(input: LoginInput): Promise<AuthResult> {
  const invalid = validateUsername(input.username)
  if (invalid) return { ok: false, message: invalid }
  if (!input.password) return { ok: false, message: '请填写密码' }

  try {
    const res = await api.login(input.username.trim(), input.password)
    adopt(res, input.remember)
    return { ok: true, message: `欢迎回来，${res.user.nickname}` }
  } catch (error) {
    return { ok: false, message: error instanceof Error ? error.message : '登录失败，请稍后重试' }
  }
}

/** 访客进入：故意不带令牌，后端把这一路记在公共演示账户 demo 上 */
export function enterAsGuest(): void {
  forgetSession()
  guestChosen.value = true
  writeGuestChoice(true)
  accountType.value = 'public_demo'
}

/**
 * 退出：先撤销服务端令牌，再清本地。
 * 后端没起 / 请求失败也照样清本地——"退出"不能因为网络失败就把人留在登录态里。
 */
export async function logout(): Promise<void> {
  try {
    if (getToken()) await api.logout()
  } catch {
    /* 撤销失败：本地仍然清干净，令牌最多在服务端等到自然过期 */
  }
  forgetSession()
}

export function useAuth() {
  return {
    currentUser,
    accountType,
    accountLabel,
    isLoggedIn,
    isGuest,
    isAuthenticated,
    /** 只读导出：界面不许直接改身份，只能走 register / login / logout / enterAsGuest */
    session: readonly(
      computed(() => (token.value ? 'private' : guestChosen.value ? 'guest' : 'none')),
    ),
    bootstrap,
    register,
    login,
    enterAsGuest,
    logout,
  }
}
