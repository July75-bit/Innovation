<script setup lang="ts">
/**
 * 白话导读：出错时的红色提示块 + "重试"按钮。
 * 要显示的文字直接来自后端返回的中文 message（父组件通过 props 传进来），前端不维护错误码对照表。
 * 点重试 = 重新发一次 GET 请求（只读、安全）；交易类请求失败绝不会自动重发。
 * 父组件通过 @retry="load" 监听这里 emit 的事件，决定重试具体做什么。
 */
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
    <p class="tip tip-alt">如果多次重试仍失败，可稍后再试，或换一个网络环境。</p>
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
  color: var(--up-text);
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
/* 备选办法提示：连续失败时用户知道还能做什么（H9 错误可恢复） */
.tip-alt {
  font-size: var(--fs-cap);
  opacity: 0.9;
}
button {
  padding: 6px 18px;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  background: var(--up-bg);
  color: var(--accent-text);
  font-size: var(--fs-body);
  font-weight: 600;
  cursor: pointer;
}
</style>