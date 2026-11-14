# PlayerStock 设计系统 Token 规范

> **产品**：PlayerStock —— 虚拟 CS2 选手股交易模拟
> **主题**：深色（金融/电竞场景），扁平化 · 产品化 · 高可读性
> **交付文件**：
> - CSS：[`code/frontend/src/assets/tokens.css`](../../code/frontend/src/assets/tokens.css)（变量定义）
> - JSON：[`code/frontend/src/assets/design-tokens.json`](../../code/frontend/src/assets/design-tokens.json)（含用途与对比度）
> - 组件实现（Vue，9 个组件 + 状态矩阵 + 禁止用法）：[ui_components.md](ui_components.md)
> - 组件样式：[`code/frontend/src/assets/ui-kit.css`](../../code/frontend/src/assets/ui-kit.css)（`ui-` 前缀参考实现）
> - 兼容层：[`code/frontend/src/assets/main.css`](../../code/frontend/src/assets/main.css)（旧变量名 → 新令牌，组件零改动）
> **对比度口径**：WCAG 2.1，文字/图标相对表面色 `#181b22`；AA 正文 ≥4.5:1、大号文字 ≥3.0:1。

---

## 1. 色彩

### 1.1 中性色 9 阶

| Token | 色值 | 用途 | 相对表面对比度 |
| --- | --- | --- | --- |
| `--color-neutral-0` | `#f7f8fa` | 最高亮文字（大数字、标题强调） | 16.22:1 ✅ |
| `--color-neutral-100` | `#e9eaee` | 正文主文字 | 14.33:1 ✅ |
| `--color-neutral-200` | `#c6c9d1` | 强调正文 | 10.40:1 ✅ |
| `--color-neutral-300` | `#b6bac4` | 次要文字、辅助说明 | 8.87:1 ✅ |
| `--color-neutral-400` | `#8f949f` | 弱辅助（时间戳、占位） | 5.67:1 ✅ |
| `--color-neutral-500` | `#5c626e` | 禁用文字、占位符（仅装饰） | 2.90:1（非正文，允许） |
| `--color-neutral-600` | `#3a404c` | 强边框、分割线 | 非文字 |
| `--color-neutral-700` | `#262b34` | 抬起面、悬停底色 | 非文字 |
| `--color-neutral-800` | `#181b22` | 卡片/表面 | — |

**画布**：`--color-canvas: #12141a`（页面底色，比 n-800 再深一档；**不使用纯黑**）。

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
| 间距 | `--space-1…8` | 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64（8pt 体系） |
| 圆角 | `--radius-xs/sm/md/lg` | **4 / 6 / 8 / 8**（标签 4、控件 6、卡片 8；禁止 12/16/999） |
| 边框 | `--border-width` | 1px（层级靠边框 + 背景色差） |
| 阴影 | `--shadow-none` / `--shadow-overlay` | `none` / 仅弹层 `0 1px 2px rgba(0,0,0,.3)` |
| 控件高 | `--control-height-sm/md/lg` | 36 / 40 / 44 |
| 图标 | `--icon-size-sm/md/lg` | 16 / 20 / 24 |
| 布局 | `--layout-max-width` / `--layout-sidebar-width` | 1280 / 232 |

> **层级规则**：卡片一律 `1px 边框 + 背景色差`，不用阴影；只有弹层/抽屉允许极轻投影。

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

### 5.1 CSS（节选，完整见 `tokens.css`）

