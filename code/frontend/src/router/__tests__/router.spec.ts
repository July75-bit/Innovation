/**
 * 路由表的回归测试。
 *
 * 由来：第 5 天线上验收 TC-405 时发现，直接访问 `https://<前端>/market` 会**白屏**——
 * 市场页的正经路径是 `/`，而 `/market` 没有被任何路由匹配；静态站 rewrite 又把
 * `/market` 也返回 `index.html`，所以既没有 404、也没有页面，只剩头部，看起来像站点坏了。
 *
 * 注意：`router.resolve()` **不会跟随 redirect**，所以这里用真实导航（`router.push`）
 * 再断言 `currentRoute`，否则测不到"重定向到底生效没有"。
 */
import { describe, expect, it } from 'vitest'

import router from '../index'

describe('router 兜底', () => {
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
})
