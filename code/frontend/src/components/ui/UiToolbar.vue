<script setup lang="ts">
/**
 * UiToolbar —— 悬浮工具栏（材质层：液态玻璃）。
 *
 * 规范：
 *  - 半透明底 + backdrop-filter + 1px 内高光 + 极轻阴影；圆角 12（= --radius-material-sm）；
 *  - 文字坐在 scrim 上（--glass-scrim），保证 AA；同屏只应出现一条（面积很小，约 2–4%）；
 *  - **禁止在里面再放玻璃按钮**（玻璃叠玻璃）：内部控件一律实色/透明按钮；
 *  - 动态高光仅 hover/focus 轻微出现；移动端与 reduced-motion 自动关闭（见 liquid-glass.css）。
 *
 * 用法：
 *  <UiToolbar label="行情操作">
 *    <span>ZywOo · 108.75 · +2.1%</span>
 *    <template #end><UiButton>买入</UiButton></template>
 *  </UiToolbar>
 */
withDefaults(
  defineProps<{
    label: string
    /** sticky：随页面滚动吸附在顶部（移动端详情页常用） */
    position?: 'static' | 'sticky'
  }>(),
  { position: 'static' },
)
</script>

<template>
  <div
    class="ui-toolbar glass glass--control glass--interactive"
    :class="`is-${position}`"
    role="toolbar"
    :aria-label="label"
  >
    <div class="ui-toolbar__main">
      <slot />
    </div>
    <div v-if="$slots.end" class="ui-toolbar__end">
      <slot name="end" />
    </div>
  </div>
</template>

<style scoped>
.ui-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  min-height: 48px;
}
.ui-toolbar.is-sticky {
  position: sticky;
  top: var(--space-3);
  z-index: var(--z-dropdown);
}
.ui-toolbar__main {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  min-width: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-aux);
}
.ui-toolbar__end {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: none;
}
</style>
