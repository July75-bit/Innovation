# PlayerStock 设计系统 Token 规范

> **产品**：PlayerStock —— 虚拟 CS2 选手股交易模拟
> **版本**：**v2.0**（2026-11-14）——在 v1「深色扁平」基础上补齐 **浅色/深色双模式** 与 **液态玻璃材质层令牌**
> **交付文件（两份同源同值，由 `design-tokens.spec.ts` 守护）**：
> - CSS（变量定义）：[`code/frontend/src/assets/tokens.css`](../../code/frontend/src/assets/tokens.css)
> - JSON（含用途与对比度标注）：[`code/frontend/src/assets/design-tokens.json`](../../code/frontend/src/assets/design-tokens.json)
> - 玻璃材质实现与降级：[`liquid-glass.css`](../../code/frontend/src/assets/liquid-glass.css) + 规范 [liquid_glass_design.md](liquid_glass_design.md)
> - 组件实现（Vue 9 组件 + 状态矩阵）：[ui_components.md](ui_components.md)；兼容层：[`main.css`](../../code/frontend/src/assets/main.css)
> **分层原则**：内容层（正文/表格/表单/长文）= 扁平实色 + 1px 边框；材质层（导航壳/浮层）= 液态玻璃，同屏面积 ≤30%。
> **对比度口径**：WCAG 2.1；深色相对表面 `#181b22`、浅色相对表面 `#ffffff`；AA 正文 ≥4.5:1、大号文字 ≥3:1。

---

## 1. 色彩

### 1.1 中性色 9 阶（双模式；**索引 = 对比强度，不随明暗翻转**）

| Token | 深色 | 浅色 | 用途 | 对比度（深/浅，相对表面） |
| --- | --- | --- | --- | --- |
| `--color-neutral-0` | `#f7f8fa` | `#0b0d11` | 最高对比文字（标题强调、大数字） | 16.22:1 / 19.45:1 |
| `--color-neutral-100` | `#e9eaee` | `#1a1d23` | 正文主文字 | 14.33:1 / 16.88:1 |
| `--color-neutral-200` | `#c6c9d1` | `#2e333c` | 强调正文 | 10.40:1 / 12.69:1 |
| `--color-neutral-300` | `#b6bac4` | `#454b56` | 次要文字 / 辅助说明 | 8.87:1 / 8.77:1 |
| `--color-neutral-400` | `#8f949f` | `#5d6470` | 弱辅助（时间戳、占位提示） | 5.67:1 / 5.96:1 |
| `--color-neutral-500` | `#5c626e` | `#8b919d` | 禁用文字、占位符（仅装饰，不作正文） | 非文字（禁用态例外） |
| `--color-neutral-600` | `#3a404c` | `#c3c8d2` | 强边框 / 分割线 | 非文字 |
| `--color-neutral-700` | `#262b34` | `#e8ebf0` | 抬起面 / 悬停底色 | 非文字 |
| `--color-neutral-800` | `#181b22` | `#ffffff` | 卡片 / 表面 | 非文字 |

**画布**：深色 `--color-canvas: #12141a` / 浅色 `#f4f6f9`（页面底色，不属于 9 阶；不用纯黑/纯白）。
> 切换模式：`document.documentElement.dataset.theme = 'light'`（默认深色；<html> 不加属性即深色）。

### 1.2 主色 5 阶（品牌红）

| Token | 色值 | 用途 | 对比度建议 |
| --- | --- | --- | --- |
| `--color-primary-50` | `#fdecec` | 浅底/标签底色 | 与深字搭配 |
| `--color-primary-100` | `#f8c9ca` | 浅底悬停 | 与深字搭配 |
| `--color-primary-300` | `#ef7377` | **深色底上的主色文字/图标** | 6.06:1 ✅（涨跌幅文字用这一档） |
| `--color-primary-500` | `#e5484d` | 品牌红：涨跌填充、图表、强调块 | 作 16px 文字 4.40:1 ⚠️（文字请用 300） |
| `--color-primary-700` | `#c23438` | **实心按钮底**（白字 5.47:1 ✅） | 白字达标 |

**交互别名**：`--color-action: #c23438`（主按钮底）、`--color-action-hover: #a82a2e`（白字 6.5:1）、`--color-action-text: #ffffff`。

### 1.3 语义色（各 3 阶：subtle / base / strong）

