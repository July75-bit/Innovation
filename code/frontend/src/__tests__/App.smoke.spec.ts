/**
 * 外壳冒烟测试（回归守卫）。
 *
 * 背景：2026-11-14 给 App.vue 加"桌面玻璃顶栏"时，把 `watch(..., {immediate:true})`
 * 放在了 `const route = useRoute()` 之前，setup 阶段直接 TDZ 报错 → 整站白屏。
 * build / lint / 普通单测都发现不了（没人 mount 过 App），所以留这条冒烟用例。
 */
import { mount } from '@vue/test-utils'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import App from '../App.vue'
import router from '../router'

beforeAll(async () => {
  // 外壳会拉账户/健康检查；这里给一个最小 fetch 假实现，避免真实网络
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ balance: 5000, total_asset: 5000, initial_balance: 5000 }),
      text: async () => '{}',
    })),
  )
  try {
    sessionStorage.setItem('playerstock.auth.guest.v1', '1')
  } catch {
    /* jsdom 里可用 */
  }
  // /ui-kit 是 public 路由：不依赖登录态，能进外壳（/ 会被守卫拦去 /auth）
  await router.push('/ui-kit')
  await router.isReady()
})

describe('App 外壳', () => {
  it('能正常挂载并渲染侧栏 / 玻璃顶栏 / 内容出口（曾经 setup 报 TDZ 导致白屏）', async () => {
    const wrapper = mount(App, {
      global: { plugins: [router], stubs: { RouterView: true } },
    })
    expect(wrapper.find('.shell').exists()).toBe(true)
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.topbar').exists()).toBe(true)
    expect(wrapper.find('.topbar').classes()).toContain('glass')
    expect(wrapper.find('.content').exists()).toBe(true)
    wrapper.unmount()
  })
})
