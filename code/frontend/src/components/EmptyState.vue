<script setup lang="ts">
/** 空态：列表无数据 / 可选操作引导（默认插槽放链接等） */
</script>

<template>
  <p class="state"><slot>暂无数据</slot></p>
</template>

<style scoped>
.state {
  color: var(--muted);
  padding: 28px 0;
  text-align: center;
}
</style>
