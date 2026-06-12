<template>
  <div class="candidates-page">
    <section class="candidate-hero glass-card fade-up">
      <div>
        <span class="eyebrow">STOCK MAP</span>
        <h1>候选股票象限</h1>
        <p>横轴看个股 3 日涨幅，纵轴看主题热度 z 分，优先观察热度先行但价格尚未充分反应的股票。</p>
      </div>
      <el-button :icon="Refresh" circle :loading="loading" @click="loadToday" />
    </section>

    <div v-if="loading" v-loading="true" class="loading-block glass-card" />

    <template v-else-if="today">
      <section class="stat-grid fade-up fade-up-1">
        <div v-for="stat in stats" :key="stat.label" class="stat-card glass-card">
          <span>{{ stat.label }}</span>
          <b class="num">{{ stat.value }}</b>
          <small>{{ stat.text }}</small>
        </div>
      </section>

      <section class="map-grid">
        <div class="glass-card panel map-panel fade-up fade-up-2">
          <div class="panel-head">
            <span>主题热度 × 个股涨幅</span>
            <small>{{ today.updated_at }}</small>
          </div>
          <div class="panel-body">
            <QuadrantChart :points="stockScatterPoints" />
            <p class="hint">左上为「补涨观察」，右上多为「高位风险」；这里只做舆情观察，不构成买卖建议。</p>
          </div>
        </div>

        <div class="glass-card panel fade-up fade-up-3">
          <div class="panel-head">
            <span>候选股票明细</span>
            <small>{{ stockScatterPoints.length }} 只</small>
          </div>
          <div class="panel-body table-wrap">
            <el-table :data="stockScatterPoints" size="small" height="430" :fit="false">
              <el-table-column prop="name" label="股票" min-width="120" fixed="left" />
              <el-table-column prop="code" label="代码" min-width="115" />
              <el-table-column prop="topic" label="主题" min-width="150" show-overflow-tooltip />
              <el-table-column label="标签" min-width="110">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain" :type="tagType(row.label)">{{ row.label }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="heat_z" label="热度 z" min-width="95" sortable />
              <el-table-column prop="return_3d" label="3日涨幅" min-width="100" sortable>
                <template #default="{ row }">{{ formatPct(row.return_3d) }}</template>
              </el-table-column>
              <el-table-column prop="return_5d" label="5日涨幅" min-width="100" sortable>
                <template #default="{ row }">{{ formatPct(row.return_5d) }}</template>
              </el-table-column>
              <el-table-column prop="volume_ratio" label="量比" min-width="90" sortable />
            </el-table>
          </div>
        </div>
      </section>
    </template>

    <el-empty v-else description="暂无候选股票数据">
      <el-button type="primary" :loading="loading" @click="loadToday">刷新</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { fetchToday } from '../../api/radar'
import type { StockScatterPoint, TodayBriefing } from '../../api/types'
import QuadrantChart from '../../components/charts/QuadrantChart.vue'

const today = ref<TodayBriefing | null>(null)
const loading = ref(true)

const stockScatterPoints = computed<StockScatterPoint[]>(() => {
  const points: StockScatterPoint[] = []
  const seen = new Set<string>()
  for (const card of today.value?.cards ?? []) {
    for (const stock of card.stock_candidates ?? []) {
      if (seen.has(stock.code)) continue
      seen.add(stock.code)
      points.push({
        name: stock.name,
        code: stock.code,
        label: stock.label,
        topic: card.title,
        scenario: card.scenario,
        heat_z: card.heat_z ?? 0,
        return_3d: stock.return_3d,
        return_5d: stock.return_5d,
        volume_ratio: stock.volume_ratio,
      })
    }
  }
  return points
})

const stats = computed(() => {
  const points = stockScatterPoints.value
  return [
    { label: '候选股票', value: points.length, text: '去重后的观察池' },
    { label: '补涨观察', value: points.filter((p) => p.label === '补涨观察').length, text: '热度高涨幅低' },
    { label: '高位风险', value: points.filter((p) => p.label === '高位风险').length, text: '价格已明显先动' },
    { label: '弱势回避', value: points.filter((p) => p.label === '弱势回避').length, text: '热度或价格偏弱' },
  ]
})

async function loadToday() {
  loading.value = true
  try {
    today.value = await fetchToday()
  } finally {
    loading.value = false
  }
}

function formatPct(value: number | null) {
  if (value == null) return '-'
  return `${value > 0 ? '+' : ''}${value}%`
}

function tagType(label: string) {
  if (label === '补涨观察') return 'success'
  if (label === '高位风险') return 'danger'
  if (label === '先动股') return 'warning'
  return 'info'
}

onMounted(loadToday)
</script>

<style scoped>
.candidates-page {
  display: grid;
  gap: 16px;
}

.candidate-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 22px;
  background:
    radial-gradient(circle at 88% 10%, rgba(59, 164, 247, 0.2), transparent 34%),
    linear-gradient(135deg, rgba(16, 24, 38, 0.98), rgba(13, 20, 32, 0.92));
}

.eyebrow {
  color: var(--brand-secondary);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.candidate-hero h1 {
  margin: 8px 0;
  font-size: 30px;
}

.candidate-hero p {
  max-width: 760px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.loading-block {
  height: 360px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  min-height: 112px;
  padding: 18px;
  background: var(--bg-elevated);
}

.stat-card span,
.stat-card small {
  display: block;
  color: var(--text-muted);
  font-size: 13px;
}

.stat-card b {
  display: block;
  margin: 8px 0 4px;
  color: var(--text-primary);
  font-size: 30px;
}

.map-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

.panel {
  overflow: hidden;
}

.panel-head {
  min-height: 46px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border);
  font-weight: 800;
}

.panel-head small {
  color: var(--text-faint);
  font-size: 12px;
}

.panel-body {
  padding: 18px;
}

.map-panel :deep(.quadrant-chart) {
  height: 500px;
}

.hint {
  margin: 12px 0 0;
  color: var(--text-faint);
  font-size: 13px;
  line-height: 1.7;
}

.table-wrap {
  overflow-x: auto;
}

@media (max-width: 1080px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .candidate-hero {
    align-items: flex-start;
    flex-direction: column;
  }

  .stat-grid {
    grid-template-columns: 1fr;
  }

  .map-panel :deep(.quadrant-chart) {
    height: 360px;
  }
}
</style>
