<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="今日预判" name="today">
        <div v-if="todayLoading" v-loading="true" class="loading-block" />
        <template v-else-if="today">
          <section class="hero">
            <div class="hero-head">
              <div>
                <h2>{{ today.headline }}</h2>
                <p class="muted">
                  更新于 {{ today.updated_at }} · {{ today.version }} · {{ today.disclaimer }}
                </p>
              </div>
              <el-button :icon="Refresh" circle :loading="refreshing" @click="loadToday(true)" />
            </div>
          </section>

          <el-row :gutter="16" class="cards-row">
            <el-col v-for="card in today.cards" :key="card.id" :xs="24" :md="8">
              <PredictionCard :card="card" @view-evidence="openDrawer" />
            </el-col>
          </el-row>

          <SummaryPanels
            :my-related="today.my_related"
            :top-risk="today.top_risk"
            :evidence-overview="today.evidence_overview"
          />
        </template>
      </el-tab-pane>

      <el-tab-pane label="我的关注" name="my" lazy>
        <MyFocusPanel />
      </el-tab-pane>

      <el-tab-pane label="设置" name="settings" lazy>
        <SettingsPanel />
      </el-tab-pane>
    </el-tabs>

    <EvidenceDrawer v-model="drawerVisible" :card-id="activeCardId" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { fetchToday } from '../../api/radar'
import type { TodayBriefing } from '../../api/types'
import PredictionCard from '../../components/today/PredictionCard.vue'
import SummaryPanels from '../../components/today/SummaryPanels.vue'
import EvidenceDrawer from '../../components/today/EvidenceDrawer.vue'
import MyFocusPanel from '../../components/today/MyFocusPanel.vue'
import SettingsPanel from '../../components/today/SettingsPanel.vue'

const activeTab = ref('today')
const today = ref<TodayBriefing | null>(null)
const todayLoading = ref(true)
const refreshing = ref(false)
const drawerVisible = ref(false)
const activeCardId = ref('')

async function loadToday(isRefresh = false) {
  if (isRefresh) refreshing.value = true
  try {
    today.value = await fetchToday()
  } finally {
    todayLoading.value = false
    refreshing.value = false
  }
}

function openDrawer(cardId: string) {
  activeCardId.value = cardId
  drawerVisible.value = true
}

onMounted(() => loadToday())
</script>

<style scoped>
.loading-block {
  height: 320px;
}

.hero {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 16px;
  border: 1px solid #e4e9ef;
}

.hero-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.hero h2 {
  margin: 0 0 8px;
  font-size: 18px;
  line-height: 1.5;
}

.cards-row {
  margin-bottom: 16px;
}
</style>
