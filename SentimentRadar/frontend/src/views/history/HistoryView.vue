<template>
  <div class="history-page">
    <section class="history-hero glass-card fade-up">
      <div>
        <span class="eyebrow">REPLAY DESK</span>
        <h1>历史复盘</h1>
        <p>这里不是再看一遍旧信号，而是验证「什么场景更可靠、什么信号要降权」。先看胜率，再用筛选器定位案例，最后把结论反哺到关注池和今日信号。</p>
      </div>
      <div class="hero-insight">
        <small>当前复盘口径</small>
        <strong>{{ replaySummary }}</strong>
        <span>{{ replayHint }}</span>
      </div>
    </section>

    <div v-if="loading" v-loading="true" class="loading-block glass-card" />

    <template v-else-if="history">
      <section class="usage-grid fade-up fade-up-1">
        <div v-for="step in usageSteps" :key="step.title" class="usage-card glass-card">
          <b>{{ step.index }}</b>
          <div>
            <strong>{{ step.title }}</strong>
            <p>{{ step.text }}</p>
          </div>
        </div>
      </section>

      <section class="stats-row fade-up fade-up-1">
        <StatChip label="累计信号" :value="history.stats.total ?? 0" />
        <StatChip label="已验证" :value="history.stats.evaluated ?? 0" sub="信号发出 3 个交易日后回填" />
        <StatChip
          label="3 日胜率"
          :value="history.stats.win_rate_3d != null ? `${history.stats.win_rate_3d}%` : '待积累'"
          :tone="history.stats.win_rate_3d != null && history.stats.win_rate_3d >= 50 ? 'up' : ''"
        />
        <StatChip
          label="平均 3 日收益"
          :value="history.stats.avg_return_3d != null ? `${history.stats.avg_return_3d}%` : '待积累'"
          :tone="returnTone(history.stats.avg_return_3d)"
        />
      </section>

      <section v-if="scenarioEntries.length" class="glass-card scenario-stats fade-up fade-up-2">
        <div class="section-row">
          <div>
            <h3 class="section-title">分场景表现</h3>
            <p class="muted">优先关注高胜率且样本数持续增加的场景，低胜率场景用来修正今日信号权重。</p>
          </div>
          <span class="faint">{{ scenarioEntries.length }} 类场景</span>
        </div>
        <div class="scenario-grid">
          <button
            v-for="[name, stat] in scenarioEntries"
            :key="name"
            type="button"
            class="scenario-item"
            :class="[scenarioClass(name), { active: scenarioFilter === name }]"
            @click="scenarioFilter = scenarioFilter === name ? '全部' : name"
          >
            <span class="scenario-name">{{ name }}</span>
            <b class="num">{{ stat.win_rate != null ? `${stat.win_rate}%` : '待验证' }}</b>
            <small>{{ stat.evaluated }} / {{ stat.count }} 已验证</small>
          </button>
        </div>
      </section>

      <section class="glass-card review-toolbar fade-up fade-up-2">
        <div class="toolbar-head">
          <div>
            <h3 class="section-title">复盘筛选</h3>
            <p class="muted">建议按「场景 + 3日结果」筛出一组案例，再逐条看证据链与收益回填。</p>
          </div>
          <el-button text @click="resetFilters">重置</el-button>
        </div>
        <div class="filters">
          <el-input v-model="searchKeyword" clearable placeholder="搜索标题 / 板块 / 判断" class="search-input" />
          <el-select v-model="scenarioFilter" class="filter-select" placeholder="场景">
            <el-option v-for="option in scenarioOptions" :key="option" :label="option" :value="option" />
          </el-select>
          <el-select v-model="statusFilter" class="filter-select" placeholder="验证状态">
            <el-option v-for="option in statusOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
          <el-select v-model="sortKey" class="sort-select" placeholder="排序">
            <el-option v-for="option in sortOptions" :key="option.value" :label="option.label" :value="option.value" />
          </el-select>
        </div>
        <div class="filter-summary">
          <span>筛选后 <b class="num">{{ filteredCards.length }}</b> 条</span>
          <span>已验证 <b class="num">{{ filteredStats.evaluated }}</b> 条</span>
          <span>3日胜率 <b class="num">{{ filteredStats.winRateText }}</b></span>
          <span>平均3日 <b class="num" :class="returnTone(filteredStats.avgReturn)">{{ filteredStats.avgReturnText }}</b></span>
        </div>
      </section>

      <section class="glass-card replay-note fade-up fade-up-3">
        <strong>怎么读：</strong>
        <span>{{ activeReplayNote }}</span>
      </section>

      <template v-if="filteredDays.length">
        <div v-for="(day, index) in filteredDays" :key="day.date" class="day-group fade-up" :class="`fade-up-${Math.min(index + 3, 4)}`">
          <div class="day-label">
            <span class="num">{{ day.date }}</span>
            <span class="day-line" />
            <small>{{ day.cards.length }} 条</small>
          </div>
          <div class="day-cards">
            <article v-for="card in day.cards" :key="card.id" class="glass-card hoverable history-card" :class="scenarioClass(card.scenario)">
              <div class="history-head">
                <div>
                  <span class="scenario-badge">{{ card.scenario }}</span>
                  <h4>{{ card.title }}</h4>
                  <span class="faint boards">{{ boardNames(card) }}</span>
                </div>
                <div class="result-pill" :class="returnTone(card.return_3d)">
                  <small>3日结果</small>
                  <b class="num">{{ card.return_3d != null ? formatReturn(card.return_3d) : '待验证' }}</b>
                </div>
              </div>
              <p class="muted judgement">{{ card.judgement }}</p>
              <div class="returns">
                <span v-for="period in RETURN_PERIODS" :key="period.key" class="return-item">
                  <span class="faint">{{ period.label }}</span>
                  <b v-if="card[period.key] != null" class="num" :class="returnTone(card[period.key])">
                    {{ formatReturn(card[period.key]) }}
                  </b>
                  <span v-else class="faint">待验证</span>
                </span>
                <span class="return-item signal-z">
                  <span class="faint">信号强度</span>
                  <span class="num muted">热度 z {{ formatZ(card.heat_z) }} / 价格 z {{ formatZ(card.price_z) }}</span>
                </span>
              </div>
              <div class="card-conclusion">
                <span>复盘结论</span>
                <p>{{ replayConclusion(card) }}</p>
              </div>
            </article>
          </div>
        </div>
      </template>

      <el-empty v-else-if="history.days.length" description="当前筛选条件下没有历史信号">
        <el-button type="primary" @click="resetFilters">清空筛选</el-button>
      </el-empty>
      <el-empty v-else description="暂无历史信号，管线运行后将逐日积累" />
      <p v-if="history.days.length" class="faint disclaimer">{{ history.disclaimer }} · 收益为信号板块的事后统计，不代表任何收益承诺</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchHistory } from '../../api/radar'
