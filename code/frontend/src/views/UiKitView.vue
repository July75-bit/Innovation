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
import { computed, ref } from 'vue'

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
</style>