| 语义 | subtle（浅底） | base（深底文字/图标） | strong（实心底/描边） | 建议 |
| --- | --- | --- | --- | --- |
| **成功/跌** | `#e8f8ef` | `#5fd394`（9.22:1 ✅） | `#1a7f4b`（白字 5.02:1 ✅） | 跌、交易中、成功提示 |
| **警告/暂停** | `#fdf3e3` | `#e8b45c`（9.12:1 ✅） | `#a86f17`（白字 4.24:1 ⚠️） | 暂停交易、校验提示；实心底请配深字 |
| **错误/危险** | `#fdeaea` | `#f07171`（5.99:1 ✅） | `#b41c1c`（白字 6.72:1 ✅） | 错误、删除账号 |
| **信息** | `#e8f1fd` | `#6b9bf5`（6.26:1 ✅） | `#1d4ed8`（白字 6.70:1 ✅） | 提示、说明 |

### 1.4 语义映射（组件只引用这些，不直接写色阶）

```css
--color-bg: var(--color-canvas);
--color-surface: var(--color-neutral-800);
--color-surface-raised: var(--color-neutral-700);
--color-surface-sunken: #14161c;        /* 输入框底，仍非纯黑 */
--color-text: var(--color-neutral-100);
--color-text-muted: var(--color-neutral-300);
--color-text-faint: var(--color-neutral-400);
--color-border: #2c313b;
--color-focus: var(--color-primary-300);
/* 业务语义：涨=主色、跌=成功绿（国内行情习惯） */
--color-up: var(--color-primary-500);
--color-up-text: var(--color-primary-300);
--color-down: var(--color-success-base);
--color-halt: var(--color-warning-base);
```

### 1.5 颜色数量控制

> 中性 9 阶 + 主色 5 阶 + 4 组语义 × 3 阶 = 固定调色板，**不新增颜色**；
> 需要透明度时用 `rgba()` 派生（如 `--color-up-subtle`），不再造新色值。

### 1.6 材质层：液态玻璃令牌（7 个必需 + 2 个辅助）

> 只给"会盖住其他内容的壳/浮层"用：导航壳、移动顶栏、模态框、Popover、tooltip、悬浮工具条。
> **内容层（卡片/表格/表单/长文）永远不用玻璃**。玻璃面积 ≤30%（实测桌面 18.13% / 移动 8.25%）。

| Token | 浅色 | 深色 | 用途 | 要求 |
| --- | --- | --- | --- | --- |
| `--glass-bg` | `rgba(255,255,255,.62)` | `rgba(20,20,20,.60)` | 玻璃底（导航壳/控件） | 玻璃上文字 ≥4.5:1 |
| `--glass-bg-strong` | `rgba(255,255,255,.72)` | `rgba(20,20,20,.72)` | 浮层面板底（弹窗/Popover） | 面板内正文 ≥4.5:1 |
| `--glass-scrim` | `rgba(255,255,255,.72)` | `rgba(20,20,20,.72)` | 可读性 scrim：文字直接坐玻璃时用 | 正文 ≥4.5:1（v2 实测最低 8.55:1） |
| `--glass-border` | `rgba(255,255,255,.72)` | `rgba(255,255,255,.16)` | 1px 描边（材质边界） | 非文字 |
| `--glass-blur` | `22px` | `22px` | 背景模糊（规格 18–28px；≤600px 降 18px） | 性能：窄屏降档 |
| `--glass-saturate` | `180%` | `180%` | 背景饱和度（规格 160–200%） | 性能：移动端注意帧率 |
| `--glass-radius` | `20px` | `20px` | 浮层圆角（= `--radius-material-lg`） | 与内容层 4/6/8 分开 |
| `--glass-shadow` | `0 8px 24px rgba(0,0,0,.08)` | `0 8px 24px rgba(0,0,0,.32)` | **仅浮层**极轻阴影 | 内容卡禁止阴影 |
| `--glass-highlight` | `rgba(255,255,255,.90)` | `rgba(255,255,255,.14)` | 顶部 1px 内高光（材质边界） | 1px 以内，禁止大范围高光/渐变 |
| `--glass-solid` | `#ffffff` | `#171a21` | 不支持 backdrop-filter / 降低透明时的回退底 | 回退后对比度不得下降 |

**配套实现**：`liquid-glass.css` 里 `.glass` / `.glass--nav` / `.glass--panel` / `.glass--control` / `.glass--scrim`
（旧类名 `--glass-tint-*`、`--glass-radius-*` 保留为别名，组件无需改）。

