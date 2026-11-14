<script setup lang="ts">
/**
 * UiTable —— 数据表格。
 *
 * 规范：表头浅底 13px、行下边框 1px、悬停浅底、数字列右对齐 tabular-nums；
 * 状态：loading（骨架行）、empty（空态文案）、error（错误 + 重试）。
 * 排序：列可排序时表头是按钮，点击 emit('sort')。
 */
export interface UiTableColumn {
  key: string
  label: string
  align?: 'left' | 'right' | 'center'
  sortable?: boolean
  width?: string
}

const props = withDefaults(
  defineProps<{
    columns: UiTableColumn[]
    rows: Record<string, unknown>[]
    rowKey?: string
    loading?: boolean
    error?: string
    emptyText?: string
    sortKey?: string
    sortDir?: 'asc' | 'desc'
    /** 加载时骨架行数 */
    skeletonRows?: number
    /** 表头吸顶（长表格用；滚动容器内生效） */
    stickyHeader?: boolean
  }>(),
  { rowKey: 'id', loading: false, emptyText: '暂无数据', skeletonRows: 5, stickyHeader: false },
)

const emit = defineEmits<{
  sort: [payload: { key: string; dir: 'asc' | 'desc' }]
  retry: []
  rowClick: [row: Record<string, unknown>]
}>()

function onSort(column: UiTableColumn) {
  if (!column.sortable) return
  const dir: 'asc' | 'desc' = props.sortKey === column.key && props.sortDir === 'asc' ? 'desc' : 'asc'
  emit('sort', { key: column.key, dir })
}

function cellValue(row: Record<string, unknown>, key: string): string {
  const value = row[key]
  return value === null || value === undefined ? '—' : String(value)
}
</script>

<template>
  <div :class="['ui-table-wrap', { 'is-sticky-head': stickyHeader }]">
    <table class="ui-table">
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :style="column.width ? { width: column.width } : undefined"
            :class="[column.align === 'right' ? 'is-num' : '', column.align === 'center' ? 'is-center' : '']"
            :aria-sort="
              column.sortable
                ? sortKey === column.key
                  ? sortDir === 'asc'
                    ? 'ascending'
                    : 'descending'
                  : 'none'
                : undefined
            "
          >
            <button
              v-if="column.sortable"
              type="button"
              class="ui-table__sort"
              @click="onSort(column)"
            >
              {{ column.label }}
              <span class="ui-table__chev" aria-hidden="true">
                {{ sortKey === column.key ? (sortDir === 'asc' ? '▲' : '▼') : '↕' }}
              </span>
            </button>
            <template v-else>{{ column.label }}</template>
          </th>
        </tr>
      </thead>

      <tbody v-if="loading">
        <tr v-for="n in skeletonRows" :key="`sk-${n}`" class="is-skeleton">
          <td v-for="column in columns" :key="column.key">
            <span class="ui-table__bar" />
          </td>
        </tr>
      </tbody>

      <tbody v-else-if="error">
        <tr>
          <td :colspan="columns.length" class="ui-table__state">
            <p class="ui-error">{{ error }}</p>
            <button type="button" class="ui-btn ui-btn--secondary ui-btn--sm" @click="emit('retry')">
              重试
            </button>
          </td>
        </tr>
      </tbody>

      <tbody v-else-if="!rows.length">
        <tr>
          <td :colspan="columns.length" class="ui-table__state ui-table__empty">
            {{ emptyText }}
          </td>
        </tr>
      </tbody>

      <tbody v-else>
        <tr
          v-for="(row, index) in rows"
          :key="String(row[rowKey] ?? index)"
          @click="emit('rowClick', row)"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            :class="[column.align === 'right' ? 'is-num' : '', column.align === 'center' ? 'is-center' : '']"
          >
            <slot :name="`cell-${column.key}`" :row="row">{{ cellValue(row, column.key) }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.ui-table-wrap {
  width: 100%;
  overflow-x: auto;
}
.ui-table__sort {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}
.ui-table__sort:hover {
  color: var(--color-text);
}
.ui-table__sort:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
  border-radius: var(--radius-xs);
}
.ui-table__chev {
  font-size: 10px;
  color: var(--color-text-faint);
}
.is-center {
  text-align: center;
}
.ui-table__state {
  padding: var(--space-8) var(--space-4);
  text-align: center;
  color: var(--color-text-muted);
}
.ui-table__empty {
  color: var(--color-text-faint);
}
.ui-table__bar {
  display: block;
  height: 12px;
  width: 70%;
  border-radius: var(--radius-xs);
  background: var(--color-surface-raised);
}
.is-skeleton td {
  padding: var(--space-3) var(--space-4);
}

/* 表头吸顶：表头实色（内容层，绝不用玻璃，避免长表格大面积透明） */
.ui-table-wrap.is-sticky-head {
  max-height: 520px;
  overflow: auto;
}
.ui-table-wrap.is-sticky-head thead th {
  position: sticky;
  top: 0;
  z-index: 1;
}
</style>
