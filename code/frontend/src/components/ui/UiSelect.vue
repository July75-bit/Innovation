<script setup lang="ts">
/**
 * UiSelect —— 下拉选择（材质层：玻璃 Popover）。
 *
 * 为什么不用原生 <select>：原生下拉的弹层由系统绘制，无法应用玻璃材质，
 * 也无法在深色/浅色两套令牌下保持一致的对比度与圆角。这里自绘一个符合 WAI-ARIA 的 listbox。
 *
 * 规范：
 *  - 触发框 = 内容层（实色输入框 + 1px 边框 + 圆角 6），不做玻璃；
 *  - 弹层 = 材质层（玻璃 panel，圆角 20，1px 内高光 + 极轻阴影）；
 *  - 弹层里的文字坐在 --glass-bg-strong/.74 的可读性底上（AA）；
 *  - 键盘：↑↓ 移动、Home/End、Enter/Space 选中、Esc 关闭、Tab 关闭并把焦点还给触发框；
 *  - 禁用/加载/错误态齐全；点击区域 ≥44px。
 */
import { computed, nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'

export interface UiSelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue: string | number
    label: string
    options: UiSelectOption[]
    hint?: string
    error?: string
    disabled?: boolean
    loading?: boolean
    required?: boolean
    placeholder?: string
  }>(),
  { disabled: false, loading: false, required: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const uid = useId()
const fieldId = computed(() => `ui-select-${uid}`)
const labelId = computed(() => `${fieldId.value}-label`)
const listId = computed(() => `${fieldId.value}-list`)
const descId = computed(() => `${fieldId.value}-desc`)
const message = computed(() => props.error || props.hint || '')
const invalid = computed(() => Boolean(props.error))
const isDisabled = computed(() => props.disabled || props.loading)

const open = ref(false)
const activeIndex = ref(-1)
const root = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const list = ref<HTMLElement | null>(null)

const selectedIndex = computed(() =>
  props.options.findIndex((o) => String(o.value) === String(props.modelValue)),
)
const selectedLabel = computed(() =>
  selectedIndex.value >= 0 ? (props.options[selectedIndex.value]?.label ?? '') : '',
)
const optionId = (i: number): string => `${fieldId.value}-opt-${i}`

function firstEnabled(from = 0, step = 1): number {
  for (let i = from; i >= 0 && i < props.options.length; i += step) {
    if (!props.options[i]?.disabled) return i
  }
  return -1
}

async function openList(): Promise<void> {
  if (isDisabled.value || open.value) return
  open.value = true
  activeIndex.value = selectedIndex.value >= 0 ? selectedIndex.value : firstEnabled()
  await nextTick()
  list.value?.focus()
}

function closeList(refocus = true): void {
  if (!open.value) return
  open.value = false
  activeIndex.value = -1
  if (refocus) trigger.value?.focus()
}

function move(delta: number): void {
  if (!props.options.length) return
  let i = activeIndex.value
  for (let n = 0; n < props.options.length; n++) {
    i = (i + delta + props.options.length) % props.options.length
    if (!props.options[i]?.disabled) {
      activeIndex.value = i
      return
    }
  }
}

function choose(index = activeIndex.value): void {
  const opt = props.options[index]
  if (!opt || opt.disabled) return
  emit('update:modelValue', String(opt.value))
  closeList()
}

function onTriggerKeydown(event: KeyboardEvent): void {
  if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(event.key)) {
    event.preventDefault()
    void openList()
  }
}

function onListKeydown(event: KeyboardEvent): void {
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      move(1)
      break
    case 'ArrowUp':
      event.preventDefault()
      move(-1)
      break
    case 'Home':
      event.preventDefault()
      activeIndex.value = firstEnabled()
      break
    case 'End':
      event.preventDefault()
      activeIndex.value = firstEnabled(props.options.length - 1, -1)
      break
    case 'Enter':
    case ' ':
      event.preventDefault()
      choose()
      break
    case 'Escape':
      event.preventDefault()
      closeList()
      break
    case 'Tab':
      closeList(false)
      break
  }
}

function onDocumentPointerDown(event: PointerEvent): void {
  if (!open.value) return
  if (root.value && !root.value.contains(event.target as Node)) closeList(false)
}

watch(
  () => props.disabled,
  (disabled) => {
    if (disabled) closeList(false)
  },
)

if (typeof document !== 'undefined') document.addEventListener('pointerdown', onDocumentPointerDown)
onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('pointerdown', onDocumentPointerDown)
  }
})
</script>

