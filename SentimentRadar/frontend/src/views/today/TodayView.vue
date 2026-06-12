<template>
  <div v-if="isConsole" class="today-dashboard">
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
              <div class="panel-tabs" role="tablist" aria-label="今日信号视图">
                <button
                  v-for="tab in signalTabs"
                  :key="tab.value"
                  type="button"
                  :class="{ active: activeSignalTab === tab.value }"
                  :aria-selected="activeSignalTab === tab.value"
                  @click="activeSignalTab = tab.value"
                >
                  {{ tab.label }}
                </button>
              </div>
            </div>
            <div class="panel-body">
              <div class="section-row">
                <div>
                  <h2>{{ activeSignalMeta.title }}</h2>
                  <p class="muted">{{ activeSignalMeta.description }}</p>
                </div>
                <span class="blue-badge">{{ activeSignalMeta.badge }}</span>
              </div>
              <div v-if="activeSignalTab === 'cards'" class="prediction-grid">
                <PredictionCard
                  v-for="(card, index) in today.cards"
                  :key="card.id"
                  :card="card"
                  class="fade-up"
                  :class="`fade-up-${index + 1}`"
                  @view-evidence="openDrawer"
                />
              </div>

              <div v-else-if="activeSignalTab === 'heat'" class="heat-list">
                <button v-for="card in heatSortedCards" :key="card.id" type="button" class="heat-row" @click="openDrawer(card.id)">
                  <span class="heat-rank num">#{{ card.rank }}</span>
                  <span class="heat-main"><strong>{{ card.title }}</strong><small>{{ card.scenario }} · {{ card.evidence }}</small></span>
                  <span class="heat-score"><b class="num">{{ formatZ(card.heat_z) }}</b><small>热度 z</small></span>
                  <span class="heat-score"><b class="num">{{ formatZ(card.price_z) }}</b><small>价格 z</small></span>
                </button>
              </div>

              <div v-else-if="activeSignalTab === 'quadrant'" class="quadrant-workbench">
                <QuadrantChart :points="stockScatterPoints" />
                <div class="quadrant-stat-grid">
                  <div v-for="stat in quadrantStats" :key="stat.label" class="quadrant-stat">
                    <span>{{ stat.label }}</span><b class="num">{{ stat.value }}</b><small>{{ stat.text }}</small>
                  </div>
                </div>
              </div>

              <div v-else class="evidence-workbench">
                <div class="evidence-summary">
                  <div v-for="item in today.evidence_overview" :key="item.name" class="evidence-tile">
                    <span>{{ item.name }}</span><b class="num">{{ item.count.toLocaleString() }}</b>
                  </div>
                </div>
                <div class="evidence-card-list">
                  <button v-for="card in today.cards" :key="card.id" type="button" class="evidence-card-row" @click="openDrawer(card.id)">
                    <span class="heat-rank num">#{{ card.rank }}</span>
                    <span class="heat-main"><strong>{{ card.title }}</strong><small>{{ card.reason }}</small></span>
                    <span class="evidence-pill">{{ card.evidence }}</span>
                  </button>
                </div>
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
                  <p>生成 {{ today.cards.length }} 张预判卡，覆盖 {{ stockScatterPoints.length }} 只候选股。</p>
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
            <div class="panel-head"><span>个股候选象限图</span></div>
            <QuadrantChart :points="stockScatterPoints" />
            <p class="faint quadrant-hint">左上优先看「补涨观察」：主题热度高、个股 3 日涨幅仍低。</p>
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
        管线尚未产出今日信号。管理员可在「平台设置」中配置并立即运行。
      </p>
      <el-button type="primary" :loading="refreshing" @click="loadToday(true)">刷新</el-button>
    </el-empty>

    <EvidenceDrawer v-model="drawerVisible" :card-id="activeCardId" />
  </div>

  <div v-else class="today-home">
    <section class="home-hero glass-card fade-up">
      <div>
        <span class="eyebrow">今日首页</span>
        <h1>{{ greeting }}，先看 3 件事</h1>
        <p>{{ today?.headline || '聚合今日强信号、关注池命中与风险边界，少跳转、直接看结论。' }}</p>
      </div>
      <div class="hero-actions">
        <el-button :icon="Refresh" circle :loading="refreshing" @click="loadToday(true)" />
      </div>
    </section>

    <div v-if="todayLoading" v-loading="true" class="loading-block glass-card" />

    <template v-else-if="today && today.cards.length">
      <section class="quick-grid fade-up fade-up-1">
        <div class="quick-card glass-card"><span>今日强信号</span><b class="num">{{ today.cards.length }}</b><small>{{ stockScatterPoints.length }} 只候选股待观察</small></div>
        <div class="quick-card glass-card"><span>我的关注命中</span><b class="num">{{ today.my_related.items[0]?.value || today.my_related.highlight || '0' }}</b><small>{{ today.my_related.summary || '股票 · 主题 · 板块' }}</small></div>
        <div class="quick-card glass-card"><span>证据样本</span><b class="num">{{ evidenceTotal.toLocaleString() }}</b><small>新闻 / 公告 / 社媒 / 行情</small></div>
      </section>

      <section class="home-grid">
        <div class="left-home">
          <div class="glass-card panel">
            <div class="panel-head"><span>今日预判卡</span></div>
            <div class="panel-body card-grid"><PredictionCard v-for="card in topCards" :key="card.id" :card="card" @view-evidence="openDrawer" /></div>
          </div>
        </div>
        <aside class="right-home">
          <div class="glass-card panel">
            <div class="panel-head"><span>我的关注</span><button type="button" class="link-btn" @click="showSettings = !showSettings">管理</button></div>
            <div class="panel-body"><MyFocusPanel @go-settings="showSettings = true" /></div>
          </div>
          <div class="glass-card panel stock-quadrant-card">
            <div class="panel-head"><span>个股候选象限</span><small>主题热度 × 个股涨幅</small></div>
            <div class="panel-body">
              <QuadrantChart :points="stockScatterPoints" />
              <p class="quadrant-hint">左上优先看「补涨观察」：主题热度高、个股 3 日涨幅仍低。</p>
            </div>
          </div>
          <details class="glass-card panel settings-fold" :open="showSettings">
            <summary @click.prevent="showSettings = !showSettings">关注管理 / 推送提醒</summary>
            <div class="panel-body"><SettingsPanel /></div>
          </details>
        </aside>
      </section>
    </template>

    <el-empty v-else :description="today?.headline || '暂无预判数据'">
      <p class="muted empty-hint">管线尚未产出今日信号，管理员可在「平台设置」中配置并运行。</p>
      <el-button type="primary" :loading="refreshing" @click="loadToday(true)">刷新</el-button>
    </el-empty>
    <EvidenceDrawer v-model="drawerVisible" :card-id="activeCardId" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { fetchToday } from '../../api/radar'
