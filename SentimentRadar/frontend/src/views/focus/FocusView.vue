<template>
  <div class="focus-page">
    <section class="focus-hero glass-card fade-up">
      <div>
        <span class="eyebrow">WATCHLIST</span>
        <h1>我的关注</h1>
        <p>集中管理股票、主题和板块关注池；命中今日主线时会在这里直接提示。</p>
      </div>
      <el-button :icon="Refresh" circle @click="reload" />
    </section>

    <section class="focus-grid">
      <div class="glass-card panel fade-up fade-up-1">
        <div class="panel-head">
          <span>今日关注命中</span>
          <small>按关注池匹配今日信号</small>
        </div>
        <div class="panel-body">
          <MyFocusPanel :key="panelKey" @go-settings="scrollToSettings" />
        </div>
      </div>

      <div ref="settingsRef" class="focus-settings fade-up fade-up-2">
        <SettingsPanel />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import MyFocusPanel from '../../components/today/MyFocusPanel.vue'
import SettingsPanel from '../../components/today/SettingsPanel.vue'

const panelKey = ref(0)
const settingsRef = ref<HTMLElement | null>(null)

function reload() {
  panelKey.value += 1
}

async function scrollToSettings() {
  await nextTick()
  settingsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
.focus-page {
  display: grid;
  gap: 16px;
}

.focus-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 22px;
  background: var(--hero-bg);
}

.eyebrow {
  color: var(--brand-secondary);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.focus-hero h1 {
  margin: 8px 0;
  color: var(--text-primary);
  font-size: 30px;
}

.focus-hero p {
  max-width: 680px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.focus-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.72fr);
  gap: 16px;
  align-items: start;
}

.panel {
  overflow: hidden;
}

.panel-head {
  min-height: 46px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border);
  font-weight: 800;
}

.panel-head small {
  color: var(--text-faint);
  font-size: 12px;
}

.panel-body {
  padding: 18px;
}

.focus-settings :deep(.panel) {
  margin-bottom: 16px;
}

@media (max-width: 1080px) {
  .focus-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .focus-hero {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