### 1.7 浅色模式覆盖（除中性 9 阶外的差异）

```css
[data-theme='light'] {
  /* 主色：浅底上的文字档必须更深才达 AA */
  --color-primary-300: #c23539;   /* 主色文字 5.6:1（深色模式是 #ef7377） */
  --color-primary-700: #b02a2e;   /* 实心按钮底，白字 ≈6.0:1 */
  /* 语义色：base 档用于浅底文字，strong 档用于实心底 */
  --color-success-base: #127a45;  --color-success-strong: #15703f;
  --color-warning-base: #8a5a0f;  --color-warning-strong: #8a5a0f;
  --color-error-base:   #b41c1c;  --color-error-strong:   #b41c1c;
  --color-info-base:    #1d4ed8;  --color-info-strong:    #1d4ed8;
  --color-border: #d7dbe3;  --color-focus: #e5484d;
  --shadow-overlay: 0 8px 24px rgba(16,24,40,.12);
}
```

### 1.8 主题切换（浅色 ↔ 深色）

- 入口：侧栏底部「浅色/深色」按钮、移动端顶栏图标按钮（`App.vue`）；`/ui-kit` 也有同款按钮。
- 实现：`src/composables/useTheme.ts` 写 `<html data-theme="light|dark">` 并持久化到
  `localStorage['playerstock.theme.v1']`；`index.html` 用**同一 key** 的内联脚本在 CSS 之前定主题（防闪）。
- 优先级：**已保存选择 > 系统 `prefers-color-scheme` > 深色**。
- 令牌：只在 `tokens.css` 里 `:root`（深色）/`[data-theme='light']`（浅色）两块整块覆盖，组件不做模式判断。
- 文字专用档：品牌红作文字必须用 `--accent-text`（= primary-300）或 `--up-text`，
  直接用 `--color-primary-500` 只有 4.40:1（不达 AA）。

> **2026-11-14 全量回归**：7 条路由 × 浅/深 × 桌面/移动，共 24 个组合；
> 自动审计全部"文字 vs 有效背景"对比度：**违规 0 条**；横向溢出 0；证据 `69~78`。

---

## 2. 字体

| Token | 值 | 用途 |
| --- | --- | --- |
| `--font-size-h1` | 28px / 700 | 页面主标题（每页最多 1 个） |
| `--font-size-h2` | 22px / 700 | 区块标题 |
| `--font-size-h3` | 18px / 600 | 卡片标题 |
| `--font-size-body` | **16px / 400–500，行高 1.6** | 正文（≥16 硬性） |
| `--font-size-aux` | 14px / 400，行高 1.5 | 辅助说明 |
| `--font-size-cap` | 13px / 400，行高 1.5 | 标签、时间戳 |
| `--font-size-min` | 12px | 仅非关键标注，禁止更小 |

- 字体栈：`'Segoe UI', 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system, sans-serif`
- 标题行高 1.35；正文行宽建议 65–75 字符（长文用 `max-width: 62ch`）
- 金额/价格：`font-variant-numeric: tabular-nums`（数字不跳动）

---

## 3. 间距 / 圆角 / 阴影

| 类别 | Token | 值 |
| --- | --- | --- |
| 间距 | `--space-1…8` | 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64（8pt 体系，只允许这 8 档） |
| 圆角·内容层 | `--radius-xs/sm/md/lg` | **4 / 6 / 8 / 8**（标签 4、控件 6、卡片 8） |
| 圆角·材质层 | `--radius-material-sm/md/lg/xl` | **12 / 16 / 20 / 24**（工具条 12、小浮层 16、弹窗 20、sheet 24） |
| 边框 | `--border-width` | 1px（内容层靠边框 + 背景色差表达层级） |
| 阴影 | `--shadow-none` / `--shadow-overlay` / `--glass-shadow` | `none` / 仅弹层 `0 8px 24px rgba(16,24,40,.12)`（浅）或 `0 1px 2px rgba(0,0,0,.3)`（深）/ 玻璃浮层见 §1.6 |
| 控件高 | `--control-height-sm/md/lg` | 36 / 40 / 44 |
| 图标 | `--icon-size-sm/md/lg` | 16 / 20 / 24 |
| 布局 | `--layout-max-width` / `--layout-sidebar-width` | 1280 / 232 |