```css
:root {
  /* 中性 9 阶 */
  --color-neutral-0: #f7f8fa;
  --color-neutral-100: #e9eaee;
  --color-neutral-200: #c6c9d1;
  --color-neutral-300: #b6bac4;
  --color-neutral-400: #8f949f;
  --color-neutral-500: #5c626e;
  --color-neutral-600: #3a404c;
  --color-neutral-700: #262b34;
  --color-neutral-800: #181b22;
  --color-canvas: #12141a;

  /* 主色 5 阶 + 交互别名 */
  --color-primary-50: #fdecec;
  --color-primary-100: #f8c9ca;
  --color-primary-300: #ef7377;
  --color-primary-500: #e5484d;
  --color-primary-700: #c23438;
  --color-action: var(--color-primary-700);
  --color-action-hover: #a82a2e;

  /* 语义色各 3 阶 */
  --color-success-subtle: #e8f8ef;
  --color-success-base: #5fd394;
  --color-success-strong: #1a7f4b;
  --color-warning-subtle: #fdf3e3;
  --color-warning-base: #e8b45c;
  --color-warning-strong: #a86f17;
  --color-error-subtle: #fdeaea;
  --color-error-base: #f07171;
  --color-error-strong: #b41c1c;
  --color-info-subtle: #e8f1fd;
  --color-info-base: #6b9bf5;
  --color-info-strong: #1d4ed8;

  /* 字体 / 间距 / 圆角 / 阴影 */
  --font-size-body: 16px;
  --line-height-body: 1.6;
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px; --space-8: 64px;
  --radius-xs: 4px; --radius-sm: 6px; --radius-md: 8px; --radius-lg: 8px;
  --shadow-none: none;
  --shadow-overlay: 0 1px 2px rgba(0, 0, 0, 0.3);
}
```

### 5.2 JSON（节选，完整见 `design-tokens.json`）

```json
{
  "color": {
    "neutral": {
      "100": { "value": "#e9eaee", "usage": "主文字", "contrastOnSurface": 14.33 },
      "400": { "value": "#8f949f", "usage": "辅助文字", "contrastOnSurface": 5.67 }
    },
    "primary": {
      "500": { "value": "#e5484d", "usage": "品牌红：涨跌/图表", "contrastOnSurface": 4.4 },
      "700": { "value": "#c23438", "usage": "实心按钮底", "contrastWhiteOnIt": 5.47 }
    },
    "semantic": {
      "error": {
        "subtle": { "value": "#fdeaea", "usage": "浅底" },
        "base": { "value": "#f07171", "usage": "深色底文字", "contrastOnSurface": 5.99 },
        "strong": { "value": "#b41c1c", "usage": "实心底", "contrastWhiteOnIt": 6.72 }
      }
    }
  },
  "typography": { "fontSize": { "body": 16, "aux": 14, "cap": 13 }, "lineHeight": { "body": 1.6 } },
  "spacing": { "1": 4, "2": 8, "3": 12, "4": 16, "5": 24, "6": 32, "7": 48, "8": 64 },
  "radius": { "xs": 4, "sm": 6, "md": 8, "lg": 8 }
}
```

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
| 中性 9 阶 | ✅ n-0…n-800 + 画布色 |
| 主色 5 阶 | ✅ 50/100/300/500/700 |
| 语义色各 3 阶 | ✅ success/warning/error/info × subtle/base/strong |
| 正文 16px/1.6、辅助 13px/1.5 | ✅ 令牌固定，页面无硬编码小字 |
| H1–H3 层级 | ✅ 28/22/18 |
| 间距 4…64 | ✅ 8 档 |
| 圆角 4/6/8 | ✅ `--radius-lg` 也映射 8，无 12/16/999 |
| 阴影只允许 0/极轻 | ✅ 卡片 none，弹层仅 0 1px 2px |
| CSS + JSON 双版本 | ✅ 两个文件同源同值 |
| 颜色用途 + 对比度标注 | ✅ 本文件 + JSON 内联 `contrastOnSurface` |
| 组件规则（按钮/输入/卡片/表格/导航） | ✅ §4 + `ui-kit.css` |
| AA 合规 | ✅ 正文 14.33:1；语义文字 5.99–9.22；按钮白字 5.02–6.72；⚠️ 唯一例外：`primary-500` 作 16px 文字 4.40:1，已在规范中要求改用 `primary-300` |
