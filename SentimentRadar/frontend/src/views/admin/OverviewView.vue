<template>
  <div>
    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="overview">
      <p class="muted">更新于 {{ overview.updated_at }}</p>

      <el-row :gutter="16" class="stats-row">
        <el-col v-for="stat in overview.stats" :key="stat.label" :xs="12" :md="6">
          <el-card shadow="never" class="stat-card" :class="`tone-${stat.tone}`">
            <div class="muted">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-trend muted">{{ stat.trend }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :md="14">
          <el-card shadow="never" class="panel">
            <template #header>近 7 日活跃趋势</template>
            <div class="trend-chart">
              <div v-for="point in overview.trend" :key="point.day" class="trend-bar-wrap">
                <div
                  class="trend-bar"
                  :style="{ height: `${(point.active / maxActive) * 100}%` }"
                  :title="`${point.day}: ${point.active}`"
                />
                <span class="muted">{{ point.day }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="10">
          <el-card shadow="never" class="panel">
            <template #header>数据源状态</template>
            <el-table :data="overview.data_sources" size="small">
              <el-table-column prop="name" label="数据源" />
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="sourceTagType(row.status)" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="note" label="备注" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchOverview } from '../../api/admin'
import type { AdminOverview } from '../../api/types'

const overview = ref<AdminOverview | null>(null)
const loading = ref(true)

const maxActive = computed(() =>
  Math.max(...(overview.value?.trend.map((point) => point.active) ?? [1])),
)

function sourceTagType(status: string) {
  if (status === '正常') return 'success'
  if (status === '注意') return 'warning'
  return 'info'
}

onMounted(async () => {
  try {
    overview.value = await fetchOverview()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.loading-block {
  height: 320px;
}

.stats-row {
  margin: 12px 0 4px;
}

.stat-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  margin: 6px 0;
}

.tone-blue .stat-value { color: var(--accent); }
.tone-ok .stat-value { color: var(--brand); }
.tone-warn .stat-value { color: #fbbf24; }
.tone-danger .stat-value { color: var(--up); }

.panel {
  border-radius: 12px;
  margin-bottom: 16px;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 180px;
  padding: 10px 4px 0;
}

.trend-bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: 6px;
  font-size: 12px;
}

.trend-bar {
  width: 100%;
  max-width: 42px;
  background: linear-gradient(180deg, var(--brand), var(--accent));
  border-radius: 6px 6px 0 0;
  min-height: 6px;
  box-shadow: 0 0 12px rgba(45, 212, 191, 0.25);
}
</style>