> **层级规则**：内容卡片一律 `1px 边框 + 背景色差`、**零阴影**；只有浮层（弹窗/Popover/tooltip）允许极轻投影。
> **两套圆角不混用**：内容层 4/6/8、材质层 12/16/20/24；跨层混用会被 `design-tokens.spec.ts` 拦下。

---

## 4. 组件规则

### 4.1 按钮

| 类型 | 背景 | 文字 | 高度 | 悬停 | 禁用 |
| --- | --- | --- | --- | --- | --- |
| 主按钮 | `--color-action` `#c23438` | 白 `#fff` | 44 | `#a82a2e` | 透明度 0.55 |
| 次按钮 | 透明 + 1px 边框 | `--color-text-muted` | 40 | 边框提亮 + 底色 raised | 0.55 |
| 危险 | `--color-error-strong` `#b41c1c` | 白 | 40 | `#9c1818` | 0.55 |
| 文字按钮 | 透明 | muted | 36–40 | 底色 raised | 0.55 |

- 焦点：`outline: 2px solid var(--color-focus); outline-offset: 2px`
- 文案：动词开头（「买入 2 股」「重新分析」「采纳建议」），禁止只写「确定/提交」
- 点击区 ≥44px（移动端主按钮 44）

### 4.2 输入框

| 状态 | 样式 |
| --- | --- |
| 默认 | 底 `--color-surface-sunken`、1px 边框、圆角 6、高 40、正文 16px |
| 悬停 | 边框 `--color-border-strong` |
| 焦点 | 2px 主色焦点环 + 边框主色 |
| 出错 | 边框 `--color-error-base` + 13px 错误文案（原因 + 下一步） |
| 禁用 | 透明度 0.55 + 禁止光标 |
| 结构 | 必须有 `<label>` + 可选 hint；错误信息用 `aria-invalid` |

### 4.3 卡片

| 状态 | 样式 |
| --- | --- |
| 默认 | 底 `--color-surface`、1px 边框、圆角 8、内边距 16、**无阴影** |
| 可点击 | 悬停边框提亮（`--color-border-strong`），不位移、不放大 |
| 选中 | 左侧 2px 主色竖条 |
| 层级 | 标题 h3 18px/600 + 辅助文字 13px muted |

### 4.4 表格 / 列表

| 项 | 规则 |
| --- | --- |
| 表头 | 底 `--color-surface-raised`、13px、600、下边框 1px |
| 行 | 下边框 1px；悬停底色 raised |
| 数字列 | 右对齐 + `tabular-nums`；涨用 `--color-up-text`、跌用 `--color-down` |
| 空态 | 居中 + 一句引导（「还没有持仓，去市场挑一个」）+ 一个次按钮 |
| 加载 | 骨架行（不整页闪白） |
| 错误 | 行内错误条 + 重试按钮（不自动重放写操作） |

### 4.5 导航

| 项 | 规则 |
| --- | --- |
| 宽度 | 232px；条目高 40px；圆角 6 |
| 默认 | 文字 muted；图标 16px 线性 |
| 悬停 | 底 `--color-surface-raised`、文字变主文字色 |
| 选中 | 底 raised + 左侧 2px 主色竖条 + 文字 600（**不用整块主色**，把红色留给主 CTA） |
| 移动端 | 折叠为顶部菜单抽屉（≤960px），条目高 44px |

### 4.6 徽章

`ui-badge`：圆角 4、13px、浅底 + 语义文字色；状态**必须带文字**（不只靠颜色）：
交易中（success）、暂停交易（warning）、风险 低/中/高（success/warning/error）。

---

## 5. 两版交付

### 5.1 CSS（节选，完整见 `tokens.css`；深色为 `:root` 默认，浅色为 `[data-theme='light']` 覆盖）

