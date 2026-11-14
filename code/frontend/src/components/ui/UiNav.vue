<script setup lang="ts">
/**
 * UiNav —— 导航容器。配合 UiNavItem 使用。
 * 规范：宽 232，纵向排列，条目间距 2px。
 */
withDefaults(defineProps<{ label?: string }>(), { label: '主导航' })
</script>

<template>
  <nav class="ui-nav" :aria-label="label">
    <slot />
  </nav>
</template>
