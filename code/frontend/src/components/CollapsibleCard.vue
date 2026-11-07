<script setup lang="ts">
/**
 * 折叠卡片（统一组件）：标题 + 摘要行 + 可展开内容。
 * 用于 AI 建议、价格变动说明等"想细看才展开"的信息，
 * 让主任务流（看行情 → 交易）保持最短。
 */
withDefaults(
  defineProps<{
    title: string
    /** 默认是否展开 */
    open?: boolean
  }>(),
  { open: true },
)
</script>

<template>
  <details class="collapse" :open="open">
    <summary>
      <span class="chev" aria-hidden="true">▸</span>
      <span class="title">{{ title }}</span>
      <span class="meta"><slot name="meta" /></span>
    </summary>
    <div class="body">
      <slot />
    </div>
  </details>
</template>

<style scoped>
.collapse {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
}
summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--space-3, 12px) var(--space-4, 16px);
  cursor: pointer;
  list-style: none;
  user-select: none;
  font-size: var(--fs-h3);
  font-weight: 700;
}
summary::-webkit-details-marker {
  display: none;
}
.chev {
  color: var(--muted);
  transition: transform 0.15s ease;
  font-size: var(--fs-aux);
}
details[open] .chev {
  transform: rotate(90deg);
}
.title {
  color: var(--text);
}
.meta {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 400;
  font-size: var(--fs-cap);
  color: var(--muted);
}
.body {
  padding: 0 var(--space-4, 16px) var(--space-4, 16px);
  font-size: var(--fs-body);
}
</style>