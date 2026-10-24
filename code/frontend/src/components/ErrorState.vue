<script setup lang="ts">
/**
 * 错误态：展示后端中文 message（契约 §2，不写映射表）+ 重试按钮。
 * 重试只是重新拉取，绝不自动重放交易请求（契约 §4.7：重试=第二笔真实交易）。
 */
defineProps<{ message: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="state error">
    <span>{{ message }}</span>
    <button @click="emit('retry')">重试</button>
    <slot />
  </div>
</template>

<style scoped>
.state {
  padding: 24px 0;
  display: flex;
  gap: 12px;
  align-items: center;
}
.error {
  color: var(--up);
}
button {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}
</style>