import type { StockScatterPoint, TodayBriefing } from '../../api/types'
import { useAuthStore } from '../../stores/auth'
import PredictionCard from '../../components/today/PredictionCard.vue'
import EvidenceDrawer from '../../components/today/EvidenceDrawer.vue'
import MyFocusPanel from '../../components/today/MyFocusPanel.vue'
import SettingsPanel from '../../components/today/SettingsPanel.vue'
import QuadrantChart from '../../components/charts/QuadrantChart.vue'

const auth = useAuthStore()
const route = useRoute()
const today = ref<TodayBriefing | null>(null)
const todayLoading = ref(true)
const refreshing = ref(false)
const drawerVisible = ref(false)
const activeCardId = ref('')
const showSettings = ref(route.query.tab === 'my')
type SignalTab = 'cards' | 'heat' | 'quadrant' | 'evidence'
const activeSignalTab = ref<SignalTab>('cards')
const signalTabs: { label: string; value: SignalTab }[] = [
  { label: '预判卡', value: 'cards' },
  { label: '热度排序', value: 'heat' },
  { label: '个股象限', value: 'quadrant' },
  { label: '证据链', value: 'evidence' },
]
const isConsole = computed(() => route.name === 'console')

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

const topCards = computed(() => today.value?.cards.slice(0, 2) ?? [])

