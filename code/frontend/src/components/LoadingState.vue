<script setup lang="ts">
/** 加载态：所有列表/详情页共用（day1 T1 统一布局要求） */
</script>

<template>
  <p class="state" aria-live="polite">
    <span class="spinner" aria-hidden="true"></span><slot>加载中…</slot>
  </p>
</template>

<style scoped>
.state {
  color: var(--muted);
  padding: var(--space-6) 0;
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-aux);
}
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>