import type { HistoryCard, HistoryResult } from '../../api/types'
import StatChip from '../../components/common/StatChip.vue'

type StatusFilter = 'all' | 'verified' | 'pending' | 'win3' | 'loss3'
type SortKey = 'date_desc' | 'return_3d_desc' | 'return_3d_asc' | 'heat_desc'
type HistoryEntry = HistoryCard & { date: string }

const history = ref<HistoryResult | null>(null)
const loading = ref(true)
const searchKeyword = ref('')
const scenarioFilter = ref('全部')
const statusFilter = ref<StatusFilter>('all')
const sortKey = ref<SortKey>('date_desc')

const RETURN_PERIODS: { key: 'return_1d' | 'return_3d' | 'return_5d'; label: string }[] = [
  { key: 'return_1d', label: '1 日' },
  { key: 'return_3d', label: '3 日' },
  { key: 'return_5d', label: '5 日' },
]

const usageSteps = [
  { index: '01', title: '先看胜率', text: '判断当前模型在 3 日窗口是否稳定，不用单条涨跌下结论。' },
  { index: '02', title: '再筛场景', text: '按先闻后动、同步共振、先动后闻筛案例，找到应该加权或降权的模式。' },
  { index: '03', title: '沉淀规则', text: '把正样本加入关注池，把负样本的噪声特征写回今日信号判断。' },
]

