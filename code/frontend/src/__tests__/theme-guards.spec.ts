/**
 * 设计系统守卫（防"深色没适配"这类问题再犯）。
 *
 * 由来（2026-11-19 用户反馈）：夜间模式下市场页"排序方式"下拉仍是白底。
 * 根因不是某个组件的样式漏了，而是**全站从没声明 CSS `color-scheme`**——
 * 原生表单控件（select/date/scrollbar/autofill）跟它走，不跟我们的颜色变量走。
 *
 * 这个 spec 守四件事：
 *   1. 深浅两套主题都声明了 `color-scheme`；
 *   2. 原生 <select> 必须自己画箭头、并给 option 上色（不能指望 UA 默认）；
 *   3. 样式里不许出现硬编码的 `#fff/#ffffff/#000/white/black`（白名单见下），
 *      主按钮白字一律用 `--color-action-text`；
 *   4. `::selection` / autofill 的主题适配不被删掉。
 */
import { readdirSync, readFileSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { describe, expect, it } from 'vitest'

const SRC = join(process.cwd(), 'src')

function walk(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) return walk(full)
    return /\.(vue|css)$/.test(entry.name) ? [full] : []
  })
}

const files: Record<string, string> = {}
for (const full of walk(SRC)) {
  files[relative(SRC, full).split(sep).join('/')] = readFileSync(full, 'utf8')
}

const tokens = files['assets/tokens.css'] ?? ''
const main = files['assets/main.css'] ?? ''
const market = files['views/MarketView.vue'] ?? ''

/** 允许写死颜色的地方：令牌文件本身、历史玻璃规范（已不用于内容层）、队标底板、UI-Kit 文档示例 */
const ALLOW = new Set([
  'assets/tokens.css',
  'assets/liquid-glass.css',
  'assets/ui-kit.css',
  'components/TeamLogo.vue',
  'views/UiKitView.vue',
])

const COLOR_LITERAL =
  /(?:color|background|border(?:-color)?|fill|stroke)\s*:\s*(?:#(?:fff|ffffff|000|000000)\b|white\b|black\b)/gi

describe('设计系统守卫 · 深色适配', () => {
  it('深色与浅色都声明了 color-scheme（原生控件跟随主题的根因）', () => {
    expect(tokens).toMatch(/:root\s*\{[^}]*color-scheme:\s*dark/)
    expect(tokens).toMatch(/\[data-theme='light'\]\s*\{[^}]*color-scheme:\s*light/)
  })

  it('市场排序的原生 <select> 自己画箭头 + option 上色', () => {
    expect(market).toMatch(/\.sort\s+select\s*\{[^}]*appearance:\s*none/)
    expect(market).toMatch(/\.sort\s+select\s+option\s*\{[^}]*background:/)
  })

  it('样式里没有硬编码黑白（主按钮白字用 --color-action-text）', () => {
    const offenders: string[] = []
    for (const [file, content] of Object.entries(files)) {
      if (ALLOW.has(file)) continue
      const hits = content.match(COLOR_LITERAL)
      if (hits) offenders.push(`${file}: ${hits.join(', ')}`)
    }
    expect(offenders).toEqual([])
  })

  it('保留了选中色 / 自动填充的主题适配', () => {
    expect(main).toContain('::selection')
    expect(main).toContain('input:-webkit-autofill')
  })
})
