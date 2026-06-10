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
import type { PredictionDetail } from '../../api/types'

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
</script>

<style scoped>
.loading-block {
  height: 200px;
}

.summary {
  font-size: 13px;
  line-height: 1.7;
  color: #475669;
}

h4 {
  margin: 18px 0 8px;
  font-size: 14px;
  color: var(--radar-brand);
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #475669;
  line-height: 1.8;
}

.timeline {
  padding-left: 4px;
  font-size: 13px;
}
</style>
