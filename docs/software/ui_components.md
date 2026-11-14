# UI 组件库（Vue 3 + TS）

> **预览页**：`/ui-kit`（免登录直达，不在主导航里）
> **代码**：`code/frontend/src/components/ui/*.vue` ｜ **样式基座**：`src/assets/{tokens.css,ui-kit.css}`
> **测试**：`src/components/ui/__tests__/ui-kit.spec.ts`（15 条状态测试）
> **规范依据**：[`design_tokens.md`](design_tokens.md) · [`ui_design_system.md`](ui_design_system.md)

## 0. 组件清单

| 组件 | 文件 | 用途 |
| --- | --- | --- |
| `UiButton` | `UiButton.vue` | 主/次/危险/文字按钮，四种尺寸态 |
| `UiInput` | `UiInput.vue` | 带标签、提示、错误、后缀单位的输入框 |
| `UiSelect` | `UiSelect.vue` | 原生下拉封装（可访问性最好） |
| `UiTag` | `UiTag.vue` | 状态标签 / 徽章（5 种语义色） |
| `UiCard` | `UiCard.vue` | 卡片（默认 / 可点击 / 选中） |
| `UiTable` | `UiTable.vue` | 表格（排序 / 加载骨架 / 空态 / 错误重试） |
| `UiPagination` | `UiPagination.vue` | 分页条（页码省略、当前页、范围文案） |
| `UiModal` | `UiModal.vue` | 弹窗（Esc / 遮罩关闭、滚动锁定、焦点进入） |
| `UiNav` + `UiNavItem` | 同名文件 | 导航容器与条目（选中态主色竖条） |

统一约定：高度 **36 / 40 / 44**、圆角 **6**、图标 **16 / 20**、正文 **16px**、
1px 边框、**无阴影无渐变**；颜色只用语义令牌（`--color-*`）。

---

## 1. 使用示例

### 按钮

```vue
<UiButton variant="primary" @click="submit">买入 2 股</UiButton>
<UiButton variant="secondary" size="sm">重新分析</UiButton>
<UiButton variant="danger" :loading="deleting" @click="remove">删除账号</UiButton>
<UiButton variant="ghost" :disabled="true">忽略</UiButton>
```

| Prop | 取值 | 默认 | 说明 |
| --- | --- | --- | --- |
| `variant` | `primary` / `secondary` / `danger` / `ghost` | `secondary` | 主按钮全站唯一实色 |
| `size` | `sm`(36) / `md`(40) / `lg`(44) | `md` | `primary` 默认 44 |
| `loading` / `disabled` | boolean | false | loading 时自动禁用 + `aria-busy` |
| `block` | boolean | false | 撑满父容器（移动端主按钮） |

### 输入框 / 下拉

```vue
<UiInput v-model="qty" label="数量" hint="1–50 股" suffix="股" :error="qtyError" />
<UiSelect v-model="role" label="位置" :options="roleOptions" />
```

| Prop | 说明 |
| --- | --- |
| `label`（必填） | 与控件 `for/id` 关联 |
| `hint` / `error` | 二者互斥：有 `error` 时显示错误（红）并设置 `aria-invalid` |
| `suffix` | 单位后缀（如「股」），不参与输入值 |
| `disabled` / `required` | 原生语义，必填带 `*` |

### 标签

```vue
<UiTag tone="success">交易中</UiTag>
<UiTag tone="warning">暂停交易</UiTag>
<UiTag tone="error">余额不足</UiTag>
```

### 卡片

```vue
<UiCard title="ZywOo" meta="Vitality · AWPer">…</UiCard>
<UiCard title="可点击" interactive @click="pick">…</UiCard>
<UiCard title="选中" selected>…</UiCard>
```

### 表格 + 分页

```vue
<UiTable
  :columns="columns" :rows="rows" row-key="id"
  :loading="loading" :error="error" empty-text="还没有数据"
  :sort-key="sortKey" :sort-dir="sortDir"
  @sort="onSort" @retry="load" @row-click="open"
>
  <template #cell-change="{ row }">
    <span :class="row.up ? 'is-up' : 'is-down'">{{ row.change }}</span>
  </template>
</UiTable>

<UiPagination v-model:page="page" :page-size="10" :total="96" />
```

| 状态 | 呈现 |
| --- | --- |
| loading | 5 行骨架条（不整页闪白） |
| empty | 居中空态文案（可带引导） |
| error | 行内错误 + 重试按钮（不自动重放写操作） |
| 排序 | 表头按钮切换 asc/desc，`aria-sort` 同步 |

### 弹窗

```vue
<UiModal v-model:open="open" title="确认删除账号？" size="sm" :dismissible="false">
  <p>删除后无法恢复。</p>
  <template #footer>
    <UiButton variant="secondary" @click="open = false">取消</UiButton>
    <UiButton variant="danger" @click="confirm">确认删除</UiButton>
  </template>
</UiModal>
```

| 行为 | 说明 |
| --- | --- |
| Esc / 点遮罩 | `dismissible=true`（默认）时关闭；危险确认传 `false` |
| 滚动 | 打开时锁定 `body` 滚动，关闭恢复 |
| 焦点 | 打开后焦点移入面板；关闭按钮有 `aria-label` |
| 图标 | 危险确认弹窗**不放 ✕**（强制用户明确选择） |

### 导航

