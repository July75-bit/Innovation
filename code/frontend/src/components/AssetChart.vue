<script setup lang="ts">
/**
 * 资产曲线（个人页）：纯 SVG 手绘，不引图表库。
 *
 * 输入是后端 `/api/account/history` 的点（时间升序、总资产），
 * 这里只做「好看刻度 + 折线 + 面积 + 首尾日期」；没有交互，个人页不需要。
 */
import { computed } from 'vue'
import type { AssetPoint } from '../api/types'
import { money } from '../utils/format'

const props = defineProps<{ points: AssetPoint[] }>()

const W = 640
const H = 200
const PAD = { top: 14, right: 14, bottom: 24, left: 62 }

function niceDomain(min: number, max: number, count: number) {
  // 数据完全没波动时也要留出纵向空间，否则线会贴在底边（实测：只有 5000 一个值时）
  const span = Math.max(max - min, Math.max(Math.abs(max) * 0.04, 2))
  const raw = span / count
  const mag = 10 ** Math.floor(Math.log10(raw))
  const norm = raw / mag
  const step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * mag
  const low = Math.floor((min - span * 0.05) / step) * step
  const high = Math.ceil((max + span * 0.05) / step) * step
  return { low, high, step }
}

function dateLabel(iso: string): string {
  const date = new Date(iso)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const chart = computed(() => {
  const pts = props.points
  if (!pts.length) return null
  const values = pts.map((point) => point.total_asset)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const { low, high, step } = niceDomain(min, max, 3)
  const span = high - low || 1
  const innerW = W - PAD.left - PAD.right
  const innerH = H - PAD.top - PAD.bottom
  const x = (index: number) => PAD.left + (pts.length === 1 ? 0 : (index / (pts.length - 1)) * innerW)
  const y = (value: number) => PAD.top + innerH * (1 - (value - low) / span)

  const dots = pts.map((point, index) => ({
    x: x(index),
    y: y(point.total_asset),
    value: point.total_asset,
  }))
  const line = dots.map((dot) => `${dot.x.toFixed(1)},${dot.y.toFixed(1)}`).join(' ')
  const first = dots[0]!
  const last = dots[dots.length - 1]!
  const area = `${line} ${last.x.toFixed(1)},${(PAD.top + innerH).toFixed(1)} ${first.x.toFixed(1)},${(PAD.top + innerH).toFixed(1)}`

  const ticks: { value: number; y: number }[] = []
  for (let value = low; value <= high + step / 1000; value += step) {
    ticks.push({ value, y: y(value) })
  }

  return {
    line,
    area,
    dots,
    ticks,
    baseline: PAD.top + innerH,
    firstDate: dateLabel(pts[0]!.ts),
    lastDate: dateLabel(pts[pts.length - 1]!.ts),
    tone: last.value > first.value ? 'up' : last.value < first.value ? 'down' : 'flat',
  }
})
</script>

<template>
  <div class="asset-chart">
    <svg
      v-if="chart"
      :viewBox="`0 0 ${W} ${H}`"
      role="img"
      :aria-label="`资产曲线：从 ${money(chart.dots[0]!.value)} 到 ${money(chart.dots[chart.dots.length - 1]!.value)}`"
    >
      <g v-for="tick in chart.ticks" :key="tick.value">
        <line
          :x1="PAD.left"
          :y1="tick.y"
          :x2="W - PAD.right"
          :y2="tick.y"
          :class="tick.value === chart.ticks[0]!.value ? 'axis' : 'grid'"
        />
        <text :x="PAD.left - 8" :y="tick.y + 4" class="tick" text-anchor="end">
          {{ money(tick.value) }}
        </text>
      </g>
      <polygon :points="chart.area" :class="['area', chart.tone]" />
      <polyline :points="chart.line" fill="none" :class="['line', chart.tone]" />
      <circle
        :cx="chart.dots[chart.dots.length - 1]!.x"
        :cy="chart.dots[chart.dots.length - 1]!.y"
        r="3.5"
        :class="chart.tone"
      />
      <text :x="PAD.left" :y="H - 6" class="tick">{{ chart.firstDate }}</text>
      <text :x="W - PAD.right" :y="H - 6" class="tick" text-anchor="end">
        {{ chart.lastDate }}
      </text>
    </svg>
    <p v-else class="empty">还没有资产数据</p>
  </div>
</template>

<style scoped>
.asset-chart svg {
  width: 100%;
  height: auto;
  display: block;
}
.grid {
  stroke: var(--color-border);
  stroke-dasharray: 4 4;
  opacity: 0.6;
}
.axis {
  stroke: var(--color-border);
}
.tick {
  fill: var(--color-text-faint);
  font-size: var(--fs-cap);
}
.line {
  stroke-width: 2;
}
.line.up {
  stroke: var(--up);
}
.line.down {
  stroke: var(--color-down);
}
.line.flat {
  stroke: var(--color-text-faint);
}
.area.flat {
  fill: var(--color-text-faint);
  opacity: 0.06;
}
circle.flat {
  fill: var(--color-text-faint);
}
.area.up {
  fill: var(--up);
  opacity: 0.08;
}
.area.down {
  fill: var(--color-down);
  opacity: 0.08;
}
circle.up {
  fill: var(--up);
}
circle.down {
  fill: var(--color-down);
}
.empty {
  margin: 0;
  padding: var(--space-6) 0;
  text-align: center;
  color: var(--faint);
  font-size: var(--fs-aux);
}
</style>
