<script setup lang="ts">
/**
 * 关于本站：把原来堆在侧栏底部的合规长文收进来。
 * 页面底部只留一行「关于本站」，需要时再展开，降低首屏噪音。
 */
import UiModal from './ui/UiModal.vue'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [open: boolean] }>()

const year = new Date().getFullYear()
</script>

<template>
  <UiModal
    :open="open"
    title="关于 PlayerStock"
    size="md"
    @update:open="emit('update:open', $event)"
  >
    <div class="about">
      <p>PlayerStock 是课程作品：用信用点模拟买卖 CS2 职业选手股，练习看行情和做交易判断。</p>
      <p>
        全程信用点，不可充值、提现或兑换。选手信息与价格评分均为模拟数据，与 Valve、HLTV
        及相关俱乐部无关联，不构成投资建议。
      </p>
      <p class="meta">16 名选手 · 8 支战队 · {{ year }}</p>
    </div>
  </UiModal>
</template>

<style scoped>
.about {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  font-size: var(--fs-body);
  line-height: var(--line-height-body);
  color: var(--text);
}
.about p {
  margin: 0;
}
.meta {
  color: var(--faint);
  font-size: var(--fs-cap);
}
</style>
