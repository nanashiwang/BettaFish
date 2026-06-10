<template>
  <div v-if="loading" v-loading="true" class="loading-block" />
  <template v-else-if="data">
    <p class="muted">更新于 {{ data.updated_at }} · {{ data.disclaimer }}</p>
    <el-row :gutter="16">
      <el-col v-for="hit in data.hits" :key="hit.name" :xs="24" :md="8">
        <el-card shadow="hover" class="hit-card">
          <div class="hit-head">
            <h3>{{ hit.name }}</h3>
            <el-tag size="small" effect="plain">{{ hit.type }}</el-tag>
          </div>
          <div class="kv"><span class="muted">命中</span><span>{{ hit.match }}</span></div>
          <div class="kv"><span class="muted">场景</span><span>{{ hit.scenario }}</span></div>
          <div class="kv"><span class="muted">风险</span><span>{{ hit.risk }}</span></div>
          <div class="kv"><span class="muted">观察</span><span>{{ hit.next }}</span></div>
        </el-card>
      </el-col>
    </el-row>
  </template>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchMyFocus } from '../../api/radar'
import type { MyFocusResult } from '../../api/types'

const data = ref<MyFocusResult | null>(null)
const loading = ref(true)

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

.hit-card {
  border-radius: 12px;
  margin-bottom: 16px;
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
</style>
