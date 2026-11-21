import { describe, expect, it } from 'vitest'
import { nearestTabIndex, pathForTabIndex, tabIndexForPath, TAB_PATHS } from '../tabPager'

describe('tabPager 索引换算', () => {
  it('四个主页面路径与索引一一对应', () => {
    expect(TAB_PATHS.market).toBe('/')
    expect(tabIndexForPath('/')).toBe(0)
    expect(tabIndexForPath('/schedule')).toBe(1)
    expect(tabIndexForPath('/positions')).toBe(2)
    expect(tabIndexForPath('/trades')).toBe(3)
  })

  it('非主页面返回 -1', () => {
    expect(tabIndexForPath('/players/1')).toBe(-1)
    expect(tabIndexForPath('/me')).toBe(-1)
    expect(tabIndexForPath('/auth')).toBe(-1)
  })

  it('索引与路径可互相换算，越界返回 null', () => {
    expect(pathForTabIndex(0)).toBe('/')
    expect(pathForTabIndex(3)).toBe('/trades')
    expect(pathForTabIndex(-1)).toBeNull()
    expect(pathForTabIndex(4)).toBeNull()
  })

  it('滚动位置四舍五入到最近一页', () => {
    expect(nearestTabIndex(0, 390)).toBe(0)
    expect(nearestTabIndex(200, 390)).toBe(1)
    expect(nearestTabIndex(760, 390)).toBe(2)
    expect(nearestTabIndex(1170, 390)).toBe(3)
    expect(nearestTabIndex(10, 0)).toBe(-1)
  })
})
