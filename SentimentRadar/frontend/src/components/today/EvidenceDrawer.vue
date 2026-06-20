<template>
  <el-drawer
    :model-value="modelValue"
    size="620px"
    :title="detail?.detail.title || '证据链解析'"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="load"
  >
    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="detail">
      <el-tag size="small" type="warning">{{ detail.detail.scenario }}</el-tag>
      <p class="summary">{{ detail.detail.summary }}</p>

      <section class="causal-panel">
        <div class="causal-title">
          <span>为什么动</span>
          <el-tag size="small" effect="plain">{{ detail.detail.confidence || '证据不足' }}</el-tag>
        </div>
        <p>{{ detail.detail.causal_summary || '当前缺少可追溯来源，暂不做明确归因。' }}</p>
      </section>

      <h4>驱动链路</h4>
      <div class="causal-chain">
        <div v-for="(item, index) in detail.detail.causal_chain || []" :key="`${item.step}-${index}`" class="chain-step">
          <span class="step-index">{{ index + 1 }}</span>
          <div>
            <strong>{{ item.step }}</strong>
            <p>{{ item.text }}</p>
          </div>
        </div>
      </div>

      <h4>真实来源依据</h4>
      <el-table :data="detail.detail.evidence_basis || []" size="small" empty-text="暂无可追溯来源">
        <el-table-column prop="source" label="来源" width="90" />
        <el-table-column prop="type" label="类型" width="90" />
        <el-table-column prop="credibility" label="可信度" width="78" />
        <el-table-column label="标题与采用原因" min-width="260">
          <template #default="{ row }">
            <el-link v-if="row.url" :href="row.url" target="_blank" type="primary">
              {{ row.title }}
            </el-link>
            <span v-else>{{ row.title }}</span>
            <div class="source-note">{{ row.note }}</div>
          </template>
        </el-table-column>
      </el-table>

      <h4>为什么这样判断</h4>
      <ul class="plain-list">
        <li v-for="(item, index) in detail.detail.why" :key="index">{{ item }}</li>
      </ul>

      <h4>时间线</h4>
      <el-timeline class="timeline">
        <el-timeline-item v-for="item in detail.detail.timeline" :key="item.time" :timestamp="item.time">
          <strong>{{ item.label }}</strong>：{{ item.text }}
        </el-timeline-item>
      </el-timeline>

      <h4>证据链</h4>
      <el-table :data="detail.detail.evidence_chain" size="small">
        <el-table-column prop="source" label="来源" width="100" />
        <el-table-column prop="count" label="数量" width="60" />
        <el-table-column prop="credibility" label="可信度" width="80" />
        <el-table-column prop="note" label="备注" />
      </el-table>

      <h4>反证提醒</h4>
      <ul class="plain-list warning-list">
        <li v-for="(item, index) in detail.detail.counter_evidence || []" :key="index">{{ item }}</li>
      </ul>

      <h4>个股观察池</h4>
      <el-table :data="detail.detail.stock_candidates || []" size="small" empty-text="暂无个股候选" :fit="false">
        <el-table-column prop="name" label="股票" width="92">
          <template #default="{ row }">
            <div class="stock-name">{{ row.name }}</div>
            <div class="stock-code">{{ row.code }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="label" label="标签" width="88" />
        <el-table-column label="3日" width="70">
          <template #default="{ row }">{{ formatPct(row.return_3d) }}</template>
        </el-table-column>
        <el-table-column label="量比" width="70">
          <template #default="{ row }">{{ row.volume_ratio }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="入池原因" />
        <el-table-column label="补充证据" width="240" show-overflow-tooltip>
          <template #default="{ row }">{{ stockEvidence(row) }}</template>
        </el-table-column>
      </el-table>

      <h4>风险边界</h4>
      <ul class="plain-list">
        <li v-for="(item, index) in detail.detail.risk_boundary" :key="index">{{ item }}</li>
      </ul>

      <h4>后续观察</h4>
      <ul class="plain-list">
        <li v-for="(item, index) in detail.detail.next_watch" :key="index">{{ item }}</li>
      </ul>

      <p class="muted">{{ detail.disclaimer }} · 更新于 {{ detail.updated_at }}</p>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { fetchPredictionDetail } from '../../api/radar'
import type { PredictionDetail, StockCandidate } from '../../api/types'

const props = defineProps<{ modelValue: boolean; cardId: string }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()

const detail = ref<PredictionDetail | null>(null)
const loading = ref(false)

async function load() {
  if (!props.cardId) return
  loading.value = true
  detail.value = null
  try {
    detail.value = await fetchPredictionDetail(props.cardId)
  } finally {
    loading.value = false
  }
}

function formatPct(value?: number | null) {
  if (value == null) return '-'
  return `${value > 0 ? '+' : ''}${value}%`
}

function formatNumber(value?: number | null, digits = 1) {
  if (value == null) return '-'
  return Number(value).toFixed(digits)
}

function formatFlow(value?: number | null) {
  if (value == null) return '-'
  if (Math.abs(value) >= 10000) return `${value > 0 ? '+' : ''}${(value / 10000).toFixed(2)}亿`
  return `${value > 0 ? '+' : ''}${value.toFixed(0)}万`
}

function stockEvidence(stock: StockCandidate) {
  const parts = []
  if (stock.company_profile) {
    parts.push([stock.company_profile.soe_tag, stock.company_profile.industry].filter(Boolean).join(' · '))
  }
  if (stock.quote_metrics?.turnover_rate != null) {
    parts.push(`换手${formatNumber(stock.quote_metrics.turnover_rate)}%`)
  }
  if (stock.financial) {
    parts.push(`营收${formatPct(stock.financial.revenue_yoy)} / 净利${formatPct(stock.financial.profit_yoy)}`)
  }
  if (stock.announcements?.[0]) {
    parts.push(`${stock.announcements[0].type}：${stock.announcements[0].title}`)
  }
  if (stock.money_flow) {
    parts.push(`个股资金${formatFlow(stock.money_flow.net_mf_amount)}`)
  }
  if (stock.board_money_flow) {
    parts.push(`板块资金${formatFlow(stock.board_money_flow.net_mf_amount)}`)
  }
  return parts.filter(Boolean).join('；') || '-'
}
</script>

<style scoped>
.loading-block {
  height: 200px;
}

.summary {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}

.causal-panel {
  margin: 12px 0 16px;
  padding: 14px;
  border: 1px solid rgba(20, 126, 245, 0.22);
  border-radius: 14px;
  background:
    radial-gradient(circle at 92% 10%, rgba(20, 126, 245, 0.12), transparent 42%),
    var(--bg-panel);
}

.causal-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--brand);
  font-weight: 900;
}

.causal-panel p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.causal-chain {
  display: grid;
  gap: 10px;
}

.chain-step {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-panel);
}

.step-index {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--brand-dim);
  color: var(--brand);
  font-weight: 900;
}

.chain-step strong,
.chain-step p {
  display: block;
}

.chain-step strong {
  margin-bottom: 3px;
  font-size: 13px;
}

.chain-step p,
.source-note {
  margin: 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.6;
}

.source-note {
  margin-top: 4px;
}

h4 {
  margin: 18px 0 8px;
  font-size: 14px;
  color: var(--brand);
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
}

.warning-list {
  color: var(--risk);
}

.timeline {
  padding-left: 4px;
  font-size: 13px;
}

.stock-name {
  font-weight: 600;
}

.stock-code {
  color: var(--text-faint);
  font-size: 11px;
}
</style>