const statusOptions: { label: string; value: StatusFilter }[] = [
  { label: '全部状态', value: 'all' },
  { label: '已验证', value: 'verified' },
  { label: '待验证', value: 'pending' },
  { label: '3日上涨', value: 'win3' },
  { label: '3日下跌', value: 'loss3' },
]

const sortOptions: { label: string; value: SortKey }[] = [
  { label: '按时间最新', value: 'date_desc' },
  { label: '3日收益最高', value: 'return_3d_desc' },
  { label: '3日收益最低', value: 'return_3d_asc' },
  { label: '热度 z 最高', value: 'heat_desc' },
]

const scenarioEntries = computed(() => Object.entries(history.value?.stats.by_scenario ?? {}))

const allCards = computed<HistoryEntry[]>(() => {
  const cards: HistoryEntry[] = []
  for (const day of history.value?.days ?? []) {
    for (const card of day.cards) cards.push({ ...card, date: day.date })
  }
  return cards
})

const scenarioOptions = computed(() => {
  const options = new Set(['全部'])
  for (const [name] of scenarioEntries.value) options.add(name)
  for (const card of allCards.value) options.add(card.scenario)
  return [...options]
})

const filteredCards = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return allCards.value
    .filter((card) => {
      const text = [card.title, card.scenario, card.judgement, boardNames(card)].join(' ').toLowerCase()
      const matchesKeyword = !keyword || text.includes(keyword)
      const matchesScenario = scenarioFilter.value === '全部' || card.scenario === scenarioFilter.value
      const matchesStatus = statusMatches(card)
      return matchesKeyword && matchesScenario && matchesStatus
    })
    .sort(sortCards)
})

const filteredDays = computed(() => {
  const groups = new Map<string, HistoryEntry[]>()
  for (const card of filteredCards.value) {
    const group = groups.get(card.date) ?? []
    group.push(card)
    groups.set(card.date, group)
  }
  return [...groups.entries()].map(([date, cards]) => ({ date, cards }))
})

const filteredStats = computed(() => {
  const returns = filteredCards.value
    .map((card) => card.return_3d)
    .filter((value): value is number => value != null)
  const wins = returns.filter((value) => value > 0).length
  const avgReturn = returns.length ? round(returns.reduce((sum, value) => sum + value, 0) / returns.length) : null
  const winRate = returns.length ? round((wins / returns.length) * 100) : null
  return {
    evaluated: returns.length,
    avgReturn,
    winRateText: winRate != null ? `${winRate}%` : '待积累',
    avgReturnText: avgReturn != null ? formatReturn(avgReturn) : '待积累',
  }
})

const replaySummary = computed(() => {
  const total = history.value?.stats.total ?? 0
  const evaluated = history.value?.stats.evaluated ?? 0
  if (!total) return '等待管线积累历史样本'
  return `${evaluated}/${total} 条信号已完成验证`
})

const replayHint = computed(() => {
  const winRate = history.value?.stats.win_rate_3d
  if (winRate == null) return '先积累 3 日回填，再比较场景胜率。'
  if (winRate >= 55) return '整体有效性偏正，重点复用高胜率场景。'
  if (winRate >= 45) return '整体接近中性，建议按场景拆分复盘。'
  return '整体胜率偏弱，优先排查噪声与追高信号。'
})