const heatSortedCards = computed(() => (
  [...(today.value?.cards ?? [])].sort((a, b) => (b.heat_z ?? -999) - (a.heat_z ?? -999))
))

const activeSignalMeta = computed(() => {
  const total = today.value?.cards.length ?? 0
  const meta: Record<SignalTab, { title: string; description: string; badge: string }> = {
    cards: { title: `舆情-价格背离 Top${total}`, description: today.value?.headline || '今日强信号预判卡', badge: '主视窗' },
    heat: { title: '热度排序', description: '按舆情热度 z 分倒序排列，点击行可展开证据链。', badge: '可点击' },
    quadrant: { title: '个股候选象限', description: '横轴个股 3 日涨幅、纵轴主题热度，优先关注热度高但涨幅低的补涨观察。', badge: '候选股' },
    evidence: { title: '证据链', description: '按信号聚合新闻、公告、社媒与行情证据，点击查看详情。', badge: '来源追踪' },
  }
  return meta[activeSignalTab.value]
})

const quadrantStats = computed(() => {
  const points = stockScatterPoints.value
  return [
    { label: '补涨观察', value: points.filter((p) => p.label === '补涨观察').length, text: '热度高涨幅低' },
    { label: '先动股', value: points.filter((p) => p.label === '先动股').length, text: '价格已启动' },
    { label: '风险股', value: points.filter((p) => p.label === '高位风险' || p.label === '弱势回避').length, text: '兑现或回避' },
  ]
})

const stockScatterPoints = computed<StockScatterPoint[]>(() => {
  const points: StockScatterPoint[] = []
  const seen = new Set<string>()
  for (const card of today.value?.cards ?? []) {
    for (const stock of card.stock_candidates ?? []) {
      if (seen.has(stock.code)) continue
      seen.add(stock.code)
      points.push({
        name: stock.name,
        code: stock.code,
        label: stock.label,
        topic: card.title,
        scenario: card.scenario,
        heat_z: card.heat_z ?? 0,
        return_3d: stock.return_3d,
        return_5d: stock.return_5d,
        volume_ratio: stock.volume_ratio,
      })
    }
  }
  return points
})

