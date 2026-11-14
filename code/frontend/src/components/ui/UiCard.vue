<script setup lang="ts">
/**
 * UiCard —— 内容卡片。
 *
 * 规范：1px 边框 + 圆角 8 + 内边距 16，**无阴影**；
 * 可点击时只提亮边框（不位移/不放大）；选中态左侧 2px 主色竖条。
 */
withDefaults(
  defineProps<{
    title?: string
    meta?: string
    interactive?: boolean
    selected?: boolean
  }>(),
  { interactive: false, selected: false },
)
</script>

<template>
  <component
    :is="interactive ? 'button' : 'div'"
    :type="interactive ? 'button' : undefined"
    :class="['ui-card', { 'ui-card--interactive': interactive, 'ui-card--selected': selected }]"
  >
    <header v-if="title || $slots.header" class="ui-card__head">
      <slot name="header">
        <h3 class="ui-card__title">{{ title }}</h3>
        <p v-if="meta" class="ui-card__meta">{{ meta }}</p>
      </slot>
    </header>
    <slot />
    <footer v-if="$slots.footer" class="ui-card__foot">
      <slot name="footer" />
    </footer>
  </component>
</template>

<style scoped>
.ui-card__head {
  margin-bottom: var(--space-3);
}
.ui-card__foot {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
/* 可点击卡片：button 复位 */
button.ui-card {
  font-family: inherit;
  text-align: left;
  width: 100%;
}
</style>
