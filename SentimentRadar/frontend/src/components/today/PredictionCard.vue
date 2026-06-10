<template>
  <el-card class="prediction-card" shadow="hover">
    <div class="card-head">
      <el-tag size="small" :type="strengthTagType">强度 {{ card.strength }}</el-tag>
      <span class="rank">#{{ card.rank }}</span>
    </div>
    <h3>{{ card.title }}</h3>
    <p class="judgement">{{ card.judgement }}</p>
    <div class="rows">
      <div class="row"><span class="label">依据</span>{{ card.reason }}</div>
      <div class="row"><span class="label">风险</span>{{ card.risk }}</div>
      <div class="row"><span class="label">关注</span>{{ card.next }}</div>
    </div>
    <div class="tags">
      <el-tag v-for="tag in card.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
    </div>
    <div class="card-foot">
      <span class="muted">{{ card.evidence }}</span>
      <el-button type="primary" link @click="$emit('view-evidence', card.id)">查看证据 →</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PredictionCard } from '../../api/types'

const props = defineProps<{ card: PredictionCard }>()
defineEmits<{ 'view-evidence': [cardId: string] }>()

const strengthTagType = computed(() => {
  if (props.card.strength.includes('高')) return 'danger'
  if (props.card.strength.includes('中')) return 'warning'
  return 'info'
})
</script>

<style scoped>
.prediction-card {
  height: 100%;
  border-radius: 12px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.rank {
  color: #c0ccda;
  font-weight: 700;
  font-size: 18px;
}

h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.judgement {
  margin: 0 0 12px;
  font-size: 13px;
  color: #475669;
  line-height: 1.6;
}

.rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.row {
  font-size: 13px;
  color: #475669;
  line-height: 1.5;
}

.label {
  display: inline-block;
  color: var(--radar-brand);
  font-weight: 600;
  margin-right: 6px;
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