const metricCards = computed(() => {
  const data = today.value
  if (!data) return []
  return [
    {
      label: '今日信号',
      value: `${data.cards.length} / ${stockScatterPoints.value.length}`,
      sub: '预判卡 / 候选股',
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

function formatZ(value?: number | null) {
  if (value == null) return '-'
  return value > 0 ? `+${value}` : `${value}`
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

.panel-head small {
  color: var(--text-faint);
  font-size: 12px;
  font-weight: 700;
}

.panel-tabs {
  display: flex;
  gap: 6px;
  padding: 3px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-panel);
  overflow-x: auto;
  max-width: 100%;
}

.panel-tabs button {
  height: 28px;
  padding: 0 10px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
}

.panel-tabs button:hover,
.panel-tabs button.active {
  color: var(--text-primary);
  background: linear-gradient(135deg, rgba(59, 164, 247, 0.2), rgba(45, 212, 191, 0.14));
  box-shadow: inset 0 0 0 1px rgba(59, 164, 247, 0.38);
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


.heat-list,
.evidence-card-list { display: grid; gap: 10px; }
.heat-row,
.evidence-card-row { width: 100%; display: grid; grid-template-columns: 56px minmax(0, 1fr) 86px 86px; gap: 12px; align-items: center; min-height: 72px; padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--bg-panel); color: var(--text-secondary); cursor: pointer; text-align: left; }
.heat-row:hover,
.evidence-card-row:hover { border-color: rgba(59, 164, 247, 0.45); background: var(--bg-hover); }
.heat-rank { color: var(--brand); font-size: 20px; font-weight: 900; }
.heat-main { min-width: 0; }
.heat-main strong,
.heat-main small,
.heat-score small { display: block; }
.heat-main strong { overflow: hidden; color: var(--text-primary); font-size: 15px; text-overflow: ellipsis; white-space: nowrap; }
.heat-main small,
.heat-score small { margin-top: 4px; color: var(--text-faint); font-size: 12px; }
.heat-score { padding: 8px 10px; border-radius: 10px; background: rgba(59, 164, 247, 0.08); text-align: right; }
.heat-score b { color: var(--text-primary); font-size: 18px; }
.quadrant-workbench { display: grid; gap: 14px; }
.quadrant-workbench :deep(.quadrant-chart) { height: 360px; }
.quadrant-stat-grid,
.evidence-summary { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.quadrant-stat,
.evidence-tile { padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--bg-panel); }
.quadrant-stat span,
.evidence-tile span,
.quadrant-stat small { display: block; color: var(--text-muted); font-size: 12px; }
.quadrant-stat b,
.evidence-tile b { display: block; margin: 5px 0 2px; color: var(--text-primary); font-size: 24px; }
.evidence-workbench { display: grid; gap: 14px; }
.evidence-card-row { grid-template-columns: 56px minmax(0, 1fr) auto; }
.evidence-pill { justify-self: end; padding: 5px 9px; border: 1px solid rgba(45, 212, 191, 0.24); border-radius: 999px; color: var(--brand-secondary); background: rgba(45, 212, 191, 0.1); font-size: 12px; white-space: nowrap; }

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

.stock-quadrant-card :deep(.quadrant-chart) {
  height: 280px;
}

.stock-quadrant-card .quadrant-hint {
  margin: 10px 0 0;
  color: var(--text-faint);
  line-height: 1.6;
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
  .prediction-grid,
  .quadrant-stat-grid,
  .evidence-summary {
    grid-template-columns: 1fr;
  }

  .panel-head { align-items: flex-start; flex-direction: column; padding: 12px 16px; }

  .heat-row,
  .evidence-card-row { grid-template-columns: 44px minmax(0, 1fr); }

  .heat-score,
  .evidence-pill { grid-column: 2; justify-self: start; text-align: left; }
}

/* 首页精简视图 */
.today-home { display: grid; gap: 16px; }
.home-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; padding: 22px; overflow: hidden; background: radial-gradient(circle at 84% 16%, rgba(59, 164, 247, 0.18), transparent 34%), linear-gradient(135deg, rgba(21, 30, 45, 0.96), rgba(16, 24, 38, 0.9)); }
.eyebrow { color: var(--brand-secondary); font-size: 12px; font-weight: 900; letter-spacing: 0.08em; }
.home-hero h1 { margin: 8px 0 8px; font-size: 28px; }
.home-hero p { max-width: 720px; margin: 0; color: var(--text-muted); line-height: 1.7; }
.quick-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.quick-card { min-height: 116px; padding: 18px; background: var(--bg-elevated); }
.quick-card span, .quick-card small { display: block; color: var(--text-muted); font-size: 13px; }
.quick-card b { display: block; margin: 8px 0 4px; color: var(--text-primary); font-size: 32px; }
.home-grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr); gap: 16px; align-items: start; }
.left-home, .right-home { display: grid; gap: 16px; }
.card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.link-btn { border: 0; background: transparent; color: var(--brand); cursor: pointer; font: inherit; font-size: 13px; font-weight: 800; }
.right-home :deep(.head-line) { display: none; }
@media (max-width: 1080px) { .home-grid, .quick-grid, .card-grid { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .home-hero { align-items: flex-start; flex-direction: column; } .hero-actions { width: 100%; justify-content: space-between; } }

</style>
