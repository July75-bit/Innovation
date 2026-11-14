<script setup lang="ts">
/**
 * UiNavItem —— 侧栏/顶部导航项。
 *
 * 规范：高度 40，圆角 6，图标 16px 线性；
 * 选中态 = 中性高亮 + 左侧 2px 主色竖条（**不用整块主色**，红色留给主 CTA）。
 */
withDefaults(
  defineProps<{
    href?: string
    active?: boolean
    disabled?: boolean
  }>(),
  { active: false, disabled: false },
)
</script>

<template>
  <component
    :is="href ? 'a' : 'button'"
    :href="href"
    :type="href ? undefined : 'button'"
    :class="['ui-nav__item', { 'is-active': active, 'is-disabled': disabled }]"
    :aria-current="active ? 'page' : undefined"
    :aria-disabled="disabled || undefined"
    :tabindex="disabled ? -1 : undefined"
  >
    <span v-if="$slots.icon" class="ui-nav__icon" aria-hidden="true"><slot name="icon" /></span>
    <slot />
  </component>
</template>

<style scoped>
.ui-nav__item.is-disabled {
  opacity: 0.45;
  pointer-events: none;
}
.ui-nav__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--icon-size-sm);
  height: var(--icon-size-sm);
}
.ui-nav__icon :deep(svg) {
  width: 100%;
  height: 100%;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
}
</style>
