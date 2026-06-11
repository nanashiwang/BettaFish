<template>
  <v-chart class="sparkline" :option="option" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ data: number[] }>()

// A 股惯例：区间收涨为红、收跌为绿
const trendColor = computed(() => {
  if (props.data.length < 2) return '#64748B'
  return props.data[props.data.length - 1] >= props.data[0] ? '#F05252' : '#31C48D'
})

const option = computed(() => ({
  backgroundColor: 'transparent',
  grid: { left: 2, right: 2, top: 4, bottom: 2 },
  xAxis: { type: 'category', show: false, data: props.data.map((_, i) => i) },
  yAxis: { type: 'value', show: false, min: 'dataMin', max: 'dataMax' },
  series: [
    {
      type: 'line',
      data: props.data,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: trendColor.value },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: `${trendColor.value}55` },
            { offset: 1, color: `${trendColor.value}00` },
          ],
        },
      },
    },
  ],
}))
</script>

<style scoped>
.sparkline {
  width: 100%;
  height: 44px;
}
</style>