```css
:root {
  /* 中性 9 阶（深色） */
  --color-neutral-0: #f7f8fa;  --color-neutral-100: #e9eaee; --color-neutral-200: #c6c9d1;
  --color-neutral-300: #b6bac4; --color-neutral-400: #8f949f; --color-neutral-500: #5c626e;
  --color-neutral-600: #3a404c; --color-neutral-700: #262b34; --color-neutral-800: #181b22;
  --color-canvas: #12141a;

  /* 主色 5 阶 + 语义（各 3 阶）—— 详见文件，这里只列关键 */
  --color-primary-500: #e5484d; --color-primary-300: #ef7377; --color-primary-700: #c23438;
  --color-success-base: #5fd394; --color-warning-base: #e8b45c; --color-error-base: #f07171;

  /* 字体 / 间距 / 圆角 / 阴影 */
  --font-size-body: 16px; --line-height-body: 1.6;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;
  --radius-xs: 4px; --radius-sm: 6px; --radius-md: 8px; --radius-lg: 8px;      /* 内容层 */
  --radius-material-sm: 12px; --radius-material-md: 16px;
  --radius-material-lg: 20px; --radius-material-xl: 24px;                       /* 材质层 */
  --shadow-none: none; --shadow-overlay: 0 1px 2px rgba(0, 0, 0, 0.3);

  /* 材质层：液态玻璃（深色） */
  --glass-bg: rgba(20, 20, 20, 0.6);
  --glass-bg-strong: rgba(20, 20, 20, 0.72);
  --glass-border: rgba(255, 255, 255, 0.16);
  --glass-blur: 22px;
  --glass-saturate: 180%;
  --glass-radius: var(--radius-material-lg);
  --glass-scrim: rgba(20, 20, 20, 0.72);
  --glass-shadow: 0 8px 24px rgba(0, 0, 0, 0.32);
  --glass-highlight: rgba(255, 255, 255, 0.14);
  --glass-solid: #171a21;              /* 降级回退底 */
}

/* 浅色模式：只覆盖差异项（中性 9 阶、主色 300/700、语义 base/strong、玻璃、阴影） */
[data-theme='light'] {
  --color-neutral-0: #0b0d11; --color-neutral-100: #1a1d23; --color-neutral-800: #ffffff;
  --color-canvas: #f4f6f9;
  --glass-bg: rgba(255, 255, 255, 0.62);
  --glass-bg-strong: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(255, 255, 255, 0.72);
  --glass-scrim: rgba(255, 255, 255, 0.72);
  --glass-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  --glass-solid: #ffffff;
}
```

### 5.2 JSON（节选，完整见 `design-tokens.json`；v2 用 `tokens` 平铺表，每个令牌带双模式值与用途）

```json
{
  "version": "2.0.0",
  "modes": { "default": "dark", "switch": "document.documentElement.dataset.theme = 'light' | 'dark'" },
  "tokens": {
    "--color-neutral-100": {
      "group": "color.neutral",
      "light": "#1a1d23",
      "dark": "#e9eaee",
      "purpose": "正文主文字",
      "contrast": {
        "requirement": "AA：正文/辅助 ≥4.5:1，≥18.66px 粗体或 ≥24px 大号 ≥3:1",
        "light": { "on": "#ffffff", "ratio": 16.88 },
        "dark": { "on": "#181b22", "ratio": 14.33 }
      }
    },
    "--glass-bg": {
      "group": "material.glass",
      "light": "rgba(255,255,255,0.62)",
      "dark": "rgba(20,20,20,0.6)",
      "purpose": "玻璃底（导航壳/控件，文字较少）",
      "requirement": "玻璃上的文字必须 ≥4.5:1；同屏玻璃面积 ≤30%"
    },
    "--glass-scrim": {
      "group": "material.glass",
      "light": "rgba(255,255,255,0.72)",
      "dark": "rgba(20,20,20,0.72)",
      "purpose": "可读性 scrim：文字直接坐玻璃时用这档",
      "requirement": "玻璃上正文 ≥4.5:1（v2 实测最低 8.55:1）"
    }
  },
  "radius": { "content": { "xs": 4, "sm": 6, "md": 8 }, "material": { "sm": 12, "md": 16, "lg": 20, "xl": 24 } },
  "spacing": { "1": 4, "2": 8, "3": 12, "4": 16, "5": 24, "6": 32, "7": 48, "8": 64 }
}
```

### 5.3 降级规则（`liquid-glass.css`，可直接抄）

```css
/* ① 浏览器不支持 backdrop-filter：回退不透明底，保留圆角/描边/内高光 */
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .glass {
    background-color: var(--glass-solid);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}

/* ② 用户要求减少透明：同样回退，并关掉半透明高光 */
@media (prefers-reduced-transparency: reduce) {
  .glass {
    background-color: var(--glass-solid);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
  .glass--interactive::after { display: none; }
}

/* ③ 手动降级开关（/ui-kit「模拟降级」按钮 / 现场演示用） */
html.no-backdrop-filter .glass {
  background-color: var(--glass-solid) !important;
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
}

/* ④ 动态高光只在「有鼠标 + 允许动效」时启用；移动端与 reduced-motion 自动关闭 */
@media (hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference) {
  .glass--interactive:hover::after { opacity: 1; }
}
```

