<template>
  <v-chart class="quadrant-chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ScatterPoint } from '../../api/types'

const props = defineProps<{ points: ScatterPoint[] }>()

const SCENARIO_COLORS: Record<string, string> = {
  先闻后动: '#3BA4F7',
  同步共振: '#2DD4BF',
  先动后闻: '#fbbf24',
}

const option = computed(() => {
  const values = props.points
  const maxAbs = Math.max(2.5, ...values.flatMap((p) => [Math.abs(p.heat_z), Math.abs(p.price_z)])) * 1.15
  return {
    backgroundColor: 'transparent',
    grid: { left: 44, right: 20, top: 28, bottom: 36 },
    tooltip: {
      backgroundColor: '#101826',
      borderColor: '#2A3648',
      textStyle: { color: '#F1F5F9', fontSize: 12 },
      formatter: (params: { data: { point: ScatterPoint } }) => {
        const p = params.data.point
        return `<b>${p.name}</b><br/>热度 z：${p.heat_z}<br/>价格 z：${p.price_z}<br/>${p.scenario ?? '无显著信号'}`
      },
    },
    xAxis: {
      name: '价格 z 分 →',
      nameLocation: 'end',
      nameTextStyle: { color: '#64748B', fontSize: 11 },
      min: -maxAbs,
      max: maxAbs,
      axisLine: { lineStyle: { color: '#2A3648' } },
      axisLabel: { color: '#64748B', fontSize: 10 },
      splitLine: { show: false },
    },
    yAxis: {
      name: '热度 z 分 ↑',
      nameTextStyle: { color: '#64748B', fontSize: 11 },
      min: -maxAbs,
      max: maxAbs,
      axisLine: { lineStyle: { color: '#2A3648' } },
      axisLabel: { color: '#64748B', fontSize: 10 },
      splitLine: { show: false },
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 14,
        data: values.map((p) => ({
          value: [p.price_z, p.heat_z],
          point: p,
          itemStyle: {
            color: p.scenario ? SCENARIO_COLORS[p.scenario] ?? '#64748B' : 'rgba(100,116,139,0.6)',
            shadowBlur: p.scenario ? 12 : 0,
            shadowColor: p.scenario ? SCENARIO_COLORS[p.scenario] ?? 'transparent' : 'transparent',
          },
        })),
        label: {
          show: true,
          position: 'top',
          color: '#94A3B8',
          fontSize: 10,
          formatter: (params: { data: { point: ScatterPoint } }) => params.data.point.name,
        },
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: '#2A3648', type: 'dashed' },
          data: [{ xAxis: 0 }, { yAxis: 0 }],
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
              { name: '先闻后动 · 机会区', xAxis: -maxAbs, yAxis: maxAbs },
              { xAxis: 0, yAxis: 0.8 },
            ],
          ],
        },
      },
    ],
  }
})
</script>

<style scoped>
.quadrant-chart {
  width: 100%;
  height: 320px;
}
</style>
