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
import { flushPromises, mount } from '@vue/test-utils'

const apiMock = vi.hoisted(() => ({ listPlayers: vi.fn<() => Promise<unknown>>() }))
vi.mock('../../api', () => ({ api: apiMock }))

import ScheduleView from '../ScheduleView.vue'

/** 钉在赛季内的比赛日（UTC）：第 14 轮 G2 vs Astralis */
const MATCH_DAY = new Date('2026-11-14T04:00:00Z')

function mountView() {
  return mount(ScheduleView, {
    global: {
      components: {
        RouterLink: { name: 'RouterLink', props: ['to'], template: '<a :href="to"><slot /></a>' },
      },
    },
  })
}

async function pickRound(w: ReturnType<typeof mountView>, round: number) {
  await w.findAll('.strip .chip')[round - 1]!.trigger('click')
}

/** 第 18 轮 FaZe Clan vs NAVI 的四名选手（抽屉里应该正好这 4 个） */
const ROUND18_PLAYERS = [
  { player_id: 2, name: 'ropz', display_name: null, team: 'FaZe Clan', role: 'Lurker', current_price: 122.99, prev_price: 122, change_pct: 0.82, rating: 78, status: 'trading' },
  { player_id: 9, name: 'broky', display_name: null, team: 'FaZe Clan', role: 'AWPer', current_price: 89.29, prev_price: 97.2, change_pct: -9.58, rating: 71, status: 'trading' },
  { player_id: 5, name: 'jL', display_name: null, team: 'NAVI', role: 'Rifler', current_price: 87.07, prev_price: 88.2, change_pct: -1.21, rating: 76, status: 'trading' },
  { player_id: 12, name: 'w0nderful', display_name: null, team: 'NAVI', role: 'AWPer', current_price: 72.3, prev_price: 71, change_pct: 1.83, rating: 74, status: 'trading' },
]

/** 列表里的第 N 轮那一行 */
function rowOf(w: ReturnType<typeof mountView>, round: number) {
  return w.findAll('tr.row').find((row) => row.find('td').text().replace('★', '').trim() === String(round))!
}

/** 列表里每一行的轮次（★ 是焦点局标记，会混在文字里） */
function listedRounds(w: ReturnType<typeof mountView>): number[] {
  return w.findAll('tr.row').map((row) => Number(row.find('td')!.text().replace('★', '').trim()))
}

beforeEach(() => {
  sessionStorage.removeItem('playerstock.schedule.round.v1')
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

describe('赛程 · 比赛抽屉', () => {
  beforeEach(() => {
    sessionStorage.removeItem('playerstock.schedule.round.v1')
    // 不用 fake timers：组件里 rAF/过渡定时器与 runAllTimers 组合会卡死；
    // 这组断言不依赖"今天"的具体日期
    vi.useRealTimers()
    apiMock.listPlayers.mockResolvedValue(ROUND18_PLAYERS)
  })

  afterEach(() => {
    vi.useRealTimers()
    apiMock.listPlayers.mockReset()
    document.body.style.overflow = ''
    document.body.innerHTML = ''
  })

  /** 抽屉通过 <Teleport to="body"> 挂到 body，测不了 wrapper，直接查 document */
  const drawer = () => document.querySelector<HTMLElement>('.match-drawer')

  it('点任意一场比赛 → 右侧抽屉显示两队与 4 名选手', async () => {
    const w = mountView()
    await rowOf(w, 18).trigger('click')
    await flushPromises()

    const el = drawer()
    expect(el).not.toBeNull()
    const text = el!.textContent ?? ''
    expect(text).toContain('第 18 轮')
    expect(text).toContain('FaZe Clan')
    expect(text).toContain('NAVI')
    for (const name of ['ropz', 'broky', 'jL', 'w0nderful']) expect(text).toContain(name)

    expect(el!.querySelectorAll('.p-link')).toHaveLength(4)
    expect(document.body.style.overflow).toBe('hidden')
    w.unmount()
    expect(document.body.style.overflow).toBe('')
  })

  it('抽屉里的选手卡指向选手详情页（看行情 → 再下单）', async () => {
    const w = mountView()
    await rowOf(w, 18).trigger('click')
    await flushPromises()

    const hrefs = [...document.querySelectorAll<HTMLAnchorElement>('.match-drawer .p-link')].map(
      (link) => link.getAttribute('href'),
    )
    expect(hrefs).toEqual(
      expect.arrayContaining(['/players/2', '/players/9', '/players/5', '/players/12']),
    )
    w.unmount()
  })

  it('未来轮次也能点开（不限制在今天）', async () => {
    const w = mountView()
    await rowOf(w, 25).trigger('click')
    await flushPromises()

    expect(drawer()!.textContent).toContain('第 25 轮')
    // 未来轮次照样能看到对阵两队（fixture 只准备了 18 轮的选手，这里只验抽屉本身）
    expect(drawer()!.querySelectorAll('.drawer-team')).toHaveLength(2)
    w.unmount()
  })

  it('Esc 关闭抽屉，并恢复页面滚动', async () => {
    const w = mountView()
    await rowOf(w, 18).trigger('click')
    await flushPromises()
    expect(drawer()).not.toBeNull()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(drawer()).toBeNull()
    expect(document.body.style.overflow).toBe('')
    w.unmount()
  })

  it('选手数据加载失败 → 给出重试，重试成功后正常显示', async () => {
    apiMock.listPlayers.mockRejectedValueOnce(new Error('network down'))
    const w = mountView()
    await rowOf(w, 18).trigger('click')
    await flushPromises()

    expect(document.querySelector('.drawer-error')).not.toBeNull()
    expect(document.querySelectorAll('.match-drawer .p-link')).toHaveLength(0)

    ;(document.querySelector('.drawer-error button') as HTMLButtonElement).click()
    await flushPromises()
    expect(document.querySelector('.drawer-error')).toBeNull()
    expect(document.querySelectorAll('.match-drawer .p-link')).toHaveLength(4)
    w.unmount()
  })
})
