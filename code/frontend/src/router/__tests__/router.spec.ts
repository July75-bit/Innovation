/**
 * 路由表 + 登录守卫的回归测试。
 *
 * 由来一：第 5 天线上验收 TC-405 时发现，直接访问 `https://<前端>/market` 会**白屏**——
 * 市场页的正经路径是 `/`，而 `/market` 没有被任何路由匹配；静态站 rewrite 又把
 * `/market` 也返回 `index.html`，所以既没有 404、也没有页面，只剩头部，看起来像站点坏了。
 *
 * 由来二：加了 /auth 之后，"能不能进主界面"变成守卫说了算。
 * 这层最容易出的事故是**来回弹**（未登录 → /auth → 已登录 → / → 又踢回 /auth），
 * 所以每条路径都断言"最终落在哪"，而不是只断言匹配到了哪个路由。
 *
 * 由来三（第 7 轮）：守卫现在要先 `await bootstrap()` 拿后端确认身份。
 * 最阴的 bug 是"刷新后闪一下弹回登录页"——那是判断发生在恢复之前。
 * 所以这里专门有一条：localStorage 里有有效令牌时，直接访问 / 必须落在市场页。
 *
 * 注意：`router.resolve()` **不会跟随 redirect**，所以这里用真实导航（`router.push`）
 * 再断言 `currentRoute`，否则测不到"重定向到底生效没有"。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

// oxlint 的 require-mock-type-parameters 要求写清 mock 的签名；
// 这里用统一的"参数未知、返回 Promise"形状，具体值由各用例的 mockResolvedValue 决定
type MockCall = (...args: unknown[]) => Promise<unknown>

const apiMock = vi.hoisted(() => ({
  register: vi.fn<MockCall>(),
  login: vi.fn<MockCall>(),
  me: vi.fn<MockCall>(),
  logout: vi.fn<MockCall>(),
  deleteAccount: vi.fn<MockCall>(),
}))

vi.mock('../../api', () => ({ api: apiMock }))

import router from '../index'
import { enterAsGuest, logout } from '../../composables/useAuth'

const TOKEN_KEY = 'playerstock.auth.token.v1'
const PRIVATE_USER = {
  user_id: 7,
  nickname: 'lan_player',
  balance: 5000,
  initial_balance: 5000,
  created_at: '2026-11-07T08:00:00Z',
  account_type: 'private' as const,
}

/** 把"已登录"这件事做真：写令牌 + 让 /api/auth/me 认它 */
function signIn(token = 'guard-token') {
  localStorage.setItem(TOKEN_KEY, token)
  apiMock.me.mockResolvedValue({ authenticated: true, user: PRIVATE_USER })
}

beforeEach(async () => {
  localStorage.clear()
  sessionStorage.clear()
  vi.clearAllMocks()
  await logout()
})

describe('登录守卫', () => {
  it('未登录访问市场页 → 送去 /auth', async () => {
    await router.push('/')

    expect(router.currentRoute.value.name).toBe('auth')
  })

  it('未登录访问深层页 → /auth 带上 ?redirect=，登录后送回原页', async () => {
    await router.push('/positions')

    expect(router.currentRoute.value.path).toBe('/auth')
    expect(router.currentRoute.value.query.redirect).toBe('/positions')
  })

  it('本地有有效令牌时刷新，直接落在目标页（不闪回登录页）', async () => {
    signIn()

    await router.push('/trades')

    expect(router.currentRoute.value.name).toBe('trades')
    expect(apiMock.me).toHaveBeenCalledTimes(1)
  })

  it('令牌已被服务端撤销 → 清掉本地令牌并回登录页', async () => {
    const { ApiError } = await import('../../api/client')
    localStorage.setItem(TOKEN_KEY, 'dead-token')
    apiMock.me.mockRejectedValue(new ApiError('登录状态已失效，请重新登录', 'UNAUTHORIZED', 401))

    await router.push('/')

    expect(router.currentRoute.value.name).toBe('auth')
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('访客进入后可以正常浏览', async () => {
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('auth')

    enterAsGuest()
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('market')
  })

  it('已登录访问 /auth（不带 redirect）→ 回市场页，不在登录页打转', async () => {
    signIn()

    await router.push('/auth')

    expect(router.currentRoute.value.name).toBe('market')
  })

  it('退出登录后再访问主界面 → 又被送回 /auth', async () => {
    signIn()
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('market')

    apiMock.logout.mockResolvedValue({ success: true, message: '已退出登录', revoked: true })
    await logout()
    await router.push('/trades')

    expect(router.currentRoute.value.name).toBe('auth')
  })
})

describe('router 兜底', () => {
  beforeEach(() => {
    // 这一组测的是路由表本身，身份直接置为"访客可逛"，免得每条都被守卫拦去 /auth
    enterAsGuest()
  })

  it('市场页挂在 /', async () => {
    await router.push('/')

    expect(router.currentRoute.value.name).toBe('market')
  })

  it('/market 重定向到 /（不再白屏）', async () => {
    await router.push('/market')

    expect(router.currentRoute.value.path).toBe('/')
    expect(router.currentRoute.value.name).toBe('market')
  })

  it('未知路径也回市场页，而不是空白', async () => {
    await router.push('/no-such-page')

    expect(router.currentRoute.value.path).toBe('/')
    expect(router.currentRoute.value.name).toBe('market')
  })

  it('正常子路由不受影响', async () => {
    await router.push('/players/1')
    expect(router.currentRoute.value.name).toBe('player-detail')

    await router.push('/positions')
    expect(router.currentRoute.value.name).toBe('positions')

    await router.push('/trades')
    expect(router.currentRoute.value.name).toBe('trades')
  })

  it('/auth 是公开路由', async () => {
    await logout()

    await router.push('/auth')
    expect(router.currentRoute.value.name).toBe('auth')

    await router.push('/auth?tab=register')
    expect(router.currentRoute.value.query.tab).toBe('register')
  })
})
