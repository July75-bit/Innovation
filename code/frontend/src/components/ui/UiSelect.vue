<script setup lang="ts">
/**
 * UiSelect —— 原生 select 的下拉封装（可访问性最好，不用自绘弹层）。
 *
 * 规范：高度 40，圆角 6，1px 边框；错误信息紧贴字段；禁用态变灰。
 */
import { computed, useId } from 'vue'

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
    required?: boolean
    placeholder?: string
  }>(),
  { disabled: false, required: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const uid = useId()
const fieldId = computed(() => `ui-select-${uid}`)
const descId = computed(() => `${fieldId.value}-desc`)
const message = computed(() => props.error || props.hint || '')
const invalid = computed(() => Boolean(props.error))

function onChange(event: Event) {
  emit('update:modelValue', (event.target as HTMLSelectElement).value)
}
</script>

<template>
  <div class="ui-field">
    <label class="ui-label" :for="fieldId">
      {{ label }}
      <span v-if="required" class="ui-label__req" aria-hidden="true">*</span>
    </label>
    <select
      :id="fieldId"
      class="ui-input ui-select"
      :class="{ 'is-invalid': invalid }"
      :value="modelValue"
      :disabled="disabled"
      :required="required"
      :aria-invalid="invalid || undefined"
      :aria-describedby="message ? descId : undefined"
      @change="onChange"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        :disabled="option.disabled"
      >
        {{ option.label }}
      </option>
    </select>
    <p v-if="message" :id="descId" :class="invalid ? 'ui-error' : 'ui-hint'">{{ message }}</p>
  </div>
</template>

<style scoped>
.ui-select {
  appearance: none;
  padding-right: 36px;
  background-image: linear-gradient(45deg, transparent 50%, currentColor 50%),
    linear-gradient(135deg, currentColor 50%, transparent 50%);
  background-position:
    calc(100% - 18px) 55%,
    calc(100% - 13px) 55%;
  background-size:
    5px 5px,
    5px 5px;
  background-repeat: no-repeat;
}
.ui-select.is-invalid {
  border-color: var(--color-error-base);
}
.ui-label__req {
  color: var(--color-error-base);
  margin-left: 2px;
}
</style>
