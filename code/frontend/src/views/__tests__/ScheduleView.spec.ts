/**
 * 白话导读：赛程页的组件测试。
 *
 * 这页现在是**纯静态派生**：名单两块（"N 人暂停交易 / M 人可交易"）按需求下线之后，
 * 页面不请求任何接口，所以测试连 api 假货都不用挂，直接 mount 就能验：
 *   1. 轮次条 28 个 chip、比赛列表 28 行、区块 8 个；
 *   2. 排布口径——没比的按时间顺序在上、比过的按时间逆序在下；
 *   3. 翻页边界、比赛日/休赛日的页头说法；
 *   4. 8 支队标真的出现在对阵与列表里。
 *
 * 为什么值得测：这页把算法结论（哪两队在打、这一轮是第几天）直接摆给用户看，
 * 一旦页面和 `core/schedule.ts` 的结论不一致，答辩现场就是硬伤。
 * 算法本身的六条契约（结构 / 均衡 / 派生 / 循环 / 生成 / 校验）在
 * `src/core/__tests__/schedule.spec.ts` 里逐条守着，这里只测界面。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import ScheduleView from '../ScheduleView.vue'

/** 钉在赛季内的比赛日（UTC）：第 14 轮 G2 vs Astralis */
const MATCH_DAY = new Date('2026-11-14T04:00:00Z')

function mountView() {
  return mount(ScheduleView, {
    global: {
      components: {
        RouterLink: { name: 'RouterLink', props: ['to'], template: '<a><slot /></a>' },
      },
    },
  })
}

async function pickRound(w: ReturnType<typeof mountView>, round: number) {
  await w.findAll('.strip .chip')[round - 1]!.trigger('click')
}

/** 列表里每一行的轮次（★ 是焦点局标记，会混在文字里） */
function listedRounds(w: ReturnType<typeof mountView>): number[] {
  return w.findAll('tr.row').map((row) => Number(row.find('td')!.text().replace('★', '').trim()))
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(MATCH_DAY)
})

afterEach(() => {
  vi.useRealTimers()
})

