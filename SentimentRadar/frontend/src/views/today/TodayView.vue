<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="今日信号" name="today">
        <div v-if="todayLoading" v-loading="true" class="loading-block" />
        <template v-else-if="today && today.cards.length">
          <!-- Hero：当日头条与统计 -->
          <section class="hero glass-card fade-up">
            <div class="hero-main">
              <h2>{{ today.headline }}</h2>
              <p class="muted">
                更新于 {{ today.updated_at }} · {{ today.version }} · {{ today.disclaimer }}
              </p>
            </div>
            <div class="hero-side">
              <StatChip
                v-for="item in today.my_related.items"
                :key="item.label"
                :label="item.label"
                :value="item.value"
              />
              <el-button :icon="Refresh" circle :loading="refreshing" @click="loadToday(true)" />
            </div>
          </section>

          <el-row :gutter="16">
            <el-col :xs="24" :lg="15">
              <div class="cards-stack">
                <div v-for="(card, index) in today.cards" :key="card.id" class="fade-up" :class="`fade-up-${index + 1}`">
                  <PredictionCard :card="card" @view-evidence="openDrawer" />
                </div>
              </div>
            </el-col>
            <el-col :xs="24" :lg="9">
              <div class="glass-card side-panel fade-up fade-up-2">
                <h3 class="section-title">信号象限图</h3>
                <QuadrantChart :points="today.signals_scatter" />
                <p class="faint quadrant-hint">
                  左上为「先闻后动」机会区：舆情升温而板块未动
                </p>
              </div>
              <div class="glass-card side-panel fade-up fade-up-3">
                <h3 class="section-title">{{ today.top_risk.title }}</h3>
                <div class="kv">
                  <span class="muted">等级</span>
                  <el-tag type="warning" size="small">{{ today.top_risk.level }}</el-tag>
                </div>
                <div class="kv"><span class="muted">范围</span><span>{{ today.top_risk.scope }}</span></div>
                <p class="risk-reason muted">{{ today.top_risk.reason }}</p>
              </div>
              <div class="glass-card side-panel fade-up fade-up-4">
                <h3 class="section-title">今日证据来源</h3>
                <div v-for="item in today.evidence_overview" :key="item.name" class="kv">
                  <span class="muted">{{ item.name }}</span>
                  <span class="num">{{ item.count.toLocaleString() }} 条</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </template>
        <el-empty v-else :description="today?.headline || '暂无预判数据'">
          <p class="muted empty-hint">
            管线尚未产出今日信号。管理员可在「管理后台 → 平台设置 → 雷达管线」中配置并立即运行。
          </p>
          <el-button type="primary" :loading="refreshing" @click="loadToday(true)">刷新</el-button>
        </el-empty>
      </el-tab-pane>

      <el-tab-pane label="我的关注" name="my" lazy>
        <MyFocusPanel @go-settings="activeTab = 'settings'" />
      </el-tab-pane>

      <el-tab-pane label="关注管理" name="settings" lazy>
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
import EvidenceDrawer from '../../components/today/EvidenceDrawer.vue'
import MyFocusPanel from '../../components/today/MyFocusPanel.vue'
import SettingsPanel from '../../components/today/SettingsPanel.vue'
import QuadrantChart from '../../components/charts/QuadrantChart.vue'
import StatChip from '../../components/common/StatChip.vue'

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
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 22px 26px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.hero-main h2 {
  margin: 0 0 8px;
  font-size: 18px;
  line-height: 1.5;
}

.hero-side {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.cards-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.side-panel {
  padding: 18px 20px;
  margin-bottom: 16px;
}

.quadrant-hint {
  margin: 8px 0 0;
  font-size: 12px;
}

.kv {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 5px 0;
}

.risk-reason {
  margin: 10px 0 0;
  line-height: 1.6;
}

.empty-hint {
  margin: 0 0 16px;
}
</style>
