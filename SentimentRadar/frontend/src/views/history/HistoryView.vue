<template>
  <div>
    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="history">
      <!-- 胜率统计 -->
      <div class="stats-row fade-up">
        <StatChip label="累计信号" :value="history.stats.total ?? 0" />
        <StatChip label="已验证" :value="history.stats.evaluated ?? 0" sub="信号发出 3 个交易日后回填" />
        <StatChip
          label="3 日胜率"
          :value="history.stats.win_rate_3d != null ? `${history.stats.win_rate_3d}%` : '待积累'"
          :tone="history.stats.win_rate_3d != null && history.stats.win_rate_3d >= 50 ? 'up' : ''"
        />
        <StatChip
          label="平均 3 日收益"
          :value="history.stats.avg_return_3d != null ? `${history.stats.avg_return_3d}%` : '待积累'"
          :tone="returnTone(history.stats.avg_return_3d)"
        />
      </div>

      <!-- 分场景胜率 -->
      <div v-if="scenarioEntries.length" class="glass-card scenario-stats fade-up fade-up-1">
        <h3 class="section-title">分场景表现</h3>
        <div class="scenario-grid">
          <div v-for="[name, stat] in scenarioEntries" :key="name" class="scenario-item">
            <span class="scenario-name" :class="scenarioClass(name)">{{ name }}</span>
            <span class="muted num">{{ stat.count }} 条</span>
            <span class="num win-rate">{{ stat.win_rate != null ? `胜率 ${stat.win_rate}%` : '待验证' }}</span>
          </div>
        </div>
      </div>

      <!-- 历史时间线 -->
      <div v-for="(day, index) in history.days" :key="day.date" class="day-group fade-up" :class="`fade-up-${Math.min(index + 2, 4)}`">
        <div class="day-label">
          <span class="num">{{ day.date }}</span>
          <span class="day-line" />
        </div>
        <div class="day-cards">
          <div v-for="card in day.cards" :key="card.id" class="glass-card hoverable history-card" :class="scenarioClass(card.scenario)">
            <div class="history-head">
              <span class="scenario-badge">{{ card.scenario }}</span>
              <h4>{{ card.title }}</h4>
              <span class="faint">{{ card.boards.map((b) => b.name).join('、') }}</span>
            </div>
            <p class="muted judgement">{{ card.judgement }}</p>
            <div class="returns">
              <span v-for="period in RETURN_PERIODS" :key="period.key" class="return-item">
                <span class="faint">{{ period.label }}</span>
                <b v-if="card[period.key] != null" class="num" :class="returnTone(card[period.key])">
                  {{ formatReturn(card[period.key]) }}
                </b>
                <span v-else class="faint">待验证</span>
              </span>
              <span class="return-item">
                <span class="faint">信号</span>
                <span class="num muted">热度z {{ card.heat_z }} / 价格z {{ card.price_z }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-if="!history.days.length" description="暂无历史信号，管线运行后将逐日积累" />
      <p v-else class="faint disclaimer">{{ history.disclaimer }} · 收益为信号板块的事后统计，不代表任何收益承诺</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchHistory } from '../../api/radar'
import type { HistoryCard, HistoryResult } from '../../api/types'
import StatChip from '../../components/common/StatChip.vue'

const history = ref<HistoryResult | null>(null)
const loading = ref(true)

const RETURN_PERIODS: { key: 'return_1d' | 'return_3d' | 'return_5d'; label: string }[] = [
  { key: 'return_1d', label: '1 日' },
  { key: 'return_3d', label: '3 日' },
  { key: 'return_5d', label: '5 日' },
]

const scenarioEntries = computed(() =>
  Object.entries(history.value?.stats.by_scenario ?? {}),
)

function scenarioClass(scenario: string) {
  if (scenario === '先闻后动') return 'scenario-news-first'
  if (scenario === '同步共振') return 'scenario-resonance'
  return 'scenario-move-first'
}

function returnTone(value: number | null | undefined): 'up' | 'down' | '' {
  if (value == null) return ''
  return value > 0 ? 'up' : value < 0 ? 'down' : ''
}

function formatReturn(value: unknown): string {
  const num = Number(value)
  return `${num > 0 ? '+' : ''}${num}%`
}

onMounted(async () => {
  try {
    history.value = await fetchHistory()
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
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.scenario-stats {
  padding: 18px 20px;
  margin-bottom: 22px;
}

.scenario-grid {
  display: flex;
  gap: 28px;
  flex-wrap: wrap;
}

.scenario-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.scenario-name {
  color: var(--scenario-color);
  font-weight: 600;
}

.win-rate {
  color: var(--text-primary);
}

.day-group {
  margin-bottom: 22px;
}

.day-label {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.day-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--glass-border), transparent);
}

.day-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  padding: 16px 20px;
  border-left: 3px solid var(--scenario-color);
}

.history-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.history-head h4 {
  margin: 0;
  font-size: 15px;
}

.scenario-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--scenario-color);
  background: color-mix(in srgb, var(--scenario-color) 14%, transparent);
  padding: 2px 10px;
  border-radius: 999px;
}

.judgement {
  margin: 8px 0 10px;
  line-height: 1.6;
}

.returns {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  font-size: 13px;
}

.return-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.disclaimer {
  text-align: center;
  font-size: 12px;
  margin-top: 8px;
}
</style>
