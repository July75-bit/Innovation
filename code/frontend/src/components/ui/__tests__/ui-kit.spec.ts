/**
 * UI 组件库状态测试（与设计规范一一对应）。
 *
 * 覆盖：按钮禁用/加载不触发点击、变体类名；输入框 label 关联与错误 aria；
 * 下拉选项与变更事件；标签色调；分页当前页与事件；弹窗 Esc 关闭；表格空/加载/排序。
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import UiButton from '../UiButton.vue'
import UiCard from '../UiCard.vue'
import UiInput from '../UiInput.vue'
import UiModal from '../UiModal.vue'
import UiNavItem from '../UiNavItem.vue'
import UiPagination from '../UiPagination.vue'
import UiSelect from '../UiSelect.vue'
import UiTable from '../UiTable.vue'
import UiTag from '../UiTag.vue'

describe('UiButton', () => {
  it('禁用时点击不发出事件', async () => {
    const wrapper = mount(UiButton, { props: { disabled: true }, slots: { default: '买入' } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('加载中：显示转圈、禁用、aria-busy', () => {
    const wrapper = mount(UiButton, { props: { loading: true }, slots: { default: '提交中' } })
    expect(wrapper.find('.ui-btn__spinner').exists()).toBe(true)
    expect(wrapper.attributes('aria-busy')).toBe('true')
    expect(wrapper.attributes('disabled')).toBeDefined()
  })

  it('变体与尺寸映射到正确的类名', () => {
    const wrapper = mount(UiButton, { props: { variant: 'primary', size: 'lg' } })
    expect(wrapper.classes()).toContain('ui-btn--primary')
    expect(wrapper.classes()).toContain('ui-btn--lg')
  })
})

describe('UiInput', () => {
  it('label 与输入框通过 for/id 关联，错误时 aria-invalid + 描述', () => {
    const wrapper = mount(UiInput, {
      props: { modelValue: 'abc', label: '数量', error: '必须是正整数' },
    })
    const input = wrapper.find('input')
    const label = wrapper.find('label')
    expect(label.attributes('for')).toBe(input.attributes('id'))
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(wrapper.text()).toContain('必须是正整数')
    expect(wrapper.find('.ui-error').exists()).toBe(true)
  })

  it('输入时发出 update:modelValue', async () => {
    const wrapper = mount(UiInput, { props: { modelValue: '', label: '数量' } })
    await wrapper.find('input').setValue('3')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['3'])
  })
})

describe('UiSelect', () => {
  it('渲染全部选项并在选择后发事件', async () => {
    const wrapper = mount(UiSelect, {
      props: {
        modelValue: 'a',
        label: '位置',
        options: [
          { label: '狙击手', value: 'a' },
          { label: '步枪手', value: 'b' },
        ],
      },
    })
    expect(wrapper.findAll('option')).toHaveLength(2)
    await wrapper.find('select').setValue('b')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['b'])
  })
})

describe('UiTag', () => {
  it('按 tone 输出语义类名', () => {
    const wrapper = mount(UiTag, { props: { tone: 'error' }, slots: { default: '余额不足' } })
    expect(wrapper.classes()).toContain('ui-badge--error')
    expect(wrapper.text()).toBe('余额不足')
  })
})

describe('UiPagination', () => {
  it('高亮当前页并发出翻页事件', async () => {
    const wrapper = mount(UiPagination, { props: { page: 3, pageSize: 10, total: 96 } })
    expect(wrapper.find('.is-current').text()).toBe('3')
    await wrapper.findAll('button')[0]!.trigger('click') // 上一页
    expect(wrapper.emitted('update:page')?.[0]).toEqual([2])
  })

  it('第一页时上一页禁用', () => {
    const wrapper = mount(UiPagination, { props: { page: 1, pageSize: 10, total: 96 } })
    expect(wrapper.findAll('button')[0]!.attributes('disabled')).toBeDefined()
  })
})

describe('UiModal', () => {
  it('打开渲染标题，Esc 关闭', async () => {
    const wrapper = mount(UiModal, {
      props: { open: true, title: '确认删除账号？', dismissible: true },
      slots: { default: '内容' },
      attachTo: document.body,
    })
    expect(document.body.textContent).toContain('确认删除账号？')
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    expect(wrapper.emitted('update:open')?.[0]).toEqual([false])
    wrapper.unmount()
  })
})

describe('UiTable', () => {
  const columns = [
    { key: 'name', label: '选手', sortable: true },
    { key: 'price', label: '现价', align: 'right' as const },
  ]

  it('空数据展示空态文案', () => {
    const wrapper = mount(UiTable, {
      props: { columns, rows: [], emptyText: '还没有数据' },
    })
    expect(wrapper.text()).toContain('还没有数据')
  })

  it('加载态渲染骨架行', () => {
    const wrapper = mount(UiTable, { props: { columns, rows: [], loading: true } })
    expect(wrapper.findAll('.is-skeleton')).toHaveLength(5)
  })

  it('点击可排序表头发送排序事件', async () => {
    const wrapper = mount(UiTable, {
      props: { columns, rows: [{ id: 1, name: 'ZywOo', price: '89.13' }] },
    })
    await wrapper.find('.ui-table__sort').trigger('click')
    expect(wrapper.emitted('sort')?.[0]).toEqual([{ key: 'name', dir: 'asc' }])
  })
})

describe('UiNavItem', () => {
  it('选中态带 aria-current 与主色指示类', () => {
    const wrapper = mount(UiNavItem, { props: { href: '#market', active: true } })
    expect(wrapper.attributes('aria-current')).toBe('page')
    expect(wrapper.classes()).toContain('is-active')
  })
})

describe('UiCard', () => {
  it('可点击卡片渲染为 button 并带交互类', () => {
    const wrapper = mount(UiCard, { props: { title: 'ZywOo', interactive: true } })
    expect(wrapper.element.tagName).toBe('BUTTON')
    expect(wrapper.classes()).toContain('ui-card--interactive')
  })
})
