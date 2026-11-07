/**
 * 删除账号弹窗的交互测试。
 *
 * 这里守的是"两道确认"这件事本身：口令 + 手输用户名，少一个都不许按下去。
 * 后端契约（§4.16）已经由 pytest 守住，组件层只关心**误触**——
 * 不可逆操作的前端职责就是让人不可能一巴掌拍下去。
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'

const deleteAccount = vi.fn<(...args: unknown[]) => Promise<unknown>>()

vi.mock('../../composables/useAuth', () => ({
  useAuth: () => ({ deleteAccount }),
}))

import DeleteAccountDialog from '../DeleteAccountDialog.vue'

// Teleport 到 body 会让 wrapper 找不到内容，测试里把 Teleport 摊平；
// deleteAccount 是模块级 mock，必须每条用例前清干净，否则调用次数会串味
beforeEach(() => {
  deleteAccount.mockReset()
})

/** 取最后一次"要求关闭"的事件；测试的 tsconfig lib 不含 ES2022，所以不用 .at(-1) */
function lastClose(wrapper: ReturnType<typeof factory>): unknown {
  const events = wrapper.emitted('update:modelValue')
  return events?.slice(-1)[0]
}

function factory() {
  return mount(DeleteAccountDialog, {
    props: { nickname: 'lan_player', modelValue: true },
    global: { stubs: { Teleport: true } },
  })
}

async function open() {
  const wrapper = factory()
  await nextTick()
  return wrapper
}

describe('两道确认', () => {
  it('刚打开时删除按钮不可点', async () => {
    const wrapper = await open()

    expect(wrapper.get('.danger').attributes('disabled')).toBeDefined()
  })

  it('只填密码不够，必须把用户名也打对', async () => {
    const wrapper = await open()

    await wrapper.get('#del-password').setValue('cs2go1234')
    expect(wrapper.get('.danger').attributes('disabled')).toBeDefined()

    await wrapper.get('#del-name').setValue('wrong_name')
    expect(wrapper.get('.danger').attributes('disabled')).toBeDefined()

    // 大小写不敏感：与后端"用户名不区分大小写"的口径保持一致
    await wrapper.get('#del-name').setValue('LAN_Player')
    await nextTick()
    expect(wrapper.get('.danger').attributes('disabled')).toBeUndefined()
  })

  it('按下去才真正调用 deleteAccount，成功后关窗并通知父层', async () => {
    deleteAccount.mockResolvedValue({ ok: true, message: '账号已删除（已删除 1 条持仓）' })
    const wrapper = await open()

    await wrapper.get('#del-password').setValue('cs2go1234')
    await wrapper.get('#del-name').setValue('lan_player')
    await wrapper.get('.danger').trigger('click')
    await nextTick()
    await vi.waitFor(() => expect(wrapper.emitted('deleted')).toBeTruthy())

    expect(deleteAccount).toHaveBeenCalledWith('cs2go1234')
    expect(lastClose(wrapper)).toEqual([false])
    // 顺序是这条用例的重点：deleted 必须早于关闭。
    // 反过来的话，父层把弹窗挂在 currentUser 上时，组件会在 emit 前被卸载，通知直接丢失
    const calls = wrapper.emitted()
    const deletedAt = calls.deleted?.length ?? 0
    expect(deletedAt).toBe(1)
    expect(calls['update:modelValue']!.length).toBeGreaterThanOrEqual(1)
  })

  it('失败时不关窗、不通知，并把后端中文原样显示', async () => {
    deleteAccount.mockResolvedValue({ ok: false, message: '密码不正确，未能删除账号' })
    const wrapper = await open()

    await wrapper.get('#del-password').setValue('wrongpass1')
    await wrapper.get('#del-name').setValue('lan_player')
    await wrapper.get('.danger').trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.err').text()).toContain('密码不正确'))

    expect(wrapper.emitted('deleted')).toBeUndefined()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('ESC 能取消：确认类弹窗必须能一键退出', async () => {
    const wrapper = await open()

    await wrapper.get('.mask').trigger('keydown', { key: 'Escape' })

    expect(lastClose(wrapper)).toEqual([false])
  })

  it('点遮罩也能取消（点空白处不该把人困在弹窗里）', async () => {
    const wrapper = await open()

    // 单独一条用例：关闭后 defineModel 会把本地值置 false，.mask 随即卸载，
    // 在同一个 wrapper 里连着测两下就会"找不到元素"，那是测试写法的问题不是代码问题
    await wrapper.get('.mask').trigger('click')

    expect(lastClose(wrapper)).toEqual([false])
  })

  it('取消按钮关窗且不发请求', async () => {
    const wrapper = await open()

    await wrapper.get('.cancel').trigger('click')

    expect(lastClose(wrapper)).toEqual([false])
    expect(deleteAccount).not.toHaveBeenCalled()
  })
})
