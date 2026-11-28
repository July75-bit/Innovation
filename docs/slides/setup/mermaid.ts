// Mermaid 图配色跟随幻灯片：纸白底、墨色线、细边，不用默认的紫色主题
import { defineMermaidSetup } from '@slidev/types'

export default defineMermaidSetup(() => ({
  theme: 'base',
  // 标签用 SVG 文字而不是 HTML：HTML 标签会继承幻灯片的行高，第二行常被节点框裁掉
  htmlLabels: false,
  flowchart: { htmlLabels: false, padding: 14 },
  themeVariables: {
    // 只用系统自带字体：Mermaid 按渲染时的字体量文字宽高，用网页字体会因加载时机不同把字裁掉
    // （Windows 有微软雅黑，GitHub Actions 的 Ubuntu 装了 fonts-noto-cjk）
    fontFamily: '"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif',
    fontSize: '15px',
    background: '#f6f4ef',
    primaryColor: '#fcfbf8',
    primaryTextColor: '#221f1b',
    primaryBorderColor: '#8a8478',
    secondaryColor: '#efe9de',
    tertiaryColor: '#f6f4ef',
    lineColor: '#6b665c',
    textColor: '#221f1b',
    edgeLabelBackground: '#f6f4ef',
  },
}))
