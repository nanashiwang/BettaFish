<template>
  <el-drawer
    :model-value="modelValue"
    size="480px"
    :title="detail?.detail.title || '证据链解析'"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="load"
  >
    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="detail">
      <el-tag size="small" type="warning">{{ detail.detail.scenario }}</el-tag>
      <p class="summary">{{ detail.detail.summary }}</p>

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
