<template>
  <div v-if="loading" v-loading="true" class="loading-block" />
  <template v-else-if="data">
    <p class="muted head-line">更新于 {{ data.updated_at }} · {{ data.disclaimer }}</p>
    <el-row v-if="data.hits.length" :gutter="16">
      <el-col v-for="hit in data.hits" :key="hit.name" :xs="24" :md="8">
        <div class="glass-card hoverable hit-card" :class="scenarioClass(hit.scenario)">
          <div class="hit-head">
            <h3>{{ hit.name }}</h3>
            <el-tag size="small" effect="plain">{{ hit.type }}</el-tag>
          </div>
          <div class="kv"><span class="muted">命中话题</span><span>{{ hit.match }}</span></div>
          <div class="kv">
            <span class="muted">场景</span>
            <span class="scenario-text">{{ hit.scenario }}</span>
          </div>
          <div class="kv"><span class="muted">风险</span><span>{{ hit.risk }}</span></div>
          <div class="kv"><span class="muted">观察</span><span>{{ hit.next }}</span></div>
        </div>
      </el-col>
    </el-row>
    <el-empty v-else description="今日暂无关注命中">
      <p class="muted empty-hint">
        {{ data.watchlist.length ? '你关注的对象今日未出现在热点话题中' : '还没有关注任何对象' }}
      </p>
      <el-button type="primary" @click="$emit('go-settings')">去管理关注</el-button>
    </el-empty>
  </template>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchMyFocus } from '../../api/radar'
import type { MyFocusResult } from '../../api/types'

defineEmits<{ 'go-settings': [] }>()

const data = ref<MyFocusResult | null>(null)
const loading = ref(true)

function scenarioClass(scenario: string) {
  if (scenario === '先闻后动') return 'scenario-news-first'
  if (scenario === '同步共振') return 'scenario-resonance'
  if (scenario === '先动后闻') return 'scenario-move-first'
  return ''
}

onMounted(async () => {
  try {
    data.value = await fetchMyFocus()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.loading-block {
  height: 240px;
}

.head-line {
  margin: 0 0 14px;
}

.hit-card {
  padding: 18px 20px;
  margin-bottom: 16px;
  border-left: 3px solid var(--scenario-color, var(--glass-border));
}

.hit-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.hit-head h3 {
  margin: 0;
  font-size: 15px;
}

.kv {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  padding: 4px 0;
}

.kv span:last-child {
  text-align: right;
}

.scenario-text {
  color: var(--scenario-color, var(--text-primary));
  font-weight: 600;
}

.empty-hint {
  margin: 0 0 16px;
}
</style>
