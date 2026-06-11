<template>
  <div class="today-dashboard">
    <section class="hero-row fade-up">
      <div>
        <h1>🪼 {{ greeting }}，{{ auth.user?.name || 'nanashiwang' }}</h1>
        <p>今天优先看左侧信号流：先判断舆情-行情背离，再跟进你的关注池。</p>
      </div>
      <div class="hero-actions">
        <div class="search-box">⌕ 搜索股票 / 主题 / 板块</div>
        <el-button :icon="Refresh" circle :loading="refreshing" @click="loadToday(true)" />
      </div>
    </section>

    <div v-if="todayLoading" v-loading="true" class="loading-block glass-card" />

    <template v-else-if="today && today.cards.length">
      <section class="metric-grid fade-up fade-up-1">
        <div v-for="metric in metricCards" :key="metric.label" class="metric-card glass-card">
          <div>
            <span class="metric-label">{{ metric.label }}</span>
            <strong class="num">{{ metric.value }}</strong>
            <small>{{ metric.sub }}</small>
          </div>
          <div class="metric-icon" :class="metric.tone">{{ metric.icon }}</div>
        </div>
      </section>

      <section class="content-grid">
        <div class="left-stack">
          <div class="glass-card panel signal-panel fade-up fade-up-2">
            <div class="panel-head">
              <span>今日信号</span>
              <div class="panel-tabs">
                <b>预判卡</b>
                <span>/ 热度排序</span>
                <span>/ 背离象限</span>
                <span>/ 证据链</span>
              </div>
            </div>
            <div class="panel-body">
              <div class="section-row">
                <div>
                  <h2>舆情-价格背离 Top{{ today.cards.length }}</h2>
                  <p class="muted">{{ today.headline }}</p>
                </div>
                <span class="blue-badge">优先放在左侧主视窗</span>
              </div>
              <div class="prediction-grid">
                <PredictionCard
                  v-for="(card, index) in today.cards"
                  :key="card.id"
                  :card="card"
                  class="fade-up"
                  :class="`fade-up-${index + 1}`"
                  @view-evidence="openDrawer"
                />
              </div>
            </div>
          </div>

          <div class="glass-card panel focus-panel fade-up fade-up-3">
            <div class="panel-head">
              <span>我的关注</span>
              <span class="blue-badge">左侧第二优先级</span>
            </div>
            <div class="panel-body">
              <MyFocusPanel @go-settings="showSettings = true" />
            </div>
          </div>

          <details class="glass-card panel settings-fold fade-up fade-up-4" :open="showSettings">
            <summary @click.prevent="showSettings = !showSettings">关注管理 / 推送提醒</summary>
            <div class="panel-body">
              <SettingsPanel />
            </div>
          </details>
        </div>

        <aside class="right-stack">
          <div class="glass-card side-panel fade-up fade-up-2">
            <div class="panel-head"><span>管线运行</span></div>
            <div class="timeline">
              <div class="timeline-item success">
                <i />
                <div>
                  <strong>今日 {{ updatedTime }} 成功</strong>
                  <p>生成 {{ today.cards.length }} 张预判卡，覆盖 {{ today.signals_scatter.length }} 个信号点。</p>
                </div>
              </div>
              <div class="timeline-item warn">
                <i />
                <div>
                  <strong>下一次 09:35</strong>
                  <p>开盘后刷新热榜与板块价格背离。</p>
                </div>
              </div>
              <div class="timeline-item success">
                <i />
                <div>
                  <strong>tushare 权限</strong>
                  <p>ths_index / ths_daily 需要确认积分权限。</p>
                </div>
              </div>
            </div>
          </div>

          <div class="glass-card side-panel fade-up fade-up-3">
            <div class="panel-head"><span>系统接入</span></div>
            <div class="status-list">
              <div class="status-row">
                <i class="status-icon ai">AI</i>
                <div><strong>Radar LLM</strong><span>OPENAI_BASE_URL 已配置</span></div>
                <b>测试</b>
              </div>
              <div class="status-row">
                <i class="status-icon ts">TS</i>
                <div><strong>Tushare</strong><span>行情主源，Akshare 兜底</span></div>
                <b>权限</b>
              </div>
              <div class="status-row">
                <i class="status-icon db">DB</i>
                <div><strong>PostgreSQL</strong><span>Radar 用户 / 管线结果库</span></div>
                <b>正常</b>
              </div>
            </div>
          </div>

          <div class="glass-card side-panel fade-up fade-up-3">
            <div class="panel-head"><span>配置完成度</span></div>
            <div class="completion-list">
              <div class="completion-row">
                <div><strong>生产可用度</strong><b>72%</b></div>
                <span>LLM、行情、数据库、调度、告警</span>
                <i><em style="width: 72%" /></i>
              </div>
              <div class="completion-row">
                <div><strong>运营后台</strong><b>84%</b></div>
                <span>用户、订阅、审计、系统配置</span>
                <i><em style="width: 84%" /></i>
              </div>
            </div>
          </div>

          <div class="glass-card side-panel fade-up fade-up-3">
            <div class="panel-head"><span>{{ today.top_risk.title }}</span></div>
            <div class="risk-box">
              <div class="risk-level">{{ today.top_risk.level }}</div>
              <div class="kv"><span>范围</span><b>{{ today.top_risk.scope }}</b></div>
              <p>{{ today.top_risk.reason }}</p>
            </div>
          </div>

          <div class="glass-card side-panel fade-up fade-up-4">
            <div class="panel-head"><span>今日证据来源</span></div>
            <div class="evidence-list">
              <div v-for="item in today.evidence_overview" :key="item.name" class="evidence-row">
                <span>{{ item.name }}</span>
                <b class="num">{{ item.count.toLocaleString() }}</b>
              </div>
            </div>
          </div>

          <div class="glass-card side-panel chart-panel fade-up fade-up-4">
            <div class="panel-head"><span>信号象限图</span></div>
            <QuadrantChart :points="today.signals_scatter" />
            <p class="faint quadrant-hint">左上为「先闻后动」机会区：舆情升温而板块未动。</p>
          </div>

          <div class="glass-card side-panel plan-note fade-up fade-up-4">
            <div class="panel-head"><span>规划说明</span></div>
            <p>
              左侧承载用户每天必看的内容：今日信号、我的关注、历史复盘；右侧承载风险、
              证据、管线和系统态。这样可以减少入口，让 Radar 像一个完整产品。
            </p>
          </div>
        </aside>
      </section>
    </template>

    <el-empty v-else :description="today?.headline || '暂无预判数据'">
      <p class="muted empty-hint">
        管线尚未产出今日信号。管理员可在「管理后台 → 平台设置 → 雷达管线」中配置并立即运行。
      </p>
      <el-button type="primary" :loading="refreshing" @click="loadToday(true)">刷新</el-button>
    </el-empty>

    <EvidenceDrawer v-model="drawerVisible" :card-id="activeCardId" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { fetchToday } from '../../api/radar'
