/**
 * 设计令牌守卫测试：CSS（tokens.css）与 JSON（design-tokens.json）必须同源同值。
 *
 * 为什么要有这条：设计交付物最怕"文档一份、代码一份，慢慢不一样"。
 * 这里把两份文件对齐 + 结构要求（9/5/3 阶、玻璃令牌、降级规则、正文 16/1.6）当测试跑。
 */
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const css = readFileSync('src/assets/tokens.css', 'utf8')
const glassCss = readFileSync('src/assets/liquid-glass.css', 'utf8')
const json = JSON.parse(readFileSync('src/assets/design-tokens.json', 'utf8')) as {
  version: string
  modes: { default: string }
  tokens: Record<string, { group: string; light: string; dark: string; purpose: string }>
  shadow: { rule: string }
}

/** 只取 :root 第一块（深色默认）与 [data-theme='light'] 块里的声明 */
function parseBlock(source: string): Record<string, string> {
  const out: Record<string, string> = {}
  for (const m of source.matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    out[m[1] ?? ''] = (m[2] ?? '').trim()
  }
  return out
}

const rootEnd = css.indexOf("/* ============================================================", css.indexOf('--z-toast'))
const darkBlock = parseBlock(css.slice(0, rootEnd > 0 ? rootEnd : undefined))
const lightIdx = css.indexOf("[data-theme='light']")
const lightBlock = lightIdx > 0 ? parseBlock(css.slice(lightIdx)) : {}

/** 归一化：去空格、小写、把小数末尾的 0 去掉（0.90 == 0.9） */
function norm(value: string): string {
  return value
    .replace(/\s+/g, '')
    .toLowerCase()
    .replace(/(\d+\.\d*?)0+(?=[,)])/g, '$1')
    .replace(/(\d+)\.(?=[,)])/g, '$1')
}

const tok = (name: string) => json.tokens[name]!
const varsOf = (group: string) => Object.keys(json.tokens).filter((k) => tok(k).group === group)

describe('设计令牌 · CSS 与 JSON 同源', () => {
  it('JSON 声明了双模式与版本', () => {
    expect(json.version).toBe('2.0.0')
    expect(json.modes.default).toBe('dark')
  })

  it('每个 JSON 令牌都能在 tokens.css 里找到同值（深色）', () => {
    const missing: string[] = []
    const diff: string[] = []
    for (const [name, token] of Object.entries(json.tokens)) {
      const cssValue = darkBlock[name]
      if (!cssValue) {
        missing.push(name)
        continue
      }
      // CSS 里用 var() 引用的令牌（如 --color-bg）不比字面值
      if (cssValue.startsWith('var(')) continue
      if (norm(cssValue) !== norm(token.dark)) diff.push(`${name}: css=${cssValue} json=${token.dark}`)
    }
    expect(missing).toEqual([])
    expect(diff).toEqual([])
  })

  it('凡在浅色块里定义的令牌，值必须与 JSON 的 light 一致', () => {
    const diff: string[] = []
    for (const [name, value] of Object.entries(lightBlock)) {
      const token = tok(name)
      if (!token) continue
      if (value.startsWith('var(')) continue // CSS 里用 var() 引用的令牌不比字面值
      if (norm(value) !== norm(token.light)) diff.push(`${name}: css=${value} json=${token.light}`)
    }
    expect(diff).toEqual([])
  })

  it('每个令牌都有用途说明（设计交付物不允许"裸值"）', () => {
    const noPurpose = Object.entries(json.tokens)
      .filter(([, t]) => !t.purpose || t.purpose.trim().length < 2)
      .map(([k]) => k)
    expect(noPurpose).toEqual([])
  })
})

describe('设计令牌 · 结构要求（对应规范条目）', () => {
  it('中性色 9 阶、主色 5 阶、语义色 4 组各 3 阶', () => {
    expect(varsOf('color.neutral')).toHaveLength(9)
    expect(varsOf('color.primary')).toHaveLength(5)
    const semantic = varsOf('color.semantic')
    expect(semantic).toHaveLength(12)
    for (const role of ['success', 'warning', 'error', 'info']) {
      expect(semantic.filter((v) => v.startsWith(`--color-${role}-`))).toHaveLength(3)
    }
  })

  it('玻璃令牌齐全（7 个必需 + 内高光/回退底）', () => {
    const glass = varsOf('material.glass')
    for (const required of [
      '--glass-bg',
      '--glass-border',
      '--glass-blur',
      '--glass-saturate',
      '--glass-radius',
      '--glass-scrim',
      '--glass-shadow',
      '--glass-highlight',
      '--glass-solid',
    ]) {
      expect(glass).toContain(required)
    }
  })

  it('材质层圆角恰好 12 / 16 / 20 / 24，内容层仍是 4/6/8', () => {
    const radii = varsOf('radius.material').map((k) => tok(k).dark)
    expect(radii).toEqual(['12px', '16px', '20px', '24px'])
    expect(tok('--radius-material-lg').dark).toBe('20px')
    expect(css).toContain('--radius-xs: 4px')
    expect(css).toContain('--radius-sm: 6px')
    expect(css).toContain('--radius-md: 8px')
  })

  it('间距 8 档 = 4/8/12/16/24/32/48/64', () => {
    const spacing = varsOf('spacing').map((k) => tok(k).dark)
    expect(spacing).toEqual(['4px', '8px', '12px', '16px', '24px', '32px', '48px', '64px'])
  })

  it('正文 16px / 行高 1.6；辅助最小 13px', () => {
    expect(tok('--font-size-body').dark).toBe('16px')
    expect(tok('--line-height-body').dark).toBe('1.6')
    expect(tok('--font-size-cap').dark).toBe('13px')
  })

  it('阴影只有"无"和"浮层极轻"，内容卡片禁止阴影', () => {
    expect(tok('--shadow-none').dark).toBe('none')
    expect(tok('--glass-shadow').dark).toMatch(/^0 \d+px \d+px rgba\(0,\s*0,\s*0,\s*0\.3/)
    expect(json.shadow.rule).toContain('1px 边框')
  })
})

describe('设计令牌 · 降级规则必须存在', () => {
  it('@supports not (backdrop-filter) 回退到 --glass-solid', () => {
    expect(glassCss).toContain('@supports not')
    expect(glassCss).toMatch(/@supports not \(\s*\(backdrop-filter/)
    expect(glassCss).toMatch(/var\(--glass-solid\)/)
  })

  it('prefers-reduced-transparency: reduce 时去模糊 + 实色底', () => {
    expect(glassCss).toContain('@media (prefers-reduced-transparency: reduce)')
  })

  it('令牌层声明了浅色模式块与玻璃令牌（深色为默认）', () => {
    expect(lightIdx).toBeGreaterThan(0)
    expect(darkBlock['--glass-bg']).toBeTruthy()
    expect(lightBlock['--glass-bg']).toBe('rgba(255, 255, 255, 0.62)')
    expect(lightBlock['--glass-scrim']).toBe('rgba(255, 255, 255, 0.72)')
    expect(lightBlock['--glass-border']).toBe('rgba(255, 255, 255, 0.72)')
  })
})
