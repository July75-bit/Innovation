<script setup lang="ts">
/**
 * UiPagination —— 分页条。
 *
 * 规范：按钮高度 36，圆角 6；当前页实色主色；禁用态不可点；
 * 无障碍：nav + aria-label，当前页 aria-current="page"。
 */
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    page: number
    pageSize: number
    total: number
    /** 左右各显示几个页码（中间用省略号） */
    siblings?: number
  }>(),
  { siblings: 1 },
)

const emit = defineEmits<{ 'update:page': [page: number] }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

/** 生成页码序列：1 … 4 5 6 … 20 */
const pageItems = computed<Array<number | 'gap'>>(() => {
  const last = totalPages.value
  const current = props.page
  const span = props.siblings * 2 + 5 // 首尾 + 当前 + 左右兄弟 + 两个省略号
  if (last <= span) return Array.from({ length: last }, (_, i) => i + 1)

  const left = Math.max(2, current - props.siblings)
  const right = Math.min(last - 1, current + props.siblings)
  const items: Array<number | 'gap'> = [1]
  if (left > 2) items.push('gap')
  for (let i = left; i <= right; i += 1) items.push(i)
  if (right < last - 1) items.push('gap')
  items.push(last)
  return items
})

const canPrev = computed(() => props.page > 1)
const canNext = computed(() => props.page < totalPages.value)
const rangeText = computed(() => {
  if (props.total === 0) return '共 0 条'
  const from = (props.page - 1) * props.pageSize + 1
  const to = Math.min(props.page * props.pageSize, props.total)
  return `第 ${from}–${to} 条，共 ${props.total} 条`
})

function go(page: number) {
  const next = Math.min(Math.max(1, page), totalPages.value)
  if (next !== props.page) emit('update:page', next)
}
</script>

<template>
  <nav class="ui-pagination" aria-label="分页">
    <span class="ui-pagination__range">{{ rangeText }}</span>
    <div class="ui-pagination__pages">
      <button
        type="button"
        class="ui-pagination__btn"
        :disabled="!canPrev"
        aria-label="上一页"
        @click="go(page - 1)"
      >
        ‹
      </button>
      <template v-for="(item, index) in pageItems" :key="index">
        <span v-if="item === 'gap'" class="ui-pagination__gap" aria-hidden="true">…</span>
        <button
          v-else
          type="button"
          class="ui-pagination__btn"
          :class="{ 'is-current': item === page }"
          :aria-current="item === page ? 'page' : undefined"
          @click="go(item)"
        >
          {{ item }}
        </button>
      </template>
      <button
        type="button"
        class="ui-pagination__btn"
        :disabled="!canNext"
        aria-label="下一页"
        @click="go(page + 1)"
      >
        ›
      </button>
    </div>
  </nav>
</template>

<style scoped>
.ui-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.ui-pagination__range {
  font-size: var(--font-size-cap);
  color: var(--color-text-muted);
}
.ui-pagination__pages {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}
.ui-pagination__btn {
  min-width: var(--control-height-sm);
  height: var(--control-height-sm);
  padding: 0 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: var(--font-size-aux);
  font-variant-numeric: tabular-nums;
  cursor: pointer;
}
.ui-pagination__btn:hover:not(:disabled) {
  color: var(--color-text);
  border-color: var(--color-border-strong);
  background: var(--color-surface-raised);
}
.ui-pagination__btn:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
.ui-pagination__btn:disabled {
  opacity: 0.45;
  cursor: default;
}
.ui-pagination__btn.is-current {
  background: var(--color-action);
  border-color: var(--color-action);
  color: var(--color-action-text);
  font-weight: var(--font-weight-semibold);
}
.ui-pagination__gap {
  padding: 0 4px;
  color: var(--color-text-faint);
}
</style>