import type { TodayBriefing } from '../../api/types'
import { useAuthStore } from '../../stores/auth'
import PredictionCard from '../../components/today/PredictionCard.vue'
import EvidenceDrawer from '../../components/today/EvidenceDrawer.vue'
import MyFocusPanel from '../../components/today/MyFocusPanel.vue'
import SettingsPanel from '../../components/today/SettingsPanel.vue'
import QuadrantChart from '../../components/charts/QuadrantChart.vue'

const auth = useAuthStore()
const today = ref<TodayBriefing | null>(null)
const todayLoading = ref(true)
const refreshing = ref(false)
const drawerVisible = ref(false)
const activeCardId = ref('')
const showSettings = ref(false)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 11) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const updatedTime = computed(() => {
  const value = today.value?.updated_at || ''
  return value.split(' ').pop()?.slice(0, 5) || '--:--'
})

const evidenceTotal = computed(() => (
  today.value?.evidence_overview.reduce((sum, item) => sum + item.count, 0) ?? 0
))

const metricCards = computed(() => {
  const data = today.value
  if (!data) return []
  return [
    {
      label: '今日信号',
      value: `${data.cards.length} / ${Math.max(data.signals_scatter.length, data.cards.length)}`,
      sub: '强信号 / 总信号',
      icon: '⌁',
      tone: 'blue',
    },
    {
      label: '我的关注命中',
      value: data.my_related.items[0]?.value || data.my_related.highlight || '0',
      sub: data.my_related.summary || '股票 · 主题 · 板块',
      icon: '◎',
      tone: 'cyan',
    },
    {
      label: '舆情热度',
      value: evidenceTotal.value.toLocaleString(),
      sub: '全网热榜样本',
      icon: '♨',
      tone: 'red',
    },
    {
      label: '管线状态',
      value: updatedTime.value,
      sub: '最近运行',
      icon: '↯',
      tone: 'blue',
    },
  ]
})

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
.today-dashboard {
  display: grid;
  gap: 16px;
}

.loading-block {
  height: 360px;
}

.hero-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
}

.hero-row h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: 0.2px;
}

.hero-row p {
  margin: 8px 0 0;
  color: var(--text-muted);
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-box {
  width: 270px;
  height: 38px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-panel);
  color: var(--text-faint);
  font-size: 14px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  min-height: 118px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  background:
    radial-gradient(circle at 88% 50%, rgba(59, 164, 247, 0.14), transparent 34%),
    var(--bg-elevated);
}

