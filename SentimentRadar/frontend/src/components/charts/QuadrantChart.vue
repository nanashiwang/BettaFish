<template>
  <v-chart class="quadrant-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ScatterPoint, StockScatterPoint } from '../../api/types'

type QuadrantPoint = StockScatterPoint | ScatterPoint

const props = defineProps<{ points: QuadrantPoint[] }>()

const LABEL_COLORS: Record<string, string> = {
  补涨观察: '#2DD4BF',
  先动股: '#fbbf24',
  高位风险: '#F05252',
  弱势回避: '#94A3B8',
  观察: '#3BA4F7',
}

const option = computed(() => {
  const values = props.points
  const returns = values.map((p) => pointReturn3d(p))
  const heats = values.map((p) => p.heat_z ?? 0)
  const xMin = Math.min(-3, ...returns) - 1
  const xMax = Math.max(8, ...returns) + 1
  const yMin = Math.min(-1, ...heats) - 0.5
  const yMax = Math.max(2.5, ...heats) + 0.5
  return {
    backgroundColor: 'transparent',
    grid: { left: 44, right: 20, top: 28, bottom: 36 },
    graphic: values.length
      ? []
      : [
          {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
              text: '暂无个股候选数据',
              fill: '#64748B',
              fontSize: 13,
            },
          },
        ],
    tooltip: {
      backgroundColor: '#101826',
      borderColor: '#2A3648',
      textStyle: { color: '#F1F5F9', fontSize: 12 },
      formatter: (params: { data: { point: QuadrantPoint } }) => {
        const p = params.data.point
        return `<b>${p.name} ${pointCode(p)}</b><br/>主题：${pointTopic(p)}<br/>场景：${p.scenario ?? '无显著信号'}<br/>标签：${pointLabel(p)}<br/>主题热度 z：${p.heat_z}<br/>个股 3 日：${formatPct(pointReturn3d(p))}<br/>个股 5 日：${formatPct(pointReturn5d(p))}<br/>量比：${pointVolumeRatio(p)}`
      },
    },
    xAxis: {
      name: '个股 3 日涨幅 →',
      nameLocation: 'end',
      nameTextStyle: { color: '#64748B', fontSize: 11 },
      min: xMin,
      max: xMax,
      axisLine: { lineStyle: { color: '#2A3648' } },
      axisLabel: {
        color: '#64748B',
        fontSize: 10,
        formatter: (value: number) => `${value}%`,
      },
      splitLine: { show: false },
    },
    yAxis: {
      name: '主题热度 z 分 ↑',
      nameTextStyle: { color: '#64748B', fontSize: 11 },
      min: yMin,
      max: yMax,
      axisLine: { lineStyle: { color: '#2A3648' } },
      axisLabel: { color: '#64748B', fontSize: 10 },
      splitLine: { show: false },
    },
    series: [
      {
        type: 'scatter',
        symbolSize: (value: number[], params: { data: { point: QuadrantPoint } }) => {
          const ratio = pointVolumeRatio(params.data.point)
          return Math.max(10, Math.min(24, 10 + ratio * 4))
        },
        data: values.map((p) => ({
          value: [pointReturn3d(p), p.heat_z],
          point: p,
          itemStyle: {
            color: LABEL_COLORS[pointLabel(p)] ?? '#64748B',
            shadowBlur: pointLabel(p) === '补涨观察' || pointLabel(p) === '高位风险' ? 12 : 0,
            shadowColor: LABEL_COLORS[pointLabel(p)] ?? 'transparent',
          },
        })),
        label: {
          show: true,
          position: 'top',
          color: '#94A3B8',
          fontSize: 10,
          formatter: (params: { data: { point: QuadrantPoint } }) => params.data.point.name,
        },
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: '#2A3648', type: 'dashed' },
          data: [{ xAxis: 0 }, { yAxis: 0.8 }, { xAxis: 8 }],
        },
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(59, 164, 247, 0.08)' },
          label: {
            show: true,
            color: '#3BA4F7',
            fontSize: 11,
            position: 'insideTopLeft',
          },
          data: [
            [
              { name: '补涨观察 · 热度先行', xAxis: -2, yAxis: yMax },
              { xAxis: 3, yAxis: 0.8 },
            ],
            [
              { name: '高位风险 · 价格先动', xAxis: 8, yAxis: yMax },
              { xAxis: xMax, yAxis: 0.8 },
            ],
          ],
        },
      },
    ],
  }
})

function formatPct(value: number | null) {
  if (value == null) return '-'
  return `${value > 0 ? '+' : ''}${value}%`
}

function isStockPoint(point: QuadrantPoint): point is StockScatterPoint {
  return 'return_3d' in point
}

function pointCode(point: QuadrantPoint) {
  return isStockPoint(point) ? point.code : ''
}

function pointTopic(point: QuadrantPoint) {
  return isStockPoint(point) ? point.topic : point.name
}

function pointLabel(point: QuadrantPoint) {
  if (isStockPoint(point)) return point.label
  if (point.scenario === '先动后闻') return '高位风险'
  if (point.scenario === '先闻后动') return '补涨观察'
  return '观察'
}

function pointReturn3d(point: QuadrantPoint) {
  return isStockPoint(point) ? point.return_3d ?? 0 : point.price_z
}

function pointReturn5d(point: QuadrantPoint) {
  return isStockPoint(point) ? point.return_5d : null
}

function pointVolumeRatio(point: QuadrantPoint) {
  return isStockPoint(point) ? point.volume_ratio || 1 : 1
}
</script>

<style scoped>
.quadrant-chart {
  width: 100%;
  height: 320px;
}
</style>
