/**
 * 路由表 + 登录守卫的回归测试。
 *
 * 由来一：第 5 天线上验收 TC-405 时发现，直接访问 `https://<前端>/market` 会**白屏**——
 * 市场页的正经路径是 `/`，而 `/market` 没有被任何路由匹配；静态站 rewrite 又把
 * `/market` 也返回 `index.html`，所以既没有 404、也没有页面，只剩头部，看起来像站点坏了。
 *
 * 由来二：加了 /auth 之后，"未登录能不能进主界面"变成守卫说了算。
 * 这层最容易出的事故是**来回弹**（未登录 → /auth → 已登录 → / → 又踢回 /auth），
 * 所以每条路径都断言"最终落在哪"，而不是只断言匹配到了哪个路由。
 *
 * 注意：`router.resolve()` **不会跟随 redirect**，所以这里用真实导航（`router.push`）
 * 再断言 `currentRoute`，否则测不到"重定向到底生效没有"。
 */
import { beforeEach, describe, expect, it } from 'vitest'

import router from '../index'
import { enterAsGuest, login, logout, register } from '../../composables/useAuth'

describe('登录守卫', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
    logout()
  })

  it('未登录访问市场页 → 送去 /auth', async () => {
    await router.push('/')

    expect(router.currentRoute.value.name).toBe('auth')
  })

  it('未登录访问深层页 → /auth 带上 ?redirect=，登录后送回原页', async () => {
    await router.push('/positions')

    expect(router.currentRoute.value.path).toBe('/auth')
    expect(router.currentRoute.value.query.redirect).toBe('/positions')
  })

  it('访客进入后可以正常浏览', async () => {
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('auth')

    enterAsGuest()
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('market')
  })

  it('已登录用户访问 /auth（不带 redirect）→ 回市场页，不在登录页打转', async () => {
    await register({
      username: 'guard_user',
      password: 'abcd1234',
      confirm: 'abcd1234',
      remember: true,
    })

    await router.push('/auth')
    expect(router.currentRoute.value.name).toBe('market')
  })

  it('退出登录后再访问主界面 → 又被送回 /auth', async () => {
    await register({
      username: 'guard_user2',
      password: 'abcd1234',
      confirm: 'abcd1234',
      remember: true,
    })
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('market')

    logout()
    await router.push('/trades')
    expect(router.currentRoute.value.name).toBe('auth')
  })

  it('登录成功 = 会话写进 storage，刷新后守卫仍然放行', async () => {
    await register({
      username: 'persist_user',
      password: 'abcd1234',
      confirm: 'abcd1234',
      remember: true,
    })
    logout()
    expect(localStorage.getItem('playerstock.auth.session.v1')).toBeNull()

    await login({ username: 'persist_user', password: 'abcd1234', remember: true })
    expect(localStorage.getItem('playerstock.auth.session.v1')).not.toBeNull()

    await router.push('/players/7')
    expect(router.currentRoute.value.name).toBe('player-detail')
  })
})

describe('router 兜底', () => {
  beforeEach(() => {
    // 这一组测的是路由表本身，登录态直接置为"访客可逛"，免得每条都被守卫拦去 /auth
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
    logout()

    await router.push('/auth')
    expect(router.currentRoute.value.name).toBe('auth')

    await router.push('/auth?tab=register')
    expect(router.currentRoute.value.query.tab).toBe('register')
  })
})