<template>
  <div ref="root" class="ui-field ui-select-root">
    <span :id="labelId" class="ui-label">
      {{ label }}
      <span v-if="required" class="ui-label__req" aria-hidden="true">*</span>
    </span>

    <button
      :id="fieldId"
      ref="trigger"
      type="button"
      class="ui-input ui-select"
      :class="{ 'is-invalid': invalid, 'is-open': open, 'is-loading': loading }"
      role="combobox"
      aria-haspopup="listbox"
      :aria-expanded="open"
      :aria-controls="open ? listId : undefined"
      :aria-labelledby="labelId"
      :aria-invalid="invalid || undefined"
      :aria-describedby="message ? descId : undefined"
      :aria-busy="loading || undefined"
      :disabled="isDisabled"
      @click="open ? closeList() : openList()"
      @keydown="onTriggerKeydown"
    >
      <span class="ui-select__value" :class="{ 'is-placeholder': !selectedLabel }">
        {{ selectedLabel || placeholder || '请选择' }}
      </span>
      <span v-if="loading" class="ui-select__spinner" aria-hidden="true" />
      <span v-else class="ui-select__arrow" aria-hidden="true" />
    </button>

    <!-- 弹层：材质层（玻璃）。文字坐在 --glass-bg-strong 上，保证 AA -->
    <div v-if="open" class="ui-select__pop glass glass--panel">
      <ul
        :id="listId"
        ref="list"
        class="ui-select__list"
        role="listbox"
        :aria-labelledby="labelId"
        :aria-activedescendant="activeIndex >= 0 ? optionId(activeIndex) : undefined"
        tabindex="-1"
        @keydown="onListKeydown"
      >
        <li
          v-for="(option, index) in options"
          :id="optionId(index)"
          :key="String(option.value)"
          role="option"
          class="ui-select__option"
          :class="{
            'is-active': index === activeIndex,
            'is-selected': index === selectedIndex,
            'is-disabled': option.disabled,
          }"
          :aria-selected="index === selectedIndex"
          :aria-disabled="option.disabled || undefined"
          @mouseenter="!option.disabled && (activeIndex = index)"
          @click="choose(index)"
        >
          <span class="ui-select__option-label">{{ option.label }}</span>
          <span v-if="index === selectedIndex" class="ui-select__check" aria-hidden="true">✓</span>
        </li>
        <li v-if="!options.length" class="ui-select__option is-disabled" aria-disabled="true">
          暂无选项
        </li>
      </ul>
    </div>

    <p v-if="message" :id="descId" :class="invalid ? 'ui-error' : 'ui-hint'">{{ message }}</p>
  </div>
</template>

<style scoped>
.ui-select-root {
  position: relative;
}
.ui-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
  text-align: left;
  cursor: pointer;
}
.ui-select:disabled {
  cursor: not-allowed;
}
.ui-select.is-open {
  border-color: var(--color-primary-500);
}
.ui-select__value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ui-select__value.is-placeholder {
  color: var(--color-text-disabled);
}
.ui-select__arrow {
  flex: none;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 6px solid currentColor;
  color: var(--color-text-muted);
  transition: transform var(--motion-fast) var(--motion-ease);
}
.ui-select.is-open .ui-select__arrow {
  transform: rotate(180deg);
}
.ui-select__spinner {
  flex: none;
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: ui-select-spin 0.7s linear infinite;
}
@keyframes ui-select-spin {
  to {
    transform: rotate(360deg);
  }
}
/* 弹层：位置贴住触发框，圆角 20 由 .glass--panel 提供 */
.ui-select__pop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: var(--z-dropdown);
  padding: var(--space-1);
  max-height: 280px;
  overflow: auto;
}
.ui-select__list {
  margin: 0;
  padding: 0;
  list-style: none;
  outline: none;
}
.ui-select__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  min-height: 44px; /* 点击区 ≥44px */
  padding: 0 var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: var(--font-size-body);
  cursor: pointer;
}
.ui-select__option.is-active {
  background: var(--color-surface-raised);
}
.ui-select__option.is-selected {
  color: var(--color-text-strong);
  font-weight: var(--font-weight-semibold);
}
.ui-select__option.is-disabled {
  color: var(--color-text-disabled);
  cursor: not-allowed;
}
.ui-select__check {
  color: var(--color-primary-300);
}
.ui-label__req {
  color: var(--color-error-base);
  margin-left: 2px;
}
@media (prefers-reduced-motion: reduce) {
  .ui-select__arrow {
    transition: none;
  }
  .ui-select__spinner {
    animation: none;
  }
}
</style>
