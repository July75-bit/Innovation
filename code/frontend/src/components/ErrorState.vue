<script setup lang="ts">
/**
 * 错误态（容错层）：展示后端中文 message（契约 §2，不写映射表）+ 重试按钮。
 * 重试只是重新拉取，绝不自动重放交易请求（契约 §4.7：重试=第二笔真实交易）。
 */
defineProps<{ message: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="state error" role="alert">
    <div class="err-main">
      <span class="err-ico" aria-hidden="true">!</span>
      <span class="err-msg">{{ message }}</span>
    </div>
    <p class="tip">数据未成功加载，你的账户与持仓不受影响，可点击重试。</p>
    <button @click="emit('retry')">重试</button>
    <slot />
  </div>
</template>

<style scoped>
.state {
  margin-top: var(--space-4);
  padding: var(--space-4) var(--space-5);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--up);
  border-radius: var(--radius-md);
}
.err-main {
  display: flex;
  align-items: center;
  gap: 10px;
}
.err-ico {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--up-bg);
  color: var(--up);
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-aux);
  flex-shrink: 0;
}
.err-msg {
  color: var(--text);
  font-size: var(--fs-body);
  font-weight: 600;
}
.tip {
  margin: 0;
  font-size: var(--fs-aux);
  color: var(--muted);
}
button {
  padding: 6px 18px;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  background: var(--up-bg);
  color: var(--accent);
  font-size: var(--fs-body);
  font-weight: 600;
  cursor: pointer;
}
</style>