<script setup lang="ts">
/**
 * UI 组件库预览页（/ui-kit）
 *
 * 用途：
 * 1) 答辩/评审时一屏看到全部组件与状态；
 * 2) 改 tokens 后回来检查有没有视觉回归；
 * 3) 给后续开发者的"照抄样例"。
 *
 * 该页不在主导航中，直接用地址访问；不影响业务页面。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import UiButton from '../components/ui/UiButton.vue'
import UiCard from '../components/ui/UiCard.vue'
import UiInput from '../components/ui/UiInput.vue'
import UiModal from '../components/ui/UiModal.vue'
import UiNav from '../components/ui/UiNav.vue'
import UiNavItem from '../components/ui/UiNavItem.vue'
import UiPagination from '../components/ui/UiPagination.vue'
import UiSelect from '../components/ui/UiSelect.vue'
import UiTable from '../components/ui/UiTable.vue'
import UiTag from '../components/ui/UiTag.vue'
import type { UiTableColumn } from '../components/ui/UiTable.vue'

/* ---------- 输入 / 下拉 ---------- */
const quantity = ref<string | number>(2)
const role = ref<string | number>('awper')
const badQty = ref<string | number>('abc')

const roleOptions = [
  { label: '狙击手（AWPer）', value: 'awper' },
  { label: '步枪手（Rifler）', value: 'rifler' },
  { label: '指挥（IGL）', value: 'igl' },
]

/* ---------- 弹窗 ---------- */
const modalOpen = ref(false)

/* ---------- 表格 ---------- */
const columns: UiTableColumn[] = [
  { key: 'name', label: '选手', sortable: true },
  { key: 'team', label: '战队' },
  { key: 'price', label: '现价', align: 'right', sortable: true },
  { key: 'change', label: '涨跌', align: 'right' },
]

const rows = [
  { id: 1, name: 'ZywOo', team: 'Vitality', price: '89.13', change: '-10.12%', up: false },
  { id: 2, name: 'donk', team: 'Spirit', price: '126.44', change: '-3.57%', up: false },
  { id: 3, name: 'sh1ro', team: 'Spirit', price: '136.43', change: '+13.96%', up: true },
]
const sortKey = ref('name')
const sortDir = ref<'asc' | 'desc'>('asc')
const tableLoading = ref(false)
const tableError = ref('')
const tableRows = computed(() => (tableError.value ? [] : rows))

function onSort(payload: { key: string; dir: 'asc' | 'desc' }) {
  sortKey.value = payload.key
  sortDir.value = payload.dir
}

/* ---------- 分页 ---------- */
const page = ref(3)
const pageSize = 10
const total = 96

/* ---------- 导航 ---------- */
const activeNav = ref('market')

/* ---------- 液态玻璃（材质层）演示 ---------- */
/** 降级开关：给 <html> 加 no-backdrop-filter，模拟"浏览器不支持 backdrop-filter" */
const fallbackOn = ref(false)
/** 当前视口内玻璃面积占比（%），用来守 30% 配额 */
const glassQuota = ref('—')

function toggleFallback(): void {
  fallbackOn.value = !fallbackOn.value
  document.documentElement.classList.toggle('no-backdrop-filter', fallbackOn.value)
}

function measureGlass(): void {
  if (typeof document === 'undefined') return
  const vw = window.innerWidth
  const vh = window.innerHeight
  let area = 0
  document.querySelectorAll<HTMLElement>('.glass').forEach((el) => {
    const r = el.getBoundingClientRect()
    const w = Math.min(r.right, vw) - Math.max(r.left, 0)
    const h = Math.min(r.bottom, vh) - Math.max(r.top, 0)
    if (w > 0 && h > 0) area += w * h
  })
  glassQuota.value = ((area / (vw * vh)) * 100).toFixed(1)
}

onMounted(() => {
  measureGlass()
  window.addEventListener('resize', measureGlass)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', measureGlass)
  document.documentElement.classList.remove('no-backdrop-filter')
  delete document.documentElement.dataset.theme
})

/** 浅色模式开关：只改 <html data-theme>，令牌全量切换（离开本页恢复深色） */
const themeLight = ref(false)
function toggleTheme(): void {
  themeLight.value = !themeLight.value
  if (themeLight.value) document.documentElement.dataset.theme = 'light'
  else delete document.documentElement.dataset.theme
}
</script>

