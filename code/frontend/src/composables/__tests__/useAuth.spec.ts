/**
 * 注册 / 登录的前端逻辑测试（第 7 轮：真鉴权）。
 *
 * 这一层现在只做三件事：表单校验、把后端响应翻译成界面要的 { ok, message }、
 * 以及"身份存在哪里"（令牌 + 访客选择）。所以测试也按这三条写：
 * - 校验类：纯函数，直接断言；
 * - 动作类：mock 掉 ../api（不让测试打网络），断言令牌落到哪个 Storage、状态怎么变；
 * - 恢复类：bootstrap 的三种结局（有效 / 401 / 网络错误）——这是最容易做错的一段。
 *
 * 为什么要 vi.resetModules() + 动态 import：useAuth 的 user / bootstrapped 是模块级状态，
 * 不重置的话前一条用例的身份会漏进后一条，测出来的绿是假的。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

// oxlint 的 require-mock-type-parameters 要求写清 mock 的签名；
// 具体返回值由各用例的 mockResolvedValue / mockRejectedValue 决定，这里只声明形状
type MockCall = (...args: unknown[]) => Promise<unknown>

const apiMock = vi.hoisted(() => ({
  register: vi.fn<MockCall>(),
  login: vi.fn<MockCall>(),
  me: vi.fn<MockCall>(),
  logout: vi.fn<MockCall>(),
}))

vi.mock('../../api', () => ({ api: apiMock }))

const TOKEN_KEY = 'playerstock.auth.token.v1'
const GUEST_KEY = 'playerstock.auth.guest.v1'

const USER = {
  user_id: 7,
  nickname: 'lan_player',
  balance: 5000,
  initial_balance: 5000,
  created_at: '2026-11-07T08:00:00Z',
  account_type: 'private' as const,
}

const auth = () => import('../useAuth')

/** 每条用例都要一个干净的模块实例 + 干净的浏览器存储 */
async function fresh() {
  vi.resetModules()
  localStorage.clear()
  sessionStorage.clear()
  vi.clearAllMocks()
  return auth()
}

beforeEach(() => {
  localStorage.clear()
  sessionStorage.clear()
  vi.clearAllMocks()
})

describe('表单校验', () => {
  it('用户名：空 / 太短 / 非法字符都要拦，正常值放行', async () => {
    const { validateUsername } = await fresh()

    expect(validateUsername('')).toMatch(/请填写/)
    expect(validateUsername('ab')).toMatch(/至少 3/)
    expect(validateUsername('s1 mple')).toMatch(/字母、数字和下划线/)
    expect(validateUsername('s1mple')).toBeNull()
  })

  it('密码：长度与字母+数字两条规则', async () => {
    const { validatePassword } = await fresh()

    expect(validatePassword('a1')).toMatch(/至少 8/)
    expect(validatePassword('allletters')).toMatch(/字母和数字/)
    expect(validatePassword('demo1234')).toBeNull()
  })

  it('强度条只提示不拦截', async () => {
    const { passwordStrength } = await fresh()

    expect(passwordStrength('demo1234').score).toBe(2)
    expect(passwordStrength('demo1234!').score).toBe(3)
    expect(passwordStrength('').score).toBe(0)
  })
})

describe('注册', () => {
  it('成功后令牌落 localStorage（勾了记住我），身份变成私人账户', async () => {
    const m = await fresh()
    apiMock.register.mockResolvedValue({
      token: 'srv-token-1',
      expires_at: '2026-12-07T08:00:00Z',
      user: USER,
    })

    const res = await m.register({
      username: ' lan_player ',
      password: 'cs2go1234',
      confirm: 'cs2go1234',
      remember: true,
    })

    expect(res.ok).toBe(true)
    expect(apiMock.register).toHaveBeenCalledWith('lan_player', 'cs2go1234')
    expect(localStorage.getItem(TOKEN_KEY)).toBe('srv-token-1')
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(m.currentUser.value?.nickname).toBe('lan_player')
    expect(m.isLoggedIn.value).toBe(true)
    expect(m.isAuthenticated.value).toBe(true)
    expect(m.accountLabel.value).toBe('私人账户')
  })

  it('不勾记住我 → 令牌只进 sessionStorage', async () => {
    const m = await fresh()
    apiMock.register.mockResolvedValue({
      token: 'srv-token-2',
      expires_at: '2026-12-07T08:00:00Z',
      user: USER,
    })

    await m.register({
      username: 'lan_player',
      password: 'cs2go1234',
      confirm: 'cs2go1234',
      remember: false,
    })

    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(sessionStorage.getItem(TOKEN_KEY)).toBe('srv-token-2')
  })

  it('两次密码不一致时根本不发请求', async () => {
    const m = await fresh()

    const res = await m.register({
      username: 'lan_player',
      password: 'cs2go1234',
      confirm: 'cs2go1235',
      remember: true,
    })

    expect(res.ok).toBe(false)
    expect(res.message).toMatch(/不一致/)
    expect(apiMock.register).not.toHaveBeenCalled()
  })

  it('后端拒绝时把中文 message 原样透传（契约 §2：前端不写映射表）', async () => {
    const m = await fresh()
    apiMock.register.mockRejectedValue(new Error('用户名 lan_player 已被注册'))

    const res = await m.register({
      username: 'lan_player',
      password: 'cs2go1234',
      confirm: 'cs2go1234',
      remember: true,
    })

    expect(res.ok).toBe(false)
    expect(res.message).toBe('用户名 lan_player 已被注册')
    expect(m.isLoggedIn.value).toBe(false)
  })
})

