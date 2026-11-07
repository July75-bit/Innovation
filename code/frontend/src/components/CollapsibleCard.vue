<script setup lang="ts">
/**
 * 白话导读：可展开/收起的卡片（浏览器原生 <details>/<summary>，一行 JS 都没有）。
 * 用在"想细看才点开"的信息上，比如 AI 建议的理由、价格变动说明。
 * <slot /> 是内容口子、<slot name="meta" /> 是标题右侧的小口子，
 * 父组件往里塞什么就显示什么——这叫插槽(slot)，是 Vue 复用外壳的常用手法。
 */
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