<template>
  <div class="kit">
    <header class="kit__head">
      <h1>UI 组件库</h1>
      <p class="kit__sub">
        扁平化 · 产品化 · 高可读性｜令牌见 <code>src/assets/tokens.css</code>，规则见
        <code>docs/software/ui_components.md</code>
      </p>
    </header>

    <!-- 按钮 -->
    <section class="kit__section">
      <h2>按钮 Button</h2>
      <p class="kit__note">高度 44/40/36，圆角 6，1px 边框或实色；无阴影。</p>
      <div class="kit__row">
        <UiButton variant="primary">买入 2 股</UiButton>
        <UiButton variant="secondary">重新分析</UiButton>
        <UiButton variant="danger">删除账号</UiButton>
        <UiButton variant="ghost">忽略</UiButton>
      </div>
      <div class="kit__row">
        <UiButton variant="secondary" size="sm">小号 36</UiButton>
        <UiButton variant="secondary">中号 40</UiButton>
        <UiButton variant="primary">大号 44</UiButton>
        <UiButton variant="primary" loading>提交中…</UiButton>
        <UiButton variant="secondary" disabled>已禁用</UiButton>
      </div>
    </section>

    <!-- 输入 / 下拉 -->
    <section class="kit__section">
      <h2>输入框 / 下拉</h2>
      <p class="kit__note">标签在上、提示在下；错误信息紧贴字段（13px）。</p>
      <div class="kit__grid">
        <UiInput v-model="quantity" label="数量" hint="1–50 股，按 Enter 直接买入" suffix="股" />
        <UiInput
          v-model="badQty"
          label="数量（错误示例）"
          error="数量必须是正整数（1–50 股）"
          type="text"
        />
        <UiInput v-model="quantity" label="禁用态" disabled hint="当前选手暂停交易" />
        <UiSelect
          v-model="role"
          label="位置筛选"
          :options="roleOptions"
          hint="选择后立即生效"
        />
      </div>
    </section>

    <!-- 标签 -->
    <section class="kit__section">
      <h2>标签 Tag</h2>
      <p class="kit__note">状态必须带文字，不能只靠颜色区分。</p>
      <div class="kit__row">
        <UiTag>默认</UiTag>
        <UiTag tone="success">交易中</UiTag>
        <UiTag tone="warning">暂停交易</UiTag>
        <UiTag tone="error">余额不足</UiTag>
        <UiTag tone="info">模拟数据</UiTag>
      </div>
    </section>

    <!-- 卡片 -->
    <section class="kit__section">
      <h2>卡片 Card</h2>
      <div class="kit__grid">
        <UiCard title="ZywOo" meta="Vitality · AWPer">
          <p class="kit__price">89.13</p>
          <p class="kit__change is-down">-10.12%</p>
        </UiCard>
        <UiCard title="可点击卡片" meta="悬停只提亮边框" interactive>
          <p class="kit__note">不位移、不放大、不加阴影。</p>
        </UiCard>
        <UiCard title="选中态" meta="左侧 2px 主色竖条" selected>
          <p class="kit__note">用于列表里"当前选中项"。</p>
        </UiCard>
      </div>
    </section>

    <!-- 表格 -->
    <section class="kit__section">
      <h2>表格 Table</h2>
      <div class="kit__row">
        <UiButton size="sm" variant="secondary" @click="tableLoading = !tableLoading">
          {{ tableLoading ? '结束加载' : '模拟加载' }}
        </UiButton>
        <UiButton size="sm" variant="secondary" @click="tableError = tableError ? '' : '数据加载失败，请重试'">
          {{ tableError ? '清除错误' : '模拟错误' }}
        </UiButton>
      </div>
      <UiTable
        :columns="columns"
        :rows="tableRows"
        :loading="tableLoading"
        :error="tableError"
        :sort-key="sortKey"
        :sort-dir="sortDir"
        empty-text="还没有数据，去市场挑一个选手"
        row-key="id"
        @sort="onSort"
        @retry="tableError = ''"
      >
        <template #cell-change="{ row }">
          <span :class="row.up ? 'is-up' : 'is-down'">{{ row.change }}</span>
        </template>
      </UiTable>
      <UiPagination v-model:page="page" :page-size="pageSize" :total="total" />
    </section>

    <!-- 导航 -->
    <section class="kit__section">
      <h2>导航 Nav</h2>
      <p class="kit__note">选中态 = 中性高亮 + 左侧主色竖条（红色留给主 CTA）。</p>
      <UiNav>
        <UiNavItem href="#market" :active="activeNav === 'market'" @click.prevent="activeNav = 'market'">
          市场
        </UiNavItem>
        <UiNavItem href="#positions" :active="activeNav === 'positions'" @click.prevent="activeNav = 'positions'">
          持仓
        </UiNavItem>
        <UiNavItem href="#disabled" disabled>赛程（不可用）</UiNavItem>
      </UiNav>
    </section>

    <!-- 弹窗 -->
    <section class="kit__section">
      <h2>弹窗 Modal</h2>
      <UiButton variant="danger" @click="modalOpen = true">打开删除确认</UiButton>
      <UiModal v-model:open="modalOpen" title="确认删除账号？" size="sm" :dismissible="false">
        <p>删除后持仓、流水与令牌会一并清除，且无法恢复。</p>
        <template #footer>
          <UiButton variant="secondary" @click="modalOpen = false">取消</UiButton>
          <UiButton variant="danger" @click="modalOpen = false">确认删除</UiButton>
        </template>
      </UiModal>
    </section>

    <!-- 液态玻璃材质层 -->
    <section id="liquid-glass" class="kit__section">
      <h2>液态玻璃材质层 Liquid Glass</h2>
      <p class="kit__note">
        只有<strong>材质层</strong>用玻璃：导航壳 / 底部工具条 / 弹窗 / Popover。
        内容层（正文、表格、表单、长文）保持实色扁平，永远不加玻璃。
        配额：同屏玻璃面积 ≤ 30%，本页实测
        <strong data-testid="glass-quota">{{ glassQuota }}%</strong>（演示页同时展示多块材质，配额会高于业务页）。
      </p>

      <div class="kit__row">
        <UiButton variant="secondary" @click="toggleFallback">
          {{ fallbackOn ? '恢复玻璃（backdrop-filter）' : '模拟降级（不支持 backdrop-filter）' }}
        </UiButton>
        <UiButton variant="secondary" @click="measureGlass">重新测量玻璃面积</UiButton>
        <UiButton variant="secondary" @click="toggleTheme">
          {{ themeLight ? '切回深色模式' : '切浅色模式（验收用）' }}
        </UiButton>
      </div>

      <!-- ① 导航壳（玻璃，文字坐在 scrim 上） -->
      <div class="glass-demo glass glass--nav glass--interactive" data-testid="glass-nav">
        <span class="glass-demo__brand">PlayerStock</span>
        <nav class="glass-demo__nav" aria-label="玻璃导航示例">
          <a href="#liquid-glass" class="is-active">市场</a>
          <a href="#liquid-glass">持仓</a>
          <a href="#liquid-glass">流水</a>
        </nav>
        <span class="glass-demo__meta">余额 5000.00</span>
      </div>

      <!-- ② 悬浮工具条（玻璃，圆角 12） -->
      <div class="glass-toolbar glass glass--control glass--interactive" data-testid="glass-toolbar">
        <span class="glass-toolbar__hint">ZywOo · 108.75 · +2.1%</span>
        <UiButton variant="primary" size="sm">买入 2 股</UiButton>
        <UiButton variant="secondary" size="sm">重新分析</UiButton>
        <UiButton variant="ghost" size="sm">忽略</UiButton>
      </div>

      <!-- ③ Popover 浮层（玻璃，圆角 20，极轻投影） -->
      <div class="glass-popover glass glass--panel glass--interactive" data-testid="glass-popover">
        <p class="glass-popover__label">今日最该看一眼</p>
        <p class="glass-popover__value">sh1ro +13.96%</p>
        <p class="glass-popover__hint">现价 136.43 · 评分 88</p>
      </div>

      <!-- ④ 浅色模式玻璃（data-theme="light" 是全局令牌开关；业务页默认深色，这里做材质对照） -->
      <div class="light-island" data-theme="light" data-testid="glass-light">
        <div class="glass glass--panel glass--interactive light-island__panel">
          <p class="light-island__title">浅色玻璃 · 同一套令牌</p>
          <p class="light-island__body">
            玻璃底 rgba(255,255,255,.62)，边框 .72，可读性 scrim .72，模糊 22px；正文 16px /
            1.6，对比度按 AA 校验。
          </p>
          <!-- 玻璃下面再放内容一律实色：这里是最多"玻璃 + 实色"两层，禁止玻璃叠玻璃 -->
          <div class="light-island__card">
            <strong>实色内容卡</strong>
            <span>表格与表单永远住在这种实色表面上</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.kit {
  max-width: var(--layout-content-max);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.kit__head h1 {
  font-size: var(--font-size-h1);
}
.kit__sub,
.kit__note {
  color: var(--color-text-muted);
  font-size: var(--font-size-aux);
  line-height: var(--line-height-aux);
  margin: var(--space-1) 0 0;
}
.kit__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-border);
}
/* 按钮不被 flex 列拉伸（否则「打开删除确认」会占满整行） */
.kit__section > .ui-btn {
  align-self: flex-start;
}
.kit__section h2 {
  font-size: var(--font-size-h2);
  font-weight: var(--font-weight-semibold);
}
.kit__row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.kit__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--space-4);
}
.kit__price {
  margin: 0;
  font-size: var(--font-size-h2);
  font-weight: var(--font-weight-semibold);
  font-variant-numeric: tabular-nums;
}
.kit__change {
  margin: var(--space-1) 0 0;
  font-size: var(--font-size-aux);
  font-variant-numeric: tabular-nums;
}
.is-up {
  color: var(--color-up-text);
}
.is-down {
  color: var(--color-down);
}

