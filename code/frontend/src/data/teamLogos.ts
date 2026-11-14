/**
 * 白话导读：8 支战队的队标图片 + "队伍 → 图片"的映射表。
 *
 * 图片不是热链，全部下载在 `src/assets/teams/` 里（来源、文件名、授权口径见同目录 SOURCES.md），
 * 断网、答辩现场没外网都不会变成一堆破图。
 *
 * 想加第 9 支队：把图放进 assets/teams，再在 TEAMS 里加一行（id / 规范名 / 别名），
 * 组件 `TeamLogo.vue` 会自动认得它，页面不用改。
 *
 * 为什么要别名表：赛程数据里队伍是 `team_id` + 简称（"G2"），后端选手对象只带队伍名，
 * 历史数据里还可能出现全称（"G2 Esports"、"Natus Vincere"）。这里统一"归一化后查表"，
 * 与 `core/schedule.ts` 里 `teamIdOf()` 的名字兜底是同一个思路。
 */
import astralis from '../assets/teams/astralis.png'
import faze from '../assets/teams/faze.png'
import falcons from '../assets/teams/falcons.png'
import g2 from '../assets/teams/g2.png'
import mongolz from '../assets/teams/mongolz.png'
import navi from '../assets/teams/navi.png'
import spirit from '../assets/teams/spirit.png'
import vitality from '../assets/teams/vitality.png'

/** 一条队伍记录：id 与 `data/match_schedule.json` 的 `teams[]` 完全一致 */
interface TeamLogoRow {
  id: number
  /** 赛程里的规范名（界面显示就用它） */
  name: string
  /** 文件名（不含扩展名），测试与排查用 */
  slug: string
  asset: string
  /** 全称 / 旧名 / 常见写法，全部指向同一支队 */
  aliases: string[]
}

const TEAMS: readonly TeamLogoRow[] = [
  { id: 1, name: 'Vitality', slug: 'vitality', asset: vitality, aliases: ['Team Vitality'] },
  { id: 2, name: 'Spirit', slug: 'spirit', asset: spirit, aliases: ['Team Spirit'] },
  { id: 3, name: 'Falcons', slug: 'falcons', asset: falcons, aliases: ['Team Falcons'] },
  { id: 4, name: 'FaZe Clan', slug: 'faze', asset: faze, aliases: ['FaZe', 'Faze Clan'] },
  { id: 5, name: 'G2', slug: 'g2', asset: g2, aliases: ['G2 Esports'] },
  { id: 6, name: 'NAVI', slug: 'navi', asset: navi, aliases: ['Natus Vincere'] },
  { id: 7, name: 'Astralis', slug: 'astralis', asset: astralis, aliases: [] },
  {
    id: 8,
    name: 'The MongolZ',
    slug: 'mongolz',
    asset: mongolz,
    aliases: ['MongolZ', 'The Mongolz'],
  },
]

/** 归一化：忽略大小写、空格、连字符之类的部分差异 */
export function normalizeTeamName(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, '')
}

const BY_ID = new Map<number, TeamLogoRow>()
const BY_NAME = new Map<string, TeamLogoRow>()
for (const row of TEAMS) {
  BY_ID.set(row.id, row)
  for (const key of [row.name, ...row.aliases]) BY_NAME.set(normalizeTeamName(key), row)
}

/** 队名（简称 / 全称 / 别名都行）→ team_id；认不出返回 null */
export function teamIdByName(name?: string | null): number | null {
  if (!name) return null
  return BY_NAME.get(normalizeTeamName(name))?.id ?? null
}

/**
 * 队伍 → 队标图片地址。`team` 可以是 team_id，也可以是队伍名；
 * 查不到就返回 null，由调用方（`TeamLogo.vue`）退成队名首字，不显示破图。
 */
export function teamLogo(team?: number | string | null): string | null {
  if (team === null || team === undefined) return null
  const row = typeof team === 'number' ? BY_ID.get(team) : BY_NAME.get(normalizeTeamName(team))
  return row?.asset ?? null
}

/** 队标的可读名字（alt 文案、没有图时的兜底显示都用它） */
export function teamDisplayName(team?: number | string | null): string {
  if (team === null || team === undefined) return ''
  const row = typeof team === 'number' ? BY_ID.get(team) : BY_NAME.get(normalizeTeamName(team))
  return row?.name ?? String(team)
}

/** 没有队标时的兜底：取队名首字母（最多两个），如 "FaZe Clan" → FC */
export function teamInitials(name?: string | null): string {
  if (!name) return '?'
  const words = name
    .trim()
    .split(/[^a-z0-9]+/i)
    .filter(Boolean)
  if (!words.length) return '?'
  if (words.length === 1) return (words[0] ?? '?').slice(0, 2).toUpperCase()
  return words
    .slice(0, 2)
    .map((word) => word.charAt(0))
    .join('')
    .toUpperCase()
}
