<script setup lang="ts">
/**
 * UiModal —— 弹窗（对话框）。
 *
 * 规范：表面色 + 1px 边框 + 圆角 8（唯一允许极轻投影的组件）；遮罩半透明；
 * 交互：Esc 关闭、点遮罩关闭（可关）、打开时锁定页面滚动、焦点初始进入面板。
 */
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    /** 宽度档位 */
    size?: 'sm' | 'md' | 'lg'
    /** 是否允许点遮罩/Esc 关闭（危险确认弹窗通常传 false） */
    dismissible?: boolean
  }>(),
  { size: 'md', dismissible: true },
)

const emit = defineEmits<{ 'update:open': [open: boolean] }>()

const panel = ref<HTMLElement | null>(null)
const uid = useId()
const titleId = `ui-modal-${uid}-title`

function close() {
  if (!props.dismissible) return
  emit('update:open', false)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    close()
    return
  }
  // 焦点陷阱：Tab 在面板内循环，避免焦点跑回背景页面
  if (event.key !== 'Tab' || !panel.value) return
  const focusable = panel.value.querySelectorAll<HTMLElement>(
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )
  if (!focusable.length) {
    event.preventDefault()
    panel.value.focus()
    return
  }
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (!first || !last) return
  const active = document.activeElement
  if (event.shiftKey && (active === first || active === panel.value)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(
  () => props.open,
  (open) => {
    if (typeof document === 'undefined') return
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) {
      window.addEventListener('keydown', onKeydown)
      void nextTick(() => {
        const first = panel.value?.querySelector<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])',
        )
        ;(first ?? panel.value)?.focus()
      })
    } else {
      window.removeEventListener('keydown', onKeydown)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="ui-modal-overlay" @click.self="close">
      <section
        ref="panel"
        class="ui-modal glass glass--panel"
        :class="`ui-modal--${size}`"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        tabindex="-1"
      >
        <header class="ui-modal__head">
          <h2 :id="titleId" class="ui-modal__title">{{ title }}</h2>
          <button
            v-if="dismissible"
            type="button"
            class="ui-modal__close"
            aria-label="关闭"
            @click="close"
          >
            ✕
          </button>
        </header>
        <div class="ui-modal__body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="ui-modal__foot">
          <slot name="footer" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.ui-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  background: var(--color-overlay);
}
.ui-modal {
  width: 100%;
  max-height: calc(100vh - var(--space-8));
  overflow: auto;
  /* 材质层：玻璃（底色/模糊/1px 内高光/极轻投影由 .glass--panel 提供） */
  outline: none;
}
.ui-modal--sm {
  max-width: 400px;
}
.ui-modal--md {
  max-width: 520px;
}
.ui-modal--lg {
  max-width: 720px;
}

/* ≤600px：弹窗接近全屏，玻璃面积会破 30% 配额，且里面是表单文字 → 回退实色底部 sheet */
@media (max-width: 600px) {
  .ui-modal {
    background-color: var(--color-surface);
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
    border: 1px solid var(--color-border);
    border-radius: var(--glass-radius-sheet) var(--glass-radius-sheet) 0 0;
    box-shadow: var(--shadow-overlay);
    max-height: 88dvh;
  }
  .ui-modal-overlay {
    align-items: flex-end;
    padding: 0;
  }
}
.ui-modal__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}
.ui-modal__title {
  margin: 0;
  font-size: var(--font-size-h3);
  font-weight: var(--font-weight-semibold);
}
.ui-modal__close {
  border: 0;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 16px;
  line-height: 1;
  padding: var(--space-1);
  cursor: pointer;
  border-radius: var(--radius-xs);
}
.ui-modal__close:hover {
  color: var(--color-text);
  background: var(--color-surface-raised);
}
.ui-modal__body {
  padding: var(--space-5);
  color: var(--color-text);
}
.ui-modal__foot {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-border);
}
</style>
