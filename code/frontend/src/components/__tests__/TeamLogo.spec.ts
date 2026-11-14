/**
 * 白话导读：队标组件与映射表的测试。
 *
 * 重点不是"图片好不好看"，而是**认不认得出队伍**：
 * 赛程给的是 team_id，后端选手给的是队伍简称，历史数据里还有全称——
 * 三种写法必须落到同一张图；认不到或图挂了要退成队名首字母，绝不能是浏览器破图。
 */
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import TeamLogo from '../TeamLogo.vue'
import { teamDisplayName, teamIdByName, teamInitials, teamLogo } from '../../data/teamLogos'

/** 与 data/match_schedule.json 的 teams[] 一一对应 */
const TEAMS: [number, string, string][] = [
  [1, 'Vitality', 'vitality'],
  [2, 'Spirit', 'spirit'],
  [3, 'Falcons', 'falcons'],
  [4, 'FaZe Clan', 'faze'],
  [5, 'G2', 'g2'],
  [6, 'NAVI', 'navi'],
  [7, 'Astralis', 'astralis'],
  [8, 'The MongolZ', 'mongolz'],
]

describe('teamLogos 映射表', () => {
  it('8 支队都有本地图，且文件名与队伍对应', () => {
    for (const [id, , slug] of TEAMS) {
      expect(teamLogo(id)).toContain(`${slug}.`)
    }
  })

  it('简称、全称、team_id 三种写法落到同一张图', () => {
    expect(teamLogo('G2')).toBe(teamLogo('G2 Esports'))
    expect(teamLogo('G2')).toBe(teamLogo(5))
    expect(teamLogo('NAVI')).toBe(teamLogo('Natus Vincere'))
    expect(teamLogo('The MongolZ')).toBe(teamLogo('MongolZ'))
    expect(teamIdByName('team vitality')).toBe(1)
    expect(teamIdByName('faze')).toBe(4)
  })

  it('认不出的队伍返回 null，交给组件兜底', () => {
    expect(teamLogo('不存在战队')).toBeNull()
    expect(teamLogo(99)).toBeNull()
    expect(teamLogo(null)).toBeNull()
    expect(teamIdByName(undefined)).toBeNull()
  })

  it('兜底首字母：单词取前两个字母，多词取首字母', () => {
    expect(teamInitials('Astralis')).toBe('AS')
    expect(teamInitials('FaZe Clan')).toBe('FC')
    expect(teamInitials('')).toBe('?')
  })

  it('显示名：id 与别名都能反查回规范名', () => {
    expect(teamDisplayName(8)).toBe('The MongolZ')
    expect(teamDisplayName('natus vincere')).toBe('NAVI')
    expect(teamDisplayName('未知队')).toBe('未知队')
  })
})

describe('TeamLogo', () => {
  it('按 team_id 渲染 img，alt 带上队名', () => {
    const w = mount(TeamLogo, { props: { team: 7 } })
    const img = w.get('img')
    expect(img.attributes('src')).toContain('astralis')
    expect(img.attributes('alt')).toContain('Astralis')
    expect(w.attributes('role')).toBe('img')
  })

  it('按队伍名渲染（名单里只有 p.team 字符串的场景）', () => {
    const w = mount(TeamLogo, { props: { team: 'FaZe Clan', size: 'xs' } })
    expect(w.classes()).toContain('xs')
    expect(w.get('img').attributes('src')).toContain('faze')
  })

  it('认不到的队伍不出现破图，退成队名首字母', () => {
    const w = mount(TeamLogo, { props: { team: 'Newbie Squad' } })
    expect(w.find('img').exists()).toBe(false)
    expect(w.text()).toBe('NS')
  })

  it('图片加载失败时同样退成首字母', async () => {
    const w = mount(TeamLogo, { props: { team: 'Spirit' } })
    await w.get('img').trigger('error')
    expect(w.find('img').exists()).toBe(false)
    expect(w.text()).toBe('SP')
  })
})
