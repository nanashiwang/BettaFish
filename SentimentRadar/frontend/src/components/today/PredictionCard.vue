<template>
  <article class="prediction-card glass-card hoverable" :class="scenarioClass">
    <div class="card-head">
      <span class="scenario-badge">{{ card.scenario }}</span>
      <span class="rank num">#{{ card.rank }}</span>
    </div>
    <h3>{{ card.title }}</h3>
    <p class="judgement">{{ card.judgement }}</p>
    <div class="rows">
      <div class="row"><span class="label">依据</span>{{ card.reason }}</div>
      <div class="row"><span class="label">风险</span>{{ card.risk }}</div>
      <div class="row"><span class="label">关注</span>{{ card.next }}</div>
    </div>
    <div class="metrics" v-if="card.heat_z != null">
      <span class="metric">热度 z <b class="num">{{ card.heat_z }}</b></span>
      <span class="metric">价格 z <b class="num">{{ card.price_z }}</b></span>
      <span class="metric">强度 <b>{{ card.strength }}</b></span>
    </div>
    <div v-if="topStocks.length" class="stock-pool">
      <div class="stock-pool-head">
        <span>个股观察池</span>
        <small>非买卖建议 · 看异动顺序</small>
      </div>
      <div class="stock-list">
        <div v-for="stock in topStocks" :key="stock.code" class="stock-item">
          <div>
            <strong>{{ stock.name }}</strong>
            <small>{{ stock.code }}</small>
          </div>
          <el-tag size="small" effect="dark" :type="stockTagType(stock.label)">
            {{ stock.label }}
          </el-tag>
          <span class="stock-metric num">3日 {{ formatPct(stock.return_3d) }}</span>
          <span class="stock-metric num">量比 {{ stock.volume_ratio }}</span>
        </div>
      </div>
    </div>
    <div class="tags">
      <el-tag v-for="tag in card.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
    </div>
    <div v-if="card.board_trend && card.board_trend.length > 1" class="trend">
      <div class="trend-head">
        <span class="muted">{{ card.board_name }} · 近 30 日</span>
      </div>
      <Sparkline :data="card.board_trend" />
    </div>
    <div class="card-foot">
      <span class="faint">{{ card.evidence }}</span>
      <el-button type="primary" link @click="$emit('view-evidence', card.id)">证据链 →</el-button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PredictionCard, StockCandidate } from '../../api/types'
import Sparkline from '../charts/Sparkline.vue'

const props = defineProps<{ card: PredictionCard }>()
defineEmits<{ 'view-evidence': [cardId: string] }>()

const scenarioClass = computed(() => {
  if (props.card.scenario === '先闻后动') return 'scenario-news-first'
  if (props.card.scenario === '同步共振') return 'scenario-resonance'
  return 'scenario-move-first'
})

const topStocks = computed(() => (props.card.stock_candidates || []).slice(0, 4))

function formatPct(value: number | null) {
  if (value == null) return '-'
  return `${value > 0 ? '+' : ''}${value}%`
}

function stockTagType(label: StockCandidate['label']) {
  if (label === '高位风险' || label === '弱势回避') return 'danger'
  if (label === '先动股') return 'warning'
  if (label === '补涨观察') return 'success'
  return 'info'
}
</script>

<style scoped>
.prediction-card {
  position: relative;
  height: 100%;
  padding: 16px;
  overflow: hidden;
  background:
    radial-gradient(circle at 92% 8%, color-mix(in srgb, var(--scenario-color) 14%, transparent), transparent 36%),
    var(--bg-elevated);
}

/* 场景色条与辉光 */
.prediction-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--scenario-color);
  box-shadow: 0 0 16px var(--scenario-color);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.scenario-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--scenario-color);
  background: color-mix(in srgb, var(--scenario-color) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--scenario-color) 35%, transparent);
  padding: 3px 10px;
  border-radius: 999px;
}

.rank {
  color: var(--text-faint);
  font-weight: 700;
  font-size: 18px;
}

h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--text-primary);
}

.judgement {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.rows {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 12px;
}

.row {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.label {
  display: inline-block;
  color: var(--scenario-color);
  font-weight: 600;
  margin-right: 6px;
}

.metrics {
  display: flex;
  gap: 14px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--text-faint);
}

.metric b {
  color: var(--text-primary);
  margin-left: 2px;
}

.stock-pool {
  margin: 2px 0 12px;
  padding: 10px;
  border-radius: 10px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
}

.stock-pool-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 600;
}

.stock-pool-head small {
  color: var(--text-faint);
  font-weight: 400;
}

.stock-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.stock-item {
  display: grid;
  grid-template-columns: minmax(80px, 1fr) auto;
  gap: 4px 8px;
  align-items: center;
  padding: 8px;
  border-radius: 10px;
  background: var(--bg-elevated);
  border: 1px solid rgba(42, 54, 72, 0.72);
}

.stock-item strong {
  display: block;
  font-size: 13px;
}

.stock-item small {
  display: block;
  margin-top: 2px;
  color: var(--text-faint);
  font-size: 11px;
}

.stock-metric {
  color: var(--text-faint);
  font-size: 11px;
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.trend {
  margin: 0 -6px 10px;
}

.trend-head {
  font-size: 11px;
  padding: 0 6px 2px;
}

.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

@media (max-width: 720px) {
  .stock-list {
    grid-template-columns: 1fr;
  }
}
</style>