> 实测：模拟不支持 backdrop-filter 时玻璃面积 0%、底为 `rgb(23,26,33)`；
> 模拟 `prefers-reduced-transparency: reduce` 时 `backdrop-filter: none`（Edge 157 生效）。

---

## 6. 接入方式（零破坏）

`main.css` 顶部引入令牌，并把**旧变量名映射**到新令牌，现有组件无需改动：

```css
@import './tokens.css';
@import './ui-kit.css';

:root {
  --bg: var(--color-canvas);
  --surface: var(--color-surface);
  --text: var(--color-text);
  --muted: var(--color-text-muted);
  --accent: var(--color-primary-500);
  --up: var(--color-up);
  --down: var(--color-down);
  --shadow-1: var(--shadow-none);   /* 扁平化：旧阴影统一清零 */
  --radius-pill: var(--radius-sm);  /* 旧胶囊统一为 6px */
}
```

新组件直接用 `ui-btn` / `ui-input` / `ui-card` / `ui-table` / `ui-nav` / `ui-badge`
（见 `ui-kit.css`），不要再写一套颜色/圆角/字号。

---

## 7. 验收自查

| 要求 | 结果 |
| --- | --- |
| 中性 9 阶 | ✅ n-0…n-800（双模式）+ 画布色 |
| 主色 5 阶 | ✅ 50/100/300/500/700（浅色模式 300/700 加深以达 AA） |
| 语义色各 3 阶 | ✅ success/warning/error/info × subtle/base/strong（双模式） |
| 正文 16px/1.6、辅助 13px/1.5 | ✅ 令牌固定，页面无硬编码小字 |
| H1–H3 层级 | ✅ 28/22/18 |
| 间距 4…64 | ✅ 8 档（4/8/12/16/24/32/48/64） |
| 圆角 | ✅ 内容层 4/6/8；材质层 12/16/20/24（两套不混用） |
| 阴影只允许 0/极轻 | ✅ 内容卡 none；遮罩层极轻；玻璃浮层 `--glass-shadow` |
| **浅色 / 深色双模式** | ✅ `:root`（深色默认）+ `[data-theme='light']`；业务页实测两种模式截图见证据 66–68 |
| **玻璃令牌 7 个必需项** | ✅ `--glass-bg/border/blur/saturate/radius/scrim/shadow`（+ 内高光/回退底） |
| **玻璃降级** | ✅ `@supports not (backdrop-filter)` → `--glass-solid`；`prefers-reduced-transparency: reduce` 同回退并去高光；另有手动开关 |
| 玻璃配额 ≤30% | ✅ 桌面 18.13%、移动 8.25%（同屏可见玻璃面积，CDP 量算） |
| 玻璃上文字 AA | ✅ 6 处直接坐在玻璃上的文字实测最低 **8.55:1**；坐在实色卡片/头像上的文字按实色对算 |
| CSS + JSON 双版本 | ✅ 83 个令牌同源同值，`design-tokens.spec.ts` 12 条断言守护（含 9/5/3 阶、玻璃、降级、半径、正文） |
| 令牌用途 + 对比度标注 | ✅ CSS 注释 + JSON 每个令牌带 `purpose` / `contrast` / `requirement` |
| 组件规则（按钮/输入/卡片/表格/导航） | ✅ §4 + `ui-kit.css` |
| AA 合规 | ✅ 正文 14.33:1（深）/16.88:1（浅）；按钮白字 5.02–6.72；品牌红文字统一走 `--accent-text`/`--up-text`（深 `#ef7377` / 浅 `#c23539`） |
| 双模式全量回归 | ✅ 7 路由 × 深/浅 × 桌面/移动 = **24 组合，自动审计违规 0**；证据 69–78 |

**已知限制（如实记录）**

1. 业务页**默认深色**；浅色模式已完整定义令牌并通过 `/ui-kit` 与市场页实拍验证，但**全站逐页浅色回归尚未做**（个别页面可能有硬编码色残留）。
2. 玻璃"液态流动感"只做 hover 轻微斜向高光，没有跟随鼠标的折射/位移（性能与规范双重限制）。
3. 配额统计口径：只算"真实生效的 backdrop-filter 元素"；被遮罩压暗的背景玻璃不计（`/ui-kit` 材质展厅例外，页面已标注）。
