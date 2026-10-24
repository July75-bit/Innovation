<script setup lang="ts">
/**
 * 价格历史折线图（契约 §4.4：points 已按 ts 升序，直接用，不再排序）。
 * 零依赖 SVG 实现；第 4 天如需交互增强（悬停显示 reason 等）可再升级。
 */
import { computed } from 'vue'
import type { PricePoint } from '../api/types'
import { money, shortTime } from '../utils/format'

const props = defineProps<{ points: PricePoint[] }>()

const W = 640
const H = 240
const PAD = { top: 16, right: 16, bottom: 30, left: 56 }

const chart = computed(() => {
  const pts = props.points
  if (pts.length === 0) return null

  let min = Infinity
  let max = -Infinity
  for (const p of pts) {
    if (p.price < min) min = p.price
    if (p.price > max) max = p.price
  }
  if (max - min < 1e-9) {
    min -= 1
    max += 1
  }

  const innerW = W - PAD.left - PAD.right
  const innerH = H - PAD.top - PAD.bottom
  const step = pts.length > 1 ? innerW / (pts.length - 1) : 0

  const xy: [number, number][] = []
  for (let i = 0; i < pts.length; i += 1) {
    const p = pts[i] as PricePoint
    const x = PAD.left + i * step
    const y = PAD.top + innerH * (1 - (p.price - min) / (max - min))
    xy.push([x, y])
  }

  const line = xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const first = xy[0] as [number, number]
  const last = xy[xy.length - 1] as [number, number]
  const area = `${line} ${last[0].toFixed(1)},${(PAD.top + innerH).toFixed(1)} ${first[0].toFixed(1)},${(PAD.top + innerH).toFixed(1)}`

  const firstPrice = (pts[0] as PricePoint).price
  const lastPrice = (pts[pts.length - 1] as PricePoint).price

  return {
    line,
    area,
    lastPoint: last,
    minY: min,
    maxY: max,
    midY: (min + max) / 2,
    baseline: PAD.top + innerH,
    firstTs: (pts[0] as PricePoint).ts,
    lastTs: (pts[pts.length - 1] as PricePoint).ts,
    rising: lastPrice >= firstPrice,
  }
})
</script>

<template>
  <div class="chart-card">
    <svg v-if="chart" :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="价格历史折线图">
      <!-- 网格线与 Y 轴刻度 -->
      <line
        :x1="PAD.left"
        :y1="chart.baseline"
        :x2="W - PAD.right"
        :y2="chart.baseline"
        class="axis"
      />
      <line :x1="PAD.left" :y1="PAD.top" :x2="W - PAD.right" :y2="PAD.top" class="grid" />
      <line
        :x1="PAD.left"
        :y1="(PAD.top + chart.baseline) / 2"
        :x2="W - PAD.right"
        :y2="(PAD.top + chart.baseline) / 2"
        class="grid"
      />
      <text :x="PAD.left - 8" :y="PAD.top + 4" class="tick" text-anchor="end">
        {{ money(chart.maxY) }}
      </text>
      <text
        :x="PAD.left - 8"
        :y="(PAD.top + chart.baseline) / 2 + 4"
        class="tick"
        text-anchor="end"
      >
        {{ money(chart.midY) }}
      </text>
      <text :x="PAD.left - 8" :y="chart.baseline + 4" class="tick" text-anchor="end">
        {{ money(chart.minY) }}
      </text>

      <polygon :points="chart.area" :class="['area', chart.rising ? 'up' : 'down']" />
      <polyline :points="chart.line" fill="none" :class="['line', chart.rising ? 'up' : 'down']" />
      <circle
        :cx="chart.lastPoint[0]"
        :cy="chart.lastPoint[1]"
        r="4"
        :class="['dot', chart.rising ? 'up' : 'down']"
      />

      <!-- X 轴首尾时间 -->
      <text :x="PAD.left" :y="H - 8" class="tick">{{ shortTime(chart.firstTs) }}</text>
      <text :x="W - PAD.right" :y="H - 8" class="tick" text-anchor="end">
        {{ shortTime(chart.lastTs) }}
      </text>
    </svg>
    <p v-else class="empty">暂无价格历史数据</p>
  </div>
</template>

<style scoped>
.chart-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
}
svg {
  width: 100%;
  height: auto;
  display: block;
}
.axis {
  stroke: var(--border);
}
.grid {
  stroke: var(--border);
  stroke-dasharray: 4 4;
  opacity: 0.6;
}
.tick {
  fill: var(--muted);
  font-size: 11px;
}
.line.up {
  stroke: var(--up);
}
.line.down {
  stroke: var(--down);
}
.line {
  stroke-width: 2;
}
.dot.up {
  fill: var(--up);
}
.dot.down {
  fill: var(--down);
}
.area.up {
  fill: var(--up);
  opacity: 0.08;
}
.area.down {
  fill: var(--down);
  opacity: 0.08;
}
.empty {
  color: var(--muted);
  text-align: center;
  padding: 40px 0;
  margin: 0;
}
</style>
