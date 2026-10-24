<script setup lang="ts">
/**
 * 价格历史折线图（契约 §4.4：points 已按 ts 升序，直接用，不再排序）。
 *
 * 第 4 天 T4-02 交互升级（零依赖）：
 * - 悬停数据点显示该点 ts/price/reason 的 tooltip（含垂直辅助线）；
 * - 每个命中圆内带原生 <title>，非鼠标用户（键盘/触屏长按）也有兜底提示；
 * - 图下方「价格变动明细」列表逐点展示 时间/价格/reason，
 *   便于与 GET /api/players/{id}/prices 响应逐条抽查（M4 验收第 3 项）。
 */
import { computed, ref } from 'vue'
import type { PricePoint } from '../api/types'
import { dateTime, money } from '../utils/format'

const props = defineProps<{ points: PricePoint[] }>()

const W = 640
const H = 240
const PAD = { top: 16, right: 16, bottom: 30, left: 56 }

const showDetail = ref(false)
const hoverIdx = ref<number | null>(null)

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

  const dots = pts.map((p, i) => {
    const x = PAD.left + i * step
    const y = PAD.top + innerH * (1 - (p.price - min) / (max - min))
    return { x, y, ts: p.ts, price: p.price, reason: p.reason }
  })

  const line = dots.map((d) => `${d.x.toFixed(1)},${d.y.toFixed(1)}`).join(' ')
  const first = dots[0] as (typeof dots)[number]
  const last = dots[dots.length - 1] as (typeof dots)[number]
  const area = `${line} ${last.x.toFixed(1)},${(PAD.top + innerH).toFixed(1)} ${first.x.toFixed(1)},${(PAD.top + innerH).toFixed(1)}`

  const firstPrice = (pts[0] as PricePoint).price
  const lastPrice = (pts[pts.length - 1] as PricePoint).price

  return {
    line,
    area,
    dots,
    minY: min,
    maxY: max,
    midY: (min + max) / 2,
    baseline: PAD.top + innerH,
    firstTs: (pts[0] as PricePoint).ts,
    lastTs: (pts[pts.length - 1] as PricePoint).ts,
    rising: lastPrice >= firstPrice,
  }
})

/** 当前悬停的数据点（null = 无） */
const hovered = computed(() => {
  const i = hoverIdx.value
  if (i === null || !chart.value) return null
  return (chart.value.dots[i] as (typeof chart.value.dots)[number] | undefined) ?? null
})

/** X 轴首尾标签：只显示日期（种子数据的时间点通常都是同一时刻） */
function dayLabel(iso: string): string {
  return new Date(iso).toLocaleDateString()
}

function tipStyle(d: { x: number; y: number }) {
  return {
    left: `${(d.x / W) * 100}%`,
    top: `${(d.y / H) * 100}%`,
  }
}
</script>

<template>
  <div class="chart-card">
    <template v-if="chart">
      <div class="chart-wrap">
        <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="价格历史折线图">
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

          <!-- 悬停辅助线 -->
          <line
            v-if="hovered"
            :x1="hovered.x"
            :y1="PAD.top"
            :x2="hovered.x"
            :y2="chart.baseline"
            class="guide"
          />

          <!-- 可见数据点（悬停放大） -->
          <circle
            v-for="(d, i) in chart.dots"
            :key="'p' + d.ts"
            :class="['pt', chart.rising ? 'up' : 'down']"
            :cx="d.x"
            :cy="d.y"
            :r="hoverIdx === i ? 4 : 2.5"
          />
          <!-- 透明大命中区：悬停出 tooltip；原生 title 兜底 -->
          <circle
            v-for="(d, i) in chart.dots"
            :key="'h' + d.ts"
            class="hit"
            :cx="d.x"
            :cy="d.y"
            r="10"
            @mouseenter="hoverIdx = i"
            @mouseleave="hoverIdx = null"
          >
            <title>{{ dateTime(d.ts) }} · {{ money(d.price) }} 币 · {{ d.reason }}</title>
          </circle>

          <!-- X 轴首尾时间 -->
          <text :x="PAD.left" :y="H - 8" class="tick">{{ dayLabel(chart.firstTs) }}</text>
          <text :x="W - PAD.right" :y="H - 8" class="tick" text-anchor="end">
            {{ dayLabel(chart.lastTs) }}
          </text>
        </svg>

        <!-- 悬停 tooltip：每点 reason（M4 验收第 3 项） -->
        <div
          v-if="hovered"
          class="tip"
          :class="{
            'tip-near-left': hovered.x < 150,
            'tip-near-right': hovered.x > W - 150,
          }"
          :style="tipStyle(hovered)"
        >
          <strong>{{ dateTime(hovered.ts) }} · {{ money(hovered.price) }} 币</strong>
          <p>{{ hovered.reason }}</p>
        </div>
      </div>

      <p class="detail-line">
        <button
          class="detail-toggle"
          type="button"
          :aria-expanded="showDetail"
          @click="showDetail = !showDetail"
        >
          {{ showDetail ? '收起' : '查看' }}价格变动明细（{{ chart.dots.length }}）
        </button>
      </p>
      <ol v-if="showDetail" class="detail-list">
        <li v-for="(d, i) in chart.dots" :key="'d' + d.ts">
          <span class="seq">#{{ i + 1 }}</span>
          <span class="ts">{{ dateTime(d.ts) }}</span>
          <span class="pr">{{ money(d.price) }}</span>
          <span class="rs">{{ d.reason }}</span>
        </li>
      </ol>
    </template>
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
.chart-wrap {
  position: relative;
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
.guide {
  stroke: var(--muted);
  stroke-dasharray: 3 3;
  opacity: 0.7;
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
.pt.up {
  fill: var(--up);
}
.pt.down {
  fill: var(--down);
}
.hit {
  fill: transparent;
  cursor: crosshair;
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
.tip {
  position: absolute;
  transform: translate(-50%, calc(-100% - 10px));
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  max-width: 260px;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  z-index: 2;
}
.tip.tip-near-left {
  transform: translate(-12%, calc(-100% - 10px));
}
.tip.tip-near-right {
  transform: translate(-88%, calc(-100% - 10px));
}
.tip p {
  margin: 4px 0 0;
  color: var(--muted);
  line-height: 1.5;
}
.detail-line {
  margin: 8px 0 0;
  text-align: right;
}
.detail-toggle {
  background: none;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
}
.detail-toggle:hover {
  color: var(--text);
}
.detail-list {
  margin: 8px 0 0;
  padding: 0 4px 0 22px;
  font-size: 12px;
  color: var(--muted);
}
.detail-list li {
  margin: 4px 0;
  line-height: 1.6;
}
.detail-list .seq {
  margin-right: 6px;
  opacity: 0.7;
}
.detail-list .ts {
  margin-right: 10px;
}
.detail-list .pr {
  font-weight: 600;
  color: var(--text);
  margin-right: 10px;
}
.empty {
  color: var(--muted);
  text-align: center;
  padding: 40px 0;
  margin: 0;
}
</style>