.metric-label,
.metric-card small {
  display: block;
  color: var(--text-muted);
  font-size: 13px;
}

.metric-card strong {
  display: block;
  margin: 8px 0 2px;
  font-size: 30px;
  font-weight: 900;
  color: var(--text-primary);
}

.metric-icon {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  font-size: 30px;
  color: var(--brand);
  background: rgba(59, 164, 247, 0.1);
}

.metric-icon.cyan {
  color: var(--brand-secondary);
  background: rgba(45, 212, 191, 0.1);
}

.metric-icon.red {
  color: var(--up);
  background: rgba(240, 82, 82, 0.1);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 2.15fr) minmax(310px, 0.78fr);
  gap: 16px;
  align-items: start;
}

.left-stack,
.right-stack {
  display: grid;
  gap: 16px;
}

.panel {
  overflow: hidden;
}

.panel-head {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  font-weight: 800;
}

.panel-tabs {
  display: flex;
  gap: 12px;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 650;
}

.panel-tabs b {
  color: var(--text-primary);
}

.panel-body {
  padding: 18px;
}

.section-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.section-row h2 {
  margin: 0 0 6px;
  font-size: 20px;
}

.section-row p {
  margin: 0;
}

.blue-badge {
  align-self: flex-start;
  border-radius: 999px;
  padding: 5px 10px;
  color: var(--brand-secondary);
  background: rgba(45, 212, 191, 0.11);
  border: 1px solid rgba(45, 212, 191, 0.24);
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.prediction-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.focus-panel :deep(.head-line) {
  display: none;
}

.focus-panel :deep(.el-empty) {
  --el-empty-padding: 34px 0;
}

.focus-panel :deep(.el-empty__image) {
  width: 110px;
}

.settings-fold summary {
  cursor: pointer;
  min-height: 42px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  font-weight: 800;
}

.side-panel {
  overflow: hidden;
}

.timeline,
.evidence-list,
.risk-box,
.plan-note p,
.status-list,
.completion-list {
  padding: 16px;
}

.timeline {
  display: grid;
  gap: 14px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 14px 1fr;
  gap: 11px;
}

.timeline-item i {
  width: 9px;
  height: 9px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--down);
  box-shadow: 0 0 0 5px rgba(49, 196, 141, 0.12);
}

.timeline-item.warn i {
  background: var(--warning);
  box-shadow: 0 0 0 5px rgba(251, 191, 36, 0.12);
}

.timeline-item strong {
  font-size: 14px;
}

.timeline-item p,
.risk-box p,
.plan-note p {
  margin: 4px 0 0;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.65;
}

.risk-box {
  border-left: 3px solid var(--warning);
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.08), transparent 68%);
}

.risk-level {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 4px 9px;
  border-radius: 999px;
  color: var(--warning);
  border: 1px solid rgba(251, 191, 36, 0.26);
  background: rgba(251, 191, 36, 0.1);
  font-weight: 800;
  font-size: 12px;
}

.kv,
.evidence-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-muted);
  font-size: 13px;
}

.kv b,
.evidence-row b {
  color: var(--text-primary);
}

.evidence-list {
  display: grid;
  gap: 12px;
}

.evidence-row {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.evidence-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.status-list {
  display: grid;
  gap: 12px;
}

.status-row {
  display: grid;
  grid-template-columns: 38px 1fr auto;
  gap: 10px;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.status-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.status-row strong,
.status-row span {
  display: block;
}

.status-row strong {
  font-size: 14px;
}

.status-row span {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 12px;
}

.status-row > b {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: 12px;
}

.status-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  color: var(--text-primary);
  font-style: normal;
  font-weight: 900;
}

.status-icon.ai { background: var(--brand); }
.status-icon.ts { background: var(--down); }
.status-icon.db { background: var(--warning); color: #111827; }

.completion-list {
  display: grid;
  gap: 16px;
}

.completion-row div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.completion-row span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.completion-row i {
  display: block;
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--bg-panel);
}

.completion-row em {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--brand), var(--brand-secondary));
}

.chart-panel :deep(.quadrant-chart) {
  height: 260px;
}

.quadrant-hint {
  margin: -6px 16px 16px;
  font-size: 12px;
}

.plan-note {
  border-color: rgba(251, 191, 36, 0.35);
  background:
    linear-gradient(180deg, rgba(251, 191, 36, 0.08), transparent 52%),
    var(--bg-elevated);
}

.empty-hint {
  margin: 0 0 16px;
}

@media (max-width: 1180px) {
  .metric-grid,
  .prediction-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .hero-row,
  .section-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-actions,
  .search-box {
    width: 100%;
  }

  .metric-grid,
  .prediction-grid {
    grid-template-columns: 1fr;
  }
}
</style>
