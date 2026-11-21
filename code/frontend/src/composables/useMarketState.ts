/**
 * 市场页状态记忆：排序 / 筛选 / 搜索词 / 简报展开 / 滚动位置。
 *
 * 为什么不用 KeepAlive：列表页离开后组件会被卸载，KeepAlive 会增加一直挂着的页面与数据新鲜度问题；
 * 放到 sessionStorage（按标签页）更简单，也顺带解决「刷新后还在原状态」。
 *
 * 默认排序不是「列表顺序」而是**涨幅从高到低**：打开先看今天谁在动，比按 id 排更像行情页。
 */
const KEY = 'playerstock.market.v1'

export type MarketSort = 'change' | 'default' | 'price' | 'rating'
export type MarketStatus = 'all' | 'trading' | 'halted'

export interface MarketState {
  keyword: string
  status: MarketStatus
  sort: MarketSort
  briefOpen: boolean
  scrollY: number
}

export const MARKET_DEFAULTS: MarketState = {
  keyword: '',
  status: 'all',
  sort: 'change',
  briefOpen: false,
  scrollY: 0,
}

const SORTS: MarketSort[] = ['change', 'default', 'price', 'rating']
const STATUSES: MarketStatus[] = ['all', 'trading', 'halted']

function isSort(value: unknown): value is MarketSort {
  return typeof value === 'string' && (SORTS as string[]).includes(value)
}

function isStatus(value: unknown): value is MarketStatus {
  return typeof value === 'string' && (STATUSES as string[]).includes(value)
}

/** 读上次离开时的状态；坏数据/隐私模式一律退回默认值 */
export function readMarketState(): MarketState {
  try {
    const raw = sessionStorage.getItem(KEY)
    if (!raw) return { ...MARKET_DEFAULTS }
    const parsed = JSON.parse(raw) as Partial<MarketState>
    return {
      keyword: typeof parsed.keyword === 'string' ? parsed.keyword : MARKET_DEFAULTS.keyword,
      status: isStatus(parsed.status) ? parsed.status : MARKET_DEFAULTS.status,
      sort: isSort(parsed.sort) ? parsed.sort : MARKET_DEFAULTS.sort,
      briefOpen: parsed.briefOpen === true,
      scrollY: typeof parsed.scrollY === 'number' && parsed.scrollY > 0 ? parsed.scrollY : 0,
    }
  } catch {
    return { ...MARKET_DEFAULTS }
  }
}

/** 合并写入（只写变化的那几个字段） */
export function saveMarketState(patch: Partial<MarketState>): void {
  try {
    const current = readMarketState()
    sessionStorage.setItem(KEY, JSON.stringify({ ...current, ...patch }))
  } catch {
    /* 隐私模式存不下：只影响「回来时是否记得」，不影响当前操作 */
  }
}