describe('登录', () => {
  it('成功即建立身份', async () => {
    const m = await fresh()
    apiMock.login.mockResolvedValue({
      token: 'srv-token-3',
      expires_at: '2026-12-07T08:00:00Z',
      user: USER,
    })

    const res = await m.login({ username: 'lan_player', password: 'cs2go1234', remember: true })

    expect(res.ok).toBe(true)
    expect(m.currentUser.value?.user_id).toBe(7)
  })

  it('口令错：后端给什么提示就显示什么', async () => {
    const m = await fresh()
    apiMock.login.mockRejectedValue(new Error('用户名或密码不正确'))

    const res = await m.login({ username: 'lan_player', password: 'wrongpass1', remember: true })

    expect(res.ok).toBe(false)
    expect(res.message).toBe('用户名或密码不正确')
  })

  it('空密码不请求', async () => {
    const m = await fresh()

    const res = await m.login({ username: 'lan_player', password: '', remember: true })

    expect(res.message).toMatch(/请填写密码/)
    expect(apiMock.login).not.toHaveBeenCalled()
  })
})

describe('首屏恢复（bootstrap）', () => {
  it('令牌有效 → 身份恢复出来，守卫就不会把人弹回登录页', async () => {
    const m = await fresh()
    localStorage.setItem(TOKEN_KEY, 'srv-token-4')
    apiMock.me.mockResolvedValue({ authenticated: true, user: USER })

    await m.bootstrap()

    expect(apiMock.me).toHaveBeenCalledTimes(1)
    expect(m.isLoggedIn.value).toBe(true)
  })

  it('令牌 401 → 清掉令牌，身份回到未登录', async () => {
    const m = await fresh()
    const { ApiError } = await import('../../api/client')
    localStorage.setItem(TOKEN_KEY, 'dead-token')
    apiMock.me.mockRejectedValue(new ApiError('登录状态已失效，请重新登录', 'UNAUTHORIZED', 401))

    await m.bootstrap()

    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(m.isAuthenticated.value).toBe(false)
  })

  it('后端没起（网络错误）→ 保留令牌，不要一重启后端就全员掉线', async () => {
    const m = await fresh()
    const { ApiError } = await import('../../api/client')
    localStorage.setItem(TOKEN_KEY, 'srv-token-5')
    apiMock.me.mockRejectedValue(
      new ApiError('无法连接后端服务，请确认后端已启动后重试', 'NETWORK_ERROR', 0),
    )

    await m.bootstrap()

    expect(localStorage.getItem(TOKEN_KEY)).toBe('srv-token-5')
  })

  it('本地没有令牌时不打 /api/auth/me（省一次必然 401 的请求）', async () => {
    const m = await fresh()

    await m.bootstrap()

    expect(apiMock.me).not.toHaveBeenCalled()
  })
})

describe('访客与退出', () => {
  it('访客 = 不带令牌、不算登录，但守卫放行', async () => {
    const m = await fresh()

    m.enterAsGuest()

    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(m.isGuest.value).toBe(true)
    expect(m.isLoggedIn.value).toBe(false)
    expect(m.isAuthenticated.value).toBe(true)
    expect(m.accountLabel.value).toBe('公共演示账户')
    expect(sessionStorage.getItem(GUEST_KEY)).toBe('1')
  })

  it('退出会撤销服务端令牌并清干净本地', async () => {
    const m = await fresh()
    apiMock.register.mockResolvedValue({
      token: 'srv-token-6',
      expires_at: '2026-12-07T08:00:00Z',
      user: USER,
    })
    apiMock.logout.mockResolvedValue({ success: true, message: '已退出登录', revoked: true })
    await m.register({
      username: 'lan_player',
      password: 'cs2go1234',
      confirm: 'cs2go1234',
      remember: true,
    })

    await m.logout()

    expect(apiMock.logout).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(sessionStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(m.isAuthenticated.value).toBe(false)
    expect(m.currentUser.value).toBeNull()
  })

  it('后端撤销失败也照样清本地（退出不能把人留在登录态里）', async () => {
    const m = await fresh()
    apiMock.register.mockResolvedValue({
      token: 'srv-token-7',
      expires_at: '2026-12-07T08:00:00Z',
      user: USER,
    })
    apiMock.logout.mockRejectedValue(new Error('无法连接后端服务'))
    await m.register({
      username: 'lan_player',
      password: 'cs2go1234',
      confirm: 'cs2go1234',
      remember: true,
    })

    await m.logout()

    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(m.isAuthenticated.value).toBe(false)
  })

  it('访客态下退出 = 放弃访客身份，回到未登录', async () => {
    const m = await fresh()
    m.enterAsGuest()

    await m.logout()

    expect(m.isGuest.value).toBe(false)
    expect(m.isAuthenticated.value).toBe(false)
    expect(apiMock.logout).not.toHaveBeenCalled()
  })
})
