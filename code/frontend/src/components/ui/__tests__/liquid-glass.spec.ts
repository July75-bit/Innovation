/**
 * 液态玻璃材质层守卫测试（设计规范 → 可执行断言）。
 *
 * 目的：不让"玻璃"慢慢扩散到内容层，也不让降级路径被无意删掉。
 * 覆盖：
 *  1) 材质层组件确实挂了 .glass 类（弹窗 / 删除账号弹窗）；
 *  2) 令牌与降级规则仍在 CSS 里（backdrop-filter / reduced-transparency / no-backdrop-filter）；
 *  3) 玻璃圆角与内容层圆角是两套（20px 浮层 vs 4/6/8 内容）。
 */
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import UiModal from '../UiModal.vue'
import DeleteAccountDialog from '../../DeleteAccountDialog.vue'

const glassCss = readFileSync('src/assets/liquid-glass.css', 'utf8')
const tokensCss = readFileSync('src/assets/tokens.css', 'utf8')

describe('液态玻璃 · 材质层落点', () => {
  it('弹窗面板使用玻璃材质（glass + glass--panel）', () => {
    const wrapper = mount(UiModal, {
      props: { open: true, title: '确认删除账号？' },
      slots: { default: '内容' },
      global: { stubs: { Teleport: true } },
    })
    const panel = wrapper.find('.ui-modal')
    expect(panel.exists()).toBe(true)
    expect(panel.classes()).toContain('glass')
    expect(panel.classes()).toContain('glass--panel')
  })

  it('删除账号弹窗同样走玻璃材质', () => {
    const wrapper = mount(DeleteAccountDialog, {
      props: { modelValue: true, nickname: 'demo' },
      global: { stubs: { Teleport: true } },
    })
    const dialog = wrapper.find('.dialog')
    expect(dialog.exists()).toBe(true)
    expect(dialog.classes()).toContain('glass')
    expect(dialog.classes()).toContain('glass--panel')
  })
})

describe('液态玻璃 · 令牌与降级', () => {
  it('玻璃令牌齐全（模糊 / 饱和度 / scrim / 边框 / 回退实色 / 两套圆角）', () => {
    for (const token of [
      '--glass-blur',
      '--glass-saturate',
      '--glass-tint-nav',
      '--glass-tint-panel',
      '--glass-border',
      '--glass-highlight',
      '--glass-solid',
      '--glass-radius-control',
      '--glass-radius-panel',
    ]) {
      expect(glassCss, `缺少令牌 ${token}`).toContain(token)
    }
  })

  it('模糊半径在规格区间 18–28px，且窄屏仍不低于 18px', () => {
    expect(glassCss).toMatch(/--glass-blur:\s*22px/)
    expect(glassCss).toMatch(/--glass-blur:\s*18px/)
  })

  it('降级三条路径都在：@supports 回退、reduced-transparency、手动开关', () => {
    expect(glassCss).toContain('@supports not')
    expect(glassCss).toContain('prefers-reduced-transparency')
    expect(glassCss).toContain('no-backdrop-filter')
  })

  it('动态高光只在 hover/pointer:fine + 允许动效时启用，移动端自动关闭', () => {
    expect(glassCss).toMatch(/@media \(hover: hover\) and \(pointer: fine\)/)
    expect(glassCss).toContain('prefers-reduced-motion: no-preference')
  })

  it('内容层圆角仍是 4/6/8，材质层是 12/20/24 —— 两套不混用', () => {
    expect(tokensCss).toContain('--radius-xs: 4px')
    expect(tokensCss).toContain('--radius-sm: 6px')
    expect(tokensCss).toContain('--radius-md: 8px')
    expect(glassCss).toMatch(/--glass-radius-control:\s*12px/)
    expect(glassCss).toMatch(/--glass-radius-panel:\s*20px/)
    expect(glassCss).toMatch(/--glass-radius-sheet:\s*24px/)
  })
})
