<script setup lang="ts">
/**
 * 白话导读：选手交易状态的小圆牌：绿点=交易中，黄点=暂停（比赛中）。
 * 市场页和详情页共用这一个组件，样式就不用各写一份（改颜色只需改这里）。
 * props 只有一个字符串 status，内部用 computed 换成要显示的中文与样式类。
 */
/**
 * 状态徽章（统一组件）：交易中=绿点、暂停交易=警示黄点。
 * 市场卡片与详情页共用，替代两处各写一份的 .status 样式。
 */
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

const trading = computed(() => props.status === 'trading')
</script>

<template>
  <span :class="['badge', trading ? 'ok' : 'halt']" role="status">
    <i class="dot" aria-hidden="true"></i>
    {{ trading ? '交易中' : '暂停交易' }}
  </span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-cap);
  padding: 2px 10px;
  border-radius: var(--radius-pill, 999px);
  white-space: nowrap;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.badge.ok {
  background: var(--down-bg);
  color: var(--down);
}
.badge.halt {
  background: var(--warn-bg);
  color: var(--warn);
}
</style>