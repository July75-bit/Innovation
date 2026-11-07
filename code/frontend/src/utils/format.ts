/**
 * 白话导读：小工具集合——把后端给的数字变成好看的字符串，纯展示、不参与任何业务计算。
 *
 * money(4748) → "4748.00"；pct(5) → "+5.00%"；trendClass(-2.3) → "down"（页面 CSS 据此染成绿/红）；
 * dateTime(...) → 浏览器本地时间格式。
 *
 * 为什么单独放一个文件：五个页面都要显示金额，规则集中一处，改格式只动这一行。
 * 涨跌幅是后端算好的，这里只加符号和百分号，绝不重算（避免前后端两个数字对不上）。
 */

/**
 * 展示层格式化。
 * 注意：后端返回的金额/百分比已是最终数值（契约 §1「前端不再二次截断」），
 * 这里只做展示格式化，不做任何四舍五入以外的数值计算。
 */

/** 金额展示：保持两位小数，如 4748 -> "4748.00" */
export function money(value: number): string {
  return value.toFixed(2)
}

/** 涨跌幅展示：后端已算好 change_pct / profit_pct，这里只加正负号与 % */
export function pct(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

/** 涨绿跌红由样式类决定：正 -> up，负 -> down，0 -> flat */
export function trendClass(value: number): 'up' | 'down' | 'flat' {
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'flat'
}

/** ISO 8601 UTC 时间转本地可读格式（浏览器直接解析契约里的 ...Z 字符串） */
export function dateTime(iso: string): string {
  return new Date(iso).toLocaleString()
}

/** 价格历史点的短时间（时:分） */
export function shortTime(iso: string): string {
  return new Date(iso).toLocaleTimeString()
}
