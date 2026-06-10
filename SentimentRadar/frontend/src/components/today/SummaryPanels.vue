<template>
  <el-row :gutter="16">
    <el-col :xs="24" :md="8">
      <el-card shadow="never" class="panel">
        <template #header>{{ myRelated.summary }}</template>
        <p class="highlight">{{ myRelated.highlight }}</p>
        <div v-for="item in myRelated.items" :key="item.label" class="kv">
          <span class="muted">{{ item.label }}</span>
          <span>{{ item.value }}</span>
        </div>
      </el-card>
    </el-col>

    <el-col :xs="24" :md="8">
      <el-card shadow="never" class="panel risk-panel">
        <template #header>{{ topRisk.title }}</template>
        <div class="kv">
          <span class="muted">等级</span>
          <el-tag type="danger" size="small">{{ topRisk.level }}</el-tag>
        </div>
        <div class="kv">
          <span class="muted">范围</span>
          <span>{{ topRisk.scope }}</span>
        </div>
        <p class="reason">{{ topRisk.reason }}</p>
      </el-card>
    </el-col>

    <el-col :xs="24" :md="8">
      <el-card shadow="never" class="panel">
        <template #header>今日证据概览</template>
        <div v-for="item in evidenceOverview" :key="item.name" class="kv">
          <span class="muted">{{ item.name }}</span>
          <span>{{ item.count.toLocaleString() }} 条</span>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import type { TodayBriefing } from '../../api/types'

defineProps<{
  myRelated: TodayBriefing['my_related']
  topRisk: TodayBriefing['top_risk']
  evidenceOverview: TodayBriefing['evidence_overview']
}>()
</script>

<style scoped>
.panel {
  border-radius: 12px;
  height: 100%;
}

.highlight {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #475669;
}

.kv {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 5px 0;
}

.reason {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #475669;
}
</style>