```vue
<UiNav>
  <UiNavItem href="/" :active="route.path === '/'" @click.prevent="go('/')">市场</UiNavItem>
  <UiNavItem href="/positions" :active="route.path === '/positions'">持仓</UiNavItem>
  <UiNavItem disabled>赛程（不可用）</UiNavItem>
</UiNav>
```

---

## 2. 状态矩阵（每个组件都必须覆盖）

| 组件 | 默认 | hover | focus | active | disabled | loading | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Button | ✅ | 背景/边框变化 | 2px 主色环 | 下沉 1px | 透明度 .55 | 转圈 + 禁用 | —（用 danger 变体） |
| Input | ✅ | 边框提亮 | 焦点环 + 主色边框 | — | 变灰 | — | 红边框 + 13px 原因 |
| Select | ✅ | 边框提亮 | 焦点环 | — | 变灰 | — | 红边框 + 原因 |
| Card | ✅ | 边框提亮 | 焦点环（可点击时） | — | — | — | — |
| Table | ✅ | 行悬停浅底 | 表头按钮焦点环 | — | — | 骨架行 | 错误行 + 重试 |
| Pagination | ✅ | 浅底 + 边框提亮 | 焦点环 | 当前页实色 | 首/尾页箭头禁用 | — | — |
| Modal | 遮罩 + 面板 | — | 面板焦点 + 关闭按钮焦点环 | — | — | — | — |
| Tag | ✅ | — | — | — | — | — | 用 `tone="error"` |
| Nav | ✅ | 浅底 | 焦点环 | 选中：浅底 + 主色竖条 | 透明度 .45 | — | — |

测试对应：`ui-kit.spec.ts` 逐项断言（禁用不触发点击、loading 转圈、错误 aria、排序事件、Esc 关闭等 15 条）。

---

## 3. 禁止用法（Anti-patterns）

| # | 禁止 | 原因 | 应该怎么做 |
| --- | --- | --- | --- |
| 1 | 给按钮/卡片加 `box-shadow`、渐变、发光 | 违反扁平化；层级会靠"光效"而不是结构 | 用 1px 边框 + 背景色差；弹层才允许 `--shadow-overlay` |
| 2 | 圆角用 10/12/16/999（胶囊） | 全站圆角不统一 | 只用 `--radius-xs/sm/md`（4/6/8） |
| 3 | 用 `#e5484d`（primary-500）写 16px 正文 | 对比度 4.40，低于 AA 4.5 | 文字用 `--color-primary-300`（6.06） |
| 4 | 绿色 `#2fbf71` 作按钮底 + 白字 | 对比度 2.38，普通文字不可读 | 实心用 `--color-success-strong` `#1a7f4b`（5.02） |
| 5 | 只用颜色表达状态（红点/绿点） | 色盲用户无法区分 | 颜色 + **文字**（`UiTag` 必须带文字） |
| 6 | 错误提示放在页面顶部或弹 alert | 离字段远，用户不知道错在哪 | 错误信息紧贴字段下方（`UiInput error`） |
| 7 | 按钮文案写「确定 / 提交 / 取消」 | 不知道会发什么 | 动词 + 对象：「买入 2 股」「确认删除」「取消编辑」 |
| 8 | loading 时仍可点击 | 重复提交（交易场景会下两单） | `loading` 自动禁用 + `aria-busy` |
| 9 | 弹窗关闭按钮藏在角落、或危险操作可一键误触 | 误操作不可恢复 | 危险弹窗 `dismissible=false`、按钮「取消」在左、「确认删除」在右且红色 |
| 10 | 表格数字列左对齐、不用等宽数字 | 价格/涨跌对不齐，扫读困难 | 右对齐 + `tabular-nums` |
| 11 | 分页只有上一页/下一页 | 96 条要翻 10 次 | 页码 + 省略号 + 范围文案 |
| 12 | 自绘下拉弹层（div 模拟 select） | 键盘/读屏支持差、易错位 | 用 `UiSelect`（原生 select 封装） |
| 13 | 在组件里写死颜色/字号（`#fff`、`14px`） | 换主题/改规范时全站失控 | 一律 `var(--color-*)` / `var(--font-size-*)` |
| 14 | 图标不成套（混用 emoji / 彩色图标 / 不同线宽） | 视觉噪、不产品化 | 统一线性 SVG，16/20，`stroke: currentColor` |

---

## 4. 接入与扩展

```ts
// 新页面直接用，不要另写一套颜色与圆角
import UiButton from '@/components/ui/UiButton.vue'
```

- 新增组件：先查 `tokens.css` 有没有需要的语义令牌；没有就**先加令牌**，不要在组件里硬编码。
- 新组件必须同时补：① 状态矩阵覆盖 ② `ui-kit.spec.ts` 一条测试 ③ `/ui-kit` 预览页一个示例。
- 改 tokens 后跑一次 `/ui-kit` 目检 + `npm run test:unit`，避免视觉回归。

## 5. 证据

| 证据 | 内容 |
| --- | --- |
| `evidence/53-ui-kit-full.png` | 组件库整页（按钮/输入/下拉/标签/卡片/表格/分页/导航/弹窗入口） |
| `evidence/54-ui-kit-modal.png` | 危险确认弹窗打开态（无 ✕、取消在左、红色确认） |
| `evidence/55-ui-kit-375.png` | 375px 移动端无横向滚动（375/375） |
| `ui-kit.spec.ts` | 15 条状态测试（Vitest） |