/* ===== 液态玻璃演示（仅在 /ui-kit 出现，业务页不要照抄这些 demo 类名） ===== */
.glass-demo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--glass-radius-control);
}
.glass-demo__brand {
  font-weight: var(--font-weight-bold);
  color: var(--color-text-strong);
}
.glass-demo__nav {
  display: flex;
  gap: var(--space-1);
  margin-left: auto;
}
.glass-demo__nav a {
  display: inline-flex;
  align-items: center;
  min-height: 44px; /* 点击区域 ≥44px */
  padding: 0 var(--space-3);
  border-radius: var(--glass-radius-control);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: var(--font-size-aux);
}
.glass-demo__nav a:hover {
  color: var(--color-text-strong);
  background: var(--color-surface-raised);
}
.glass-demo__nav a.is-active {
  color: var(--color-text-strong);
  background: var(--color-surface-raised);
  box-shadow: inset 2px 0 0 var(--color-primary-500);
}
.glass-demo__nav a:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
.glass-demo__meta {
  margin-left: auto;
  font-size: var(--font-size-cap);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.glass-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  padding: var(--space-2) var(--space-3);
}
.glass-toolbar__hint {
  margin-right: auto;
  font-size: var(--font-size-aux);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

.glass-popover {
  width: min(280px, 100%);
  padding: var(--space-4);
}
.glass-popover__label {
  margin: 0;
  font-size: var(--font-size-cap);
  color: var(--color-text-muted);
}
.glass-popover__value {
  margin: var(--space-1) 0 0;
  font-size: var(--font-size-h3);
  font-weight: var(--font-weight-semibold);
  color: var(--color-up-text);
  font-variant-numeric: tabular-nums;
}
.glass-popover__hint {
  margin: var(--space-1) 0 0;
  font-size: var(--font-size-cap);
  color: var(--color-text-muted);
}

/* 浅色玻璃对照区：自带浅色画布，避免和深色业务页混在一起看不出对比 */
.light-island {
  background: var(--color-canvas);
  border-radius: var(--glass-radius-panel);
  padding: var(--space-5);
}
.light-island__panel {
  padding: var(--space-4);
}
.light-island__title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-h3);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-strong);
}
.light-island__body {
  margin: 0 0 var(--space-3);
  font-size: var(--font-size-body);
  line-height: var(--line-height-body);
  color: var(--color-text);
}
.light-island__card {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--font-size-aux);
}
</style>
