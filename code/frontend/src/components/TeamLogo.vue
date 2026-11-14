<script setup lang="ts">
/**
 * 白话导读：战队队标小方块。赛程页的对阵、全季表、停牌名单都用它。
 *
 * 用法：`<TeamLogo :team="match.team_a" :name="teamOf(match, 'team_a')" size="lg" />`
 * ——`team` 传 team_id 或队伍名都行（映射表在 `src/data/teamLogos.ts`）。
 *
 * 两个刻意的细节：
 * 1. 底板是浅色的：站队标里有一批是纯黑/纯白图形（Vitality、Spirit、G2），
 *    直接放在深色主题上会糊成一片，垫一块浅色砖才谁都看得清；
 * 2. 图挂了（文件缺失、构建时漏拷）就退成队名首字母，绝不出现浏览器破图。
 */
import { computed, ref } from 'vue'
import { teamDisplayName, teamInitials, teamLogo } from '../data/teamLogos'

const props = withDefaults(
  defineProps<{
    /** team_id 或队伍名（简称 / 全称都认） */
    team?: number | string | null
    /** 显示名，优先用它做 alt；没传就按映射表补 */
    name?: string | null
    size?: 'xs' | 'sm' | 'md' | 'lg'
  }>(),
  { team: null, name: null, size: 'sm' },
)

const label = computed(() => props.name || teamDisplayName(props.team) || '战队')
const src = computed(() => teamLogo(props.team))

/** 记录"哪张图"加载失败，换成别的队标时不会把新图也一起挡掉 */
const failed = ref<string | null>(null)
const shown = computed(() => (src.value && src.value !== failed.value ? src.value : null))
</script>

<template>
  <span :class="['team-logo', props.size]" role="img" :aria-label="`${label} 队标`" :title="label">
    <img
      v-if="shown"
      :src="shown"
      :alt="`${label} 队标`"
      loading="lazy"
      decoding="async"
      @error="failed = shown"
    />
    <b v-else class="fallback">{{ teamInitials(label) }}</b>
  </span>
</template>

<style scoped>
.team-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-sizing: border-box;
  background: #f3f5f9;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: var(--radius-sm);
  overflow: hidden;
  line-height: 1;
}
.team-logo img {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: var(--logo-pad, 3px);
  object-fit: contain;
  display: block;
}
.fallback {
  font-style: normal;
  font-weight: 800;
  color: #16181c;
  letter-spacing: 0;
}
.team-logo.xs {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  font-size: 9px;
  --logo-pad: 1px;
}
.team-logo.sm {
  width: 26px;
  height: 26px;
  font-size: 11px;
  --logo-pad: 2px;
}
.team-logo.md {
  width: 40px;
  height: 40px;
  font-size: 14px;
}
.team-logo.lg {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  font-size: 18px;
}
</style>
