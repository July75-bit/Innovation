<script setup lang="ts">
/**
 * UiInput —— 带标签 / 提示 / 错误信息的输入框。
 *
 * 规范：高度 40，圆角 6，1px 边框；错误信息紧贴字段（13px，原因 + 下一步）；
 * 无障碍：label 与控件用 for/id 关联，错误用 aria-invalid + aria-describedby。
 */
import { computed, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string | number | null
    label: string
    /** 字段说明（未出错时显示） */
    hint?: string
    /** 错误信息（出错时显示，优先于 hint） */
    error?: string
    placeholder?: string
    type?: 'text' | 'number' | 'password' | 'search'
    disabled?: boolean
    required?: boolean
    size?: 'sm' | 'md'
    inputmode?: 'text' | 'numeric' | 'decimal'
    min?: number
    max?: number
    step?: number
    /** 后缀单位（如「股」） */
    suffix?: string
  }>(),
  { type: 'text', disabled: false, required: false, size: 'md' },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const uid = useId()
const fieldId = computed(() => `ui-input-${uid}`)
const descId = computed(() => `${fieldId.value}-desc`)
const message = computed(() => props.error || props.hint || '')
const invalid = computed(() => Boolean(props.error))

function onInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="ui-field">
    <label class="ui-label" :for="fieldId">
      {{ label }}
      <span v-if="required" class="ui-label__req" aria-hidden="true">*</span>
    </label>
    <div :class="['ui-input-wrap', { 'is-invalid': invalid, [`is-${size}`]: true }]">
      <input
        :id="fieldId"
        class="ui-input"
        :class="{ 'has-suffix': Boolean(suffix) }"
        :type="type"
        :value="modelValue ?? ''"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :inputmode="inputmode"
        :min="min"
        :max="max"
        :step="step"
        :aria-invalid="invalid || undefined"
        :aria-describedby="message ? descId : undefined"
        @input="onInput"
        @blur="emit('blur')"
      />
      <span v-if="suffix" class="ui-input__suffix" aria-hidden="true">{{ suffix }}</span>
    </div>
    <p v-if="message" :id="descId" :class="invalid ? 'ui-error' : 'ui-hint'">{{ message }}</p>
  </div>
</template>

<style scoped>
.ui-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.ui-input-wrap.is-sm .ui-input {
  height: var(--control-height-sm);
}
.ui-input-wrap.is-invalid .ui-input {
  border-color: var(--color-error-base);
}
.ui-input.has-suffix {
  padding-right: 32px;
}
.ui-input__suffix {
  position: absolute;
  right: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-aux);
  pointer-events: none;
}
.ui-label__req {
  color: var(--color-error-base);
  margin-left: 2px;
}
</style>
