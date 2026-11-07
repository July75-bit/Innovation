<script setup lang="ts">
/** 空态：图标 + 文案 + 可选引导（默认插槽放链接/按钮），避免"白屏像坏了" */
</script>

<template>
  <div class="state">
    <svg class="ico" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4M3 9l2-5h14l2 5v1H3V9Zm5 5h8" />
    </svg>
    <p class="msg"><slot>暂无数据</slot></p>
  </div>
</template>

<style scoped>
.state {
  padding: var(--space-6) 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  color: var(--muted);
  text-align: center;
}
.ico {
  width: 34px;
  height: 34px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.4;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0.6;
}
.msg {
  margin: 0;
  font-size: var(--fs-aux);
}
</style>