<script setup lang="ts">
/**
 * UiBottomTab —— 底部 Tab 栏（材质层：液态玻璃）。
 *
 * 规范：
 *  - 只在移动端出现（≤960px），是"主导航"的等价入口，所以点击区 ≥44px；
 *  - 玻璃 + scrim：文字坐在 --glass-scrim 上，保证 AA；同屏玻璃面积很小（约 8%）；
 *  - 选中态 = 中性高亮 + 2px 主色指示条（红色只留主 CTA 与涨跌语义）；
 *  - 动态高光只 hover/focus 轻微出现（由 .glass--interactive 统一控制，移动端自动关）。
 * 用法：
 *  <UiBottomTab v-model="tab" :items="items" @select="onSelect" />
 */
export interface UiTabItem {
  key: string
  label: string
  /** 16×16 viewBox 的 SVG path（尽量用现有线性图标风格） */
  icon?: string
}

const props = withDefaults(
  defineProps<{
    modelValue: string
    items: UiTabItem[]
    ariaLabel?: string
    /** true = 组件库预览用：不再 fixed，直接排在页面流里 */
    preview?: boolean
  }>(),
  { ariaLabel: '主导航', preview: false },
)

const emit = defineEmits<{ 'update:modelValue': [key: string]; select: [key: string] }>()

function pick(key: string): void {
  if (key === props.modelValue) return
  emit('update:modelValue', key)
  emit('select', key)
}
</script>

<template>
  <nav
    class="ui-tabbar glass glass--panel glass--scrim glass--interactive"
    :class="{ 'is-preview': preview }"
    :aria-label="ariaLabel"
  >
    <button
      v-for="item in items"
      :key="item.key"
      type="button"
      class="ui-tab"
      :class="{ 'is-active': item.key === modelValue }"
      :aria-current="item.key === modelValue ? 'page' : undefined"
      @click="pick(item.key)"
    >
      <span v-if="item.icon" class="ui-tab__icon" aria-hidden="true">
        <svg viewBox="0 0 16 16"><path :d="item.icon" /></svg>
      </span>
      <span class="ui-tab__label">{{ item.label }}</span>
    </button>
  </nav>
</template>

<style scoped>
.ui-tabbar {
  position: fixed;
  left: 50%;
  bottom: calc(12px + env(safe-area-inset-bottom, 0px));
  transform: translateX(-50%);
  z-index: var(--z-nav);
  display: none; /* 桌面隐藏；≤960px 打开 */
  align-items: stretch;
  gap: 2px;
  width: min(520px, calc(100% - 24px));
  padding: 6px;
}
.ui-tab {
  flex: 1;
  min-width: 0;
  min-height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 4px;
  border: 0;
  border-radius: var(--radius-material-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: var(--font-size-cap);
  line-height: 1.2;
  cursor: pointer;
  position: relative;
}
.ui-tab:hover {
  color: var(--color-text);
  background: var(--color-surface-raised);
}
.ui-tab:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
.ui-tab.is-active {
  /* P1：与侧栏统一——淡主色底 pill + 主色文字，不再用顶部竖条 */
  color: var(--color-selection-text);
  background: var(--color-selection-bg);
  font-weight: var(--font-weight-semibold);
}
.ui-tab__icon svg {
  width: var(--icon-size-sm);
  height: var(--icon-size-sm);
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.ui-tab__label {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 960px) {
  .ui-tabbar {
    display: flex;
  }
}
/* 组件库预览：不吸底、直接排在流里（业务页永远用 fixed 那版） */
.ui-tabbar.is-preview {
  display: flex;
  position: static;
  transform: none;
  max-width: 520px;
  margin: 0 auto;
}
</style>