const activeReplayNote = computed(() => {
  if (!filteredCards.value.length) return '换一个筛选条件，或等待更多历史样本。'
  if (statusFilter.value === 'loss3') return '正在看负样本：重点找共同噪声，例如价格先涨、热度回落、证据重复。'
  if (statusFilter.value === 'win3') return '正在看正样本：重点找可复制触发条件，适合加入关注池和推送模板。'
  if (scenarioFilter.value !== '全部') return `正在看「${scenarioFilter.value}」：对比该场景的胜率、收益和判断文案是否一致。`
  return '默认按最新信号排列：先看统计，再挑 3 日结果明显的案例做深复盘。'
})

function scenarioClass(scenario: string) {
  if (scenario === '先闻后动') return 'scenario-news-first'
  if (scenario === '同步共振') return 'scenario-resonance'
  return 'scenario-move-first'
}

function statusMatches(card: HistoryCard) {
  if (statusFilter.value === 'verified') return card.return_3d != null
  if (statusFilter.value === 'pending') return card.return_3d == null
  if (statusFilter.value === 'win3') return card.return_3d != null && card.return_3d > 0
  if (statusFilter.value === 'loss3') return card.return_3d != null && card.return_3d < 0
  return true
}

function sortCards(a: HistoryEntry, b: HistoryEntry) {
  if (sortKey.value === 'return_3d_desc') return compareNullableDesc(a.return_3d, b.return_3d)
  if (sortKey.value === 'return_3d_asc') return compareNullableAsc(a.return_3d, b.return_3d)
  if (sortKey.value === 'heat_desc') return compareNullableDesc(a.heat_z, b.heat_z)
  return b.date.localeCompare(a.date)
}

function compareNullableAsc(a: number | null, b: number | null) {
  if (a == null && b == null) return 0
  if (a == null) return 1
  if (b == null) return -1
  return a - b
}

function compareNullableDesc(a: number | null, b: number | null) {
  if (a == null && b == null) return 0
  if (a == null) return 1
  if (b == null) return -1
  return b - a
}

function returnTone(value: number | null | undefined): 'up' | 'down' | '' {
  if (value == null) return ''
  return value > 0 ? 'up' : value < 0 ? 'down' : ''
}

function formatReturn(value: number | null | undefined): string {
  if (value == null) return '待验证'
  return `${value > 0 ? '+' : ''}${value}%`
}

function formatZ(value: number | null) {
  return value == null ? '-' : value
}

function boardNames(card: HistoryCard) {
  return card.boards.map((board) => board.name).join('、') || '未标注板块'
}

function replayConclusion(card: HistoryCard) {
  if (card.return_3d == null) return '未到验证窗口：先保留观察，不纳入胜率判断。'
  if (card.return_3d > 0) return '验证偏正：回看当时证据是否可复制，适合沉淀为后续加权规则。'
  if (card.return_3d < 0) return '验证偏负：检查是否追高、证据噪声过大或价格先动后热度补发。'
  return '表现持平：单靠方向信号不够，需要结合成交量与风险边界再判断。'
}

function round(value: number) {
  return Math.round(value * 100) / 100
}

function resetFilters() {
  searchKeyword.value = ''
  scenarioFilter.value = '全部'
  statusFilter.value = 'all'
  sortKey.value = 'date_desc'
}