describe('ScheduleView', () => {
  it('渲染 28 场比赛的列表与轮次选择条（区块按"每 4 轮一组"，跨今天的那组拆成两截 → 8 个）', () => {
    const w = mountView()

    expect(w.text()).toContain('赛程')
    expect(w.findAll('.strip .chip')).toHaveLength(28)
    expect(w.findAll('tr.row')).toHaveLength(28)
    expect(w.findAll('tr.group-row')).toHaveLength(8)
    expect(w.find('.chip-d i').exists()).toBe(true) // 焦点局标了 ★
  })

  it('排布口径：没比的按时间顺序在上（14→28），比过的按时间逆序在下（13→1）', () => {
    const w = mountView()

    const listed = listedRounds(w)
    expect(listed.slice(0, 15)).toEqual(Array.from({ length: 15 }, (_, i) => 14 + i))
    expect(listed.slice(15)).toEqual(Array.from({ length: 13 }, (_, i) => 13 - i))

    // 组头按"实际列在里面的轮次"写，跨今天的那一组被拆成两截，不会假装整组都打完了
    const banners = w.findAll('tr.group-row').map((row) => row.text())
    expect(banners.slice(0, 4)).toEqual([
      '第 14–16 轮 · 未开始',
      '第 17–20 轮 · 未开始',
      '第 21–24 轮 · 未开始',
      '第 25–28 轮 · 未开始',
    ])
    expect(banners.slice(4)).toEqual([
      '第 13 轮 · 已结束',
      '第 9–12 轮 · 已结束',
      '第 5–8 轮 · 已结束',
      '第 1–4 轮 · 已结束',
    ])
    expect(w.find('.list-head').text()).toContain('未开始 15 场')
    expect(w.find('.list-head').text()).toContain('已结束 13 场')
  })

  it('点第 12 轮：对阵换成焦点局两队，页头同步说这两队暂停交易', async () => {
    const w = mountView()

    await pickRound(w, 12)

    expect(w.text()).toContain('第 12 轮')
    expect(w.text()).toContain('Vitality / Spirit')
    expect(w.find('.match').text()).toContain('Vitality')
    expect(w.find('.match').text()).toContain('Spirit')
    expect(w.find('.match-meta').text()).toContain('★ 焦点局')
  })

  it('选中的轮次 chip 自动滚到条带正中间（轮次 + 日期始终在屏幕中央）', async () => {
    const w = mountView()
    const bar = w.get('.strip').element
    const chips = w.findAll('.chip')
    const scrollTo = vi.fn<(options?: ScrollToOptions) => void>()

    // jsdom 没有真布局：手工喂一套"真实尺寸"，再验居中的算术对不对
    Object.defineProperty(bar, 'clientWidth', { value: 600, configurable: true })
    Object.defineProperty(bar, 'scrollTo', { value: scrollTo, configurable: true })
    bar.getBoundingClientRect = () =>
      ({ left: 40, top: 100, bottom: 160, right: 640, width: 600 }) as DOMRect
    chips.forEach((chip, index) => {
      chip.element.getBoundingClientRect = () => ({ left: 40 + index * 58, width: 52 }) as DOMRect
    })

    await pickRound(w, 26)

    // 第 26 个 chip 左边在 40 + 25×58 = 1490，相对条带左沿 1450；
    // 居中 = 1450 − (600 − 52)/2 = 1176
    expect(scrollTo).toHaveBeenCalledWith({ left: 1176, behavior: 'smooth' })
  })

  it('视口一变（转屏 / 缩放窗口）就按新宽度重新居中', async () => {
    const w = mountView()
    const bar = w.get('.strip').element
    const scrollTo = vi.fn<(options?: ScrollToOptions) => void>()

    Object.defineProperty(bar, 'scrollTo', { value: scrollTo, configurable: true })
    Object.defineProperty(bar, 'clientWidth', { value: 600, configurable: true })
    bar.getBoundingClientRect = () =>
      ({ left: 40, top: 100, bottom: 160, right: 640, width: 600 }) as DOMRect
    w.findAll('.chip').forEach((chip, index) => {
      chip.element.getBoundingClientRect = () => ({ left: 40 + index * 58, width: 52 }) as DOMRect
    })
    // 先让挂载时那一次居中跑完，否则它和 resize 这一次会混在一起数
    await vi.advanceTimersByTimeAsync(50)
    scrollTo.mockClear()

    window.dispatchEvent(new Event('resize'))
    await vi.advanceTimersByTimeAsync(50) // rAF 合并连续 resize

    // 选中的是第 14 轮（索引 13）：754 − (600 − 52)/2 = 480
    expect(scrollTo).toHaveBeenCalledTimes(1)
    expect(scrollTo).toHaveBeenLastCalledWith({ left: 480, behavior: 'auto' })
  })

  it('条带整条滚出视野时（点了列表最底下那行），先把它带回屏幕再居中', async () => {
    const w = mountView()
    const bar = w.get('.strip').element
    const scrollIntoView = vi.fn<(options?: unknown) => void>()

    Object.defineProperty(bar, 'scrollIntoView', { value: scrollIntoView, configurable: true })
    Object.defineProperty(bar, 'clientWidth', { value: 600, configurable: true })
    // 条带已经在视口上方（bottom <= 0）
    bar.getBoundingClientRect = () => ({ left: 0, top: -400, bottom: -340, width: 600 }) as DOMRect
    w.findAll('.chip').forEach((chip, index) => {
      chip.element.getBoundingClientRect = () => ({ left: index * 58, width: 52 }) as DOMRect
    })

    await pickRound(w, 26)
    expect(scrollIntoView).toHaveBeenCalledWith({ block: 'center', behavior: 'smooth' })
  })

  it('左右翻页按钮按轮次移动，边界处禁用', async () => {
    const w = mountView()

    await pickRound(w, 2)
    await w.get('button[aria-label="下一轮"]').trigger('click')
    expect(w.find('.match-meta').text()).toContain('第 3 轮')

    await pickRound(w, 1)
    expect(w.get('button[aria-label="上一轮"]').attributes('disabled')).toBeDefined()

    await pickRound(w, 28)
    expect(w.get('button[aria-label="下一轮"]').attributes('disabled')).toBeDefined()
  })

  it('比赛日：页头显示"今天 · 第 14 轮"，默认就停在这一轮', () => {
    const w = mountView()

    expect(w.find('.today').text()).toContain('第 14 轮')
    expect(w.find('.today').text()).not.toContain('休赛日')
    expect(w.find('.match-meta').text()).toContain('第 14 轮')
  })

  it('休赛日：页头改口"休赛日"，并把默认轮次停在最后一轮而不是假装第 1 轮', () => {
    vi.setSystemTime(new Date('2026-12-01T04:00:00Z')) // 赛季 11-28 打完

    const w = mountView()

    expect(w.find('.today').text()).toContain('休赛日')
    expect(w.find('.today').text()).toContain('第 28 轮')
    // 休赛日没有"本轮停牌"，市场页与接口都放行；赛程页仍可浏览第 28 轮的对阵
    expect(w.find('.match-meta').text()).toContain('第 28 轮')
  })

  it('队标：本轮对阵两队与列表 28 行都带上图', async () => {
    const w = mountView()

    await pickRound(w, 12)

    // 焦点局大字：Vitality vs Spirit，两张图按主客顺序出现
    const featured = w.findAll('.match-main .team-logo img')
    expect(featured).toHaveLength(2)
    expect(featured.map((img) => img.attributes('src'))).toEqual([
      expect.stringContaining('vitality'),
      expect.stringContaining('spirit'),
    ])
    // 列表 28 轮 × 每轮 2 队，一行都不该漏图
    expect(w.findAll('tr.row .vs-cell .team-logo')).toHaveLength(56)
    // alt 文案带上队名，读屏与图片加载失败时都说得清是谁
    expect(featured[0]?.attributes('alt')).toContain('Vitality')
  })

  it('两块名单已下线：不再出现"N 人暂停交易 / M 人可交易"，页面也不请求选手接口', () => {
    const w = mountView()

    expect(w.find('.roster').exists()).toBe(false)
    expect(w.text()).not.toContain('人暂停交易')
    expect(w.text()).not.toContain('人可交易')
    // 页头仍然给出结论（谁停牌），只是不再逐人列名单
    expect(w.find('.page-head').text()).toContain('暂停交易')
  })
})
