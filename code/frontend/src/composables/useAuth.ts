/**
 * 注册 / 登录的本地账号态（模块级 ref，沿用团队"不装 Pinia"的约定）。
 *
 * 为什么是纯前端：本轮需求只要"本地查看"的注册与登录界面，后端没有 /api/auth 契约，
 * 真去发请求只会撞 CORS + 404，答辩现场反而更难看。所以账号只落在浏览器
 * localStorage 里，密码只存"加盐 SHA-256 摘要"（绝不存明文）。
 *
 * 注册字段刻意保持最小：**只要用户名 + 密码**（确认密码算密码的一部分）。
 * 邮箱/昵称这类字段后端没有对应接口，收上来也只是本地留着好看，不如不收。
 *
 * 铁律：这是**演示级**实现，不是真实鉴权——没有过期、没有签名、没有服务端校验，
 * 清掉浏览器数据就没了。将来接后端时，把这里的 register/login 换成 api.* 即可，
 * 视图层只依赖导出的这几个函数，不用改界面。
 */
import { computed, readonly, ref } from 'vue'

/** 本地存储键：带版本号，将来字段结构变了可以整体作废，不至于读到半截数据 */
const USERS_KEY = 'playerstock.auth.users.v1'
/** 勾选"记住我"的会话：localStorage，关掉浏览器再开还是登录态 */
const SESSION_KEY = 'playerstock.auth.session.v1'
/** 没勾"记住我" / 访客态：sessionStorage，关掉标签页就退出，符合"记住我"的直觉 */
const SESSION_ONCE_KEY = 'playerstock.auth.session.v1.once'

/** 落库的用户（含摘要与盐，绝不返回给界面层） */
interface StoredUser {
  username: string
  salt: string
  hash: string
  created_at: string
}

/** 界面层拿到的用户（去掉了盐与摘要） */
export interface AuthUser {
  username: string
  created_at: string
}

/**
 * 会话：
 * - user  = 注册/登录成功，侧栏显示用户名与退出入口；
 * - guest = 「先随便逛逛」，能看行情但不算登录（答辩时后端没起也能走完整流程）。
 */
export type Session =
  | { mode: 'user'; user: AuthUser; remember: boolean; login_at: string }
  | { mode: 'guest'; login_at: string }
  | null

export interface AuthResult {
  ok: boolean
  message: string
}

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

/** 演示账号：登录页"用演示账号进入"会用到，省得现场手输 */
export const DEMO_USERNAME = 'demo'
export const DEMO_PASSWORD = 'demo1234'

/* ------------------------------ 存储读写 ------------------------------ */

function readJSON<T>(store: Storage, key: string, fallback: T): T {
  try {
    const raw = store.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    // 隐私模式 / 脏数据：当作没登录，不要让界面直接崩在白屏上
    return fallback
  }
}

function writeJSON(store: Storage, key: string, value: unknown): void {
  try {
    store.setItem(key, JSON.stringify(value))
  } catch {
    /* 存不下就算了：本地演示不该因为配额把页面卡死 */
  }
}

/* ------------------------------ 摘要与盐 ------------------------------ */

function toHex(bytes: Uint8Array): string {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

function randomSalt(): string {
  const bytes = new Uint8Array(8)
  if (globalThis.crypto?.getRandomValues) {
    globalThis.crypto.getRandomValues(bytes)
  } else {
    for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256)
  }
  return toHex(bytes)
}

/**
 * jsdom（单测环境）与部分老浏览器没有 crypto.subtle，退化成 FNV-1a。
 * 摘要算法可换不影响界面，但生产环境一定换成后端的 bcrypt/argon2。
 */
async function digest(salt: string, password: string): Promise<string> {
  const data = new TextEncoder().encode(`${salt}:${password}`)
  const subtle = globalThis.crypto?.subtle
  if (subtle) {
    const buf = await subtle.digest('SHA-256', data)
    return `sha256$${toHex(new Uint8Array(buf))}`
  }
  let h = 0x811c9dc5
  for (const byte of data) {
    h ^= byte
    h = Math.imul(h, 0x01000193) >>> 0
  }
  return `fnv1a$${h.toString(16)}`
}

function publicUser(u: StoredUser): AuthUser {
  return { username: u.username, created_at: u.created_at }
}

/* ------------------------------ 表单校验 ------------------------------ */

/** 用户名限制成"能安全出现在 URL/日志/侧栏"的字符集，避免花哨符号把布局撑坏 */
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
  // 不用数组下标取档位：noUncheckedIndexedAccess 下那样写要么加断言要么留 ??，都不如直白分支好读
  if (hits <= 1) return { score: 1, label: '弱' }
  if (hits === 2) return { score: 2, label: '中' }
  return { score: 3, label: '较强' }
}

function firstError(...messages: (string | null)[]): string | null {
  return messages.find((m) => m !== null) ?? null
}

/* ------------------------------ 状态 ------------------------------ */

