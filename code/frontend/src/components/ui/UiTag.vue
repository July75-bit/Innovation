<script setup lang="ts">
/**
 * UiTag —— 状态标签 / 徽章。
 *
 * 规范：圆角 4，13px，浅底 + 语义文字色；**必须带文字**，不能只靠颜色表达状态。
 */
type Tone = 'neutral' | 'success' | 'warning' | 'error' | 'info'

withDefaults(defineProps<{ tone?: Tone }>(), { tone: 'neutral' })
</script>

<template>
  <span :class="['ui-badge', `ui-badge--${tone}`]"><slot /></span>
</template>
