<script setup lang="ts">
/**
 * UiButton —— 统一按钮（扁平化）。
 *
 * 规范：高度 36/40/44，圆角 6，1px 边框，无阴影/无渐变；
 * 状态：default / hover / focus-visible / active / disabled / loading。
 * 主按钮全站唯一实色（--color-action），次按钮描边，危险操作红色。
 */
import { computed } from 'vue'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'
type Size = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<{
    variant?: Variant
    size?: Size
    /** 加载中：禁用点击 + 左侧转圈 + aria-busy */
    loading?: boolean
    disabled?: boolean
    /** 撑满父容器（移动端主按钮常用） */
    block?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  { variant: 'secondary', size: 'md', loading: false, disabled: false, block: false, type: 'button' },
)

const emit = defineEmits<{ click: [event: MouseEvent] }>()

const isDisabled = computed(() => props.disabled || props.loading)

const classes = computed(() => [
  'ui-btn',
  `ui-btn--${props.variant}`,
  props.size !== 'md' ? `ui-btn--${props.size}` : '',
  { 'is-block': props.block, 'is-loading': props.loading },
])

function onClick(event: MouseEvent) {
  if (isDisabled.value) return
  emit('click', event)
}
</script>

<template>
  <button
    :type="type"
    :class="classes"
    :disabled="isDisabled"
    :aria-busy="loading || undefined"
    @click="onClick"
  >
    <span v-if="loading" class="ui-btn__spinner" aria-hidden="true" />
    <slot />
  </button>
</template>

<style scoped>
.ui-btn.is-block {
  width: 100%;
}
.ui-btn:active:not(:disabled) {
  transform: translateY(1px);
}
.ui-btn__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ui-btn-spin 0.7s linear infinite;
}
@keyframes ui-btn-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .ui-btn:active:not(:disabled) {
    transform: none;
  }
  .ui-btn__spinner {
    animation: none;
  }
}
</style>