const users = ref<StoredUser[]>(readJSON<StoredUser[]>(localStorage, USERS_KEY, []))

/** 先读"记住我"的 localStorage，再退回只活于当前标签页的 sessionStorage */
function readSession(): Session {
  const remembered = readJSON<Session>(localStorage, SESSION_KEY, null)
  return remembered ?? readJSON<Session>(sessionStorage, SESSION_ONCE_KEY, null)
}

/**
 * 写会话：remember=true 落 localStorage，否则落 sessionStorage（关标签页即退出）。
 * 访客态一律 sessionStorage——"随便逛逛"不该在下次打开时还占着登录位。
 */
function setSession(next: Session, remember = false): void {
  session.value = next
  try {
    localStorage.removeItem(SESSION_KEY)
    sessionStorage.removeItem(SESSION_ONCE_KEY)
    if (next === null) return
    if (remember && next.mode === 'user') {
      localStorage.setItem(SESSION_KEY, JSON.stringify(next))
    } else {
      sessionStorage.setItem(SESSION_ONCE_KEY, JSON.stringify(next))
    }
  } catch {
    /* 隐私模式存不下：会话只在内存里，刷新掉线而已，不影响当前这一屏 */
  }
}

const session = ref<Session>(readSession())

const currentUser = computed<AuthUser | null>(() =>
  session.value?.mode === 'user' ? session.value.user : null,
)

/** 是否已登录（真正的账号） */
const isLoggedIn = computed(() => session.value?.mode === 'user')

/** 是否以访客身份浏览 */
const isGuest = computed(() => session.value?.mode === 'guest')

/** 路由守卫用的放行条件：登录或访客都算"可以进主界面" */
const isAuthenticated = computed(() => session.value !== null)

/** 本地已注册账号数：登录页用来提示"这台机器上有几个号" */
const registeredCount = computed(() => users.value.length)

/* ------------------------------ 动作 ------------------------------ */

export async function register(input: RegisterInput): Promise<AuthResult> {
  const username = input.username.trim()
  const invalid = firstError(
    validateUsername(username),
    validatePassword(input.password),
    input.confirm === input.password ? null : '两次输入的密码不一致',
  )
  if (invalid) return { ok: false, message: invalid }

  const taken = users.value.some((u) => u.username.toLowerCase() === username.toLowerCase())
  if (taken) return { ok: false, message: `用户名 ${username} 已存在，换一个或直接登录` }

  const salt = randomSalt()
  const stored: StoredUser = {
    username,
    salt,
    hash: await digest(salt, input.password),
    created_at: new Date().toISOString(),
  }
  users.value = [...users.value, stored]
  writeJSON(localStorage, USERS_KEY, users.value)
  setSession(
    {
      mode: 'user',
      user: publicUser(stored),
      remember: input.remember,
      login_at: stored.created_at,
    },
    input.remember,
  )
  return { ok: true, message: `注册成功，欢迎 ${stored.username}` }
}

export async function login(input: LoginInput): Promise<AuthResult> {
  const username = input.username.trim()
  const invalid = firstError(validateUsername(username), input.password ? null : '请填写密码')
  if (invalid) return { ok: false, message: invalid }

  const found = users.value.find((u) => u.username.toLowerCase() === username.toLowerCase())
  if (!found) return { ok: false, message: `没有 ${username} 这个账号，先注册一个？` }

  if ((await digest(found.salt, input.password)) !== found.hash) {
    // 真实系统会把"用户不存在"和"密码错"并成一句模糊提示；
    // 本地演示更希望现场看得懂，所以这里分开说清楚。
    return { ok: false, message: '密码不正确' }
  }

  const now = new Date().toISOString()
  setSession(
    { mode: 'user', user: publicUser(found), remember: input.remember, login_at: now },
    input.remember,
  )
  return { ok: true, message: `欢迎回来，${found.username}` }
}

/** 访客模式：给"后端还没起、但想看一眼界面"的场合留的出口 */
export function enterAsGuest(): void {
  setSession({ mode: 'guest', login_at: new Date().toISOString() })
}

export function logout(): void {
  setSession(null)
}

/** 保证演示账号存在（幂等）：登录页挂载时调用一次 */
export async function ensureDemoUser(): Promise<void> {
  if (users.value.some((u) => u.username.toLowerCase() === DEMO_USERNAME)) return
  const salt = randomSalt()
  const stored: StoredUser = {
    username: DEMO_USERNAME,
    salt,
    hash: await digest(salt, DEMO_PASSWORD),
    created_at: new Date().toISOString(),
  }
  users.value = [...users.value, stored]
  writeJSON(localStorage, USERS_KEY, users.value)
}

export function useAuth() {
  return {
    currentUser,
    /** 只读导出，界面不许直接改会话 */
    session: readonly(session),
    isLoggedIn,
    isGuest,
    isAuthenticated,
    registeredCount,
    register,
    login,
    enterAsGuest,
    logout,
    ensureDemoUser,
  }
}