onMounted(async () => {
  try {
    history.value = await fetchHistory()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.history-page {
  display: grid;
  gap: 16px;
}

.history-hero {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  background: var(--hero-bg);
}

.eyebrow {
  color: var(--brand-secondary);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.history-hero h1 {
  margin: 8px 0;
  font-size: 30px;
}

.history-hero p {
  max-width: 780px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.75;
}

.hero-insight {
  min-width: 250px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  background: rgba(10, 15, 26, 0.42);
}

.hero-insight small,
.hero-insight span {
  color: var(--text-muted);
  line-height: 1.6;
}

.hero-insight strong {
  font-size: 20px;
}

.loading-block {
  min-height: 320px;
}

.usage-grid,
.stats-row,
.scenario-grid,
.filters,
.filter-summary,
.returns {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.usage-card {
  flex: 1 1 220px;
  display: flex;
  gap: 14px;
  padding: 16px;
}

.usage-card b {
  color: var(--brand-secondary);
  font-size: 18px;
}

.usage-card strong {
  display: block;
  margin-bottom: 6px;
}

.usage-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
  font-size: 13px;
}

.scenario-stats,
.review-toolbar,
.replay-note {
  padding: 18px 20px;
}

.section-row,
.toolbar-head,
.history-head,
.day-label,
.return-item {
  display: flex;
  align-items: center;
}

.section-row,
.toolbar-head,
.history-head {
  justify-content: space-between;
  gap: 14px;
}

.section-row p,
.toolbar-head p {
  margin: -8px 0 0;
}

.scenario-item {
  display: grid;
  gap: 6px;
  min-width: 170px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--scenario-color) 28%, var(--glass-border));
  border-radius: 12px;
  color: var(--text-primary);
  background: color-mix(in srgb, var(--scenario-color) 8%, transparent);
  text-align: left;
  cursor: pointer;
}

.scenario-item.active {
  box-shadow: inset 0 0 0 1px var(--scenario-color), 0 14px 30px rgba(0, 0, 0, 0.22);
}

.scenario-item b,
.scenario-name {
  color: var(--scenario-color);
}

.scenario-item small {
  color: var(--text-muted);
}

.review-toolbar {
  display: grid;
  gap: 14px;
}

.search-input {
  flex: 1 1 280px;
}

.filter-select {
  width: 150px;
}

.sort-select {
  width: 170px;
}

.filter-summary {
  color: var(--text-muted);
  font-size: 13px;
}

.filter-summary span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(10, 15, 26, 0.36);
}

.replay-note {
  display: flex;
  gap: 8px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.replay-note strong {
  color: var(--brand-secondary);
  white-space: nowrap;
}

.day-group {
  margin-top: 4px;
}

.day-label {
  gap: 14px;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.day-label small {
  color: var(--text-muted);
}

.day-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--glass-border), transparent);
}

.day-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  padding: 16px 20px;
  border-left: 3px solid var(--scenario-color);
  background:
    radial-gradient(circle at 96% 8%, color-mix(in srgb, var(--scenario-color) 10%, transparent), transparent 32%),
    var(--glass-bg);
}

.history-head > div:first-child {
  min-width: 0;
}

.history-head h4 {
  margin: 8px 0 4px;
  font-size: 16px;
}

.boards {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scenario-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--scenario-color);
  background: color-mix(in srgb, var(--scenario-color) 14%, transparent);
  padding: 2px 10px;
  border-radius: 999px;
}

.result-pill {
  min-width: 108px;
  display: grid;
  gap: 2px;
  justify-items: end;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(10, 15, 26, 0.42);
}

.result-pill small {
  color: var(--text-muted);
}

.result-pill b {
  color: var(--text-primary);
}

.result-pill.up b {
  color: var(--up);
}

.result-pill.down b {
  color: var(--down);
}

.judgement {
  margin: 10px 0 12px;
  line-height: 1.65;
}

.returns {
  font-size: 13px;
}

.return-item {
  gap: 6px;
}

.signal-z {
  margin-left: auto;
}

.card-conclusion {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--glass-border);
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.65;
}

.card-conclusion span {
  color: var(--brand-secondary);
  white-space: nowrap;
}

.card-conclusion p {
  margin: 0;
}

.disclaimer {
  text-align: center;
  font-size: 12px;
  margin-top: 2px;
}

@media (max-width: 760px) {
  .history-hero,
  .section-row,
  .toolbar-head,
  .history-head,
  .replay-note,
  .card-conclusion {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-insight,
  .filter-select,
  .sort-select,
  .search-input {
    width: 100%;
  }

  .result-pill {
    width: 100%;
    justify-items: start;
  }

  .signal-z {
    margin-left: 0;
  }
}
</style>
