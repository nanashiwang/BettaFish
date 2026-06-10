<template>
  <div class="home-page">
    <!-- 顶栏 -->
    <header class="home-topbar">
      <div class="brand">
        <div class="logo">雷</div>
        <span class="brand-name">A 股舆情雷达</span>
      </div>
      <div class="topbar-actions">
        <el-button text @click="router.push('/login')">登录</el-button>
        <el-button type="primary" @click="router.push('/register')">免费注册</el-button>
      </div>
    </header>

    <!-- Hero 主张 -->
    <section class="hero">
      <h1>每天 3 条，看懂 A 股舆情主线</h1>
      <p class="hero-sub">
        聚合新闻、公告、社媒与行情异动，AI 给出当日最值得关注的 3 条舆情预判，
        每条都附完整证据链与风险边界。
      </p>
      <div class="hero-actions">
        <el-button type="primary" size="large" @click="router.push('/register')">免费注册</el-button>
        <el-button size="large" @click="scrollToSample">查看预判样例</el-button>
      </div>
      <p class="hero-disclaimer">仅供舆情观察 · 不构成投资建议</p>
    </section>

    <!-- 三大能力 -->
    <section class="features">
      <div class="section-inner">
        <h2>三大核心能力</h2>
        <el-row :gutter="20">
          <el-col v-for="feature in FEATURES" :key="feature.title" :xs="24" :md="8">
            <el-card shadow="hover" class="feature-card">
              <el-icon class="feature-icon" :size="36"><component :is="feature.icon" /></el-icon>
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.text }}</p>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- 预判样例预览（锁定） -->
    <section ref="sampleSection" class="sample-preview">
      <div class="section-inner">
        <h2>预判样例</h2>
        <p class="muted sample-sub">以下为脱敏历史样例，注册后可查看每日最新完整预判与证据链</p>
        <div class="sample-wrap">
          <div class="sample-grid">
            <PredictionCard v-for="card in SAMPLE_CARDS" :key="card.id" :card="card" />
          </div>
          <div class="sample-mask">
            <el-icon :size="32"><Lock /></el-icon>
            <p>注册后解锁今日完整 3 条预判与证据链</p>
            <el-button type="primary" size="large" @click="router.push('/register')">
              免费注册解锁
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="home-footer">
      <p>仅供舆情观察 · 不构成投资建议</p>
      <p class="footer-text">
        本产品所有内容均基于公开舆情信息的自动化聚合与分析，不构成任何证券投资建议、
        收益承诺或风险担保。市场有风险，投资需谨慎。
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataAnalysis, Link, WarnTriangleFilled, Lock } from '@element-plus/icons-vue'
import PredictionCard from '../components/today/PredictionCard.vue'
import type { PredictionCard as PredictionCardType } from '../api/types'

const router = useRouter()
const sampleSection = ref<HTMLElement | null>(null)

function scrollToSample() {
  sampleSection.value?.scrollIntoView({ behavior: 'smooth' })
}

const FEATURES = [
  {
    icon: DataAnalysis,
    title: '今日 3 条预判',
    text: '每个交易日聚合全网舆情，只保留最值得关注的 3 条主线判断，拒绝信息过载。',
  },
  {
    icon: Link,
    title: '完整证据链',
    text: '每条预判附新闻、公告、社媒、行情异动的来源数量与可信度评估，判断有据可查。',
  },
  {
    icon: WarnTriangleFilled,
    title: '风险边界提醒',
    text: '识别先动后闻、消息兑现、过热分歧等风险场景，明确每条判断的失效条件。',
  },
]

// 脱敏静态样例：仅用于首页预览，不请求后端
const SAMPLE_CARDS: PredictionCardType[] = [
  {
    id: 'sample-1',
    rank: 1,
    title: '某科技主题持续升温',
    scenario: '同步共振',
    strength: '高',
    judgement: '新闻、舆情与板块表现同步增强，市场主线集中。',
    reason: '政策催化、产业订单与多平台舆情同时出现。',
    risk: '短期讨论过热，分歧可能放大。',
    next: '关注权威来源与公告证据是否持续补充。',
    evidence: '新闻 18 条 / 公告 2 条 / 社媒 260 条',
    tags: ['示例主题', '同步共振'],
  },
  {
    id: 'sample-2',
    rank: 2,
    title: '某制造板块景气验证中',
    scenario: '先闻后动',
    strength: '中-高',
    judgement: '产业新闻先出现，板块随后扩散，仍在验证阶段。',
    reason: '库存周期改善与政策支持延续。',
    risk: '周期波动与个股业绩分化。',
    next: '关注产能利用率与价格趋势数据。',
    evidence: '新闻 12 条 / 研报 9 条 / 社媒 142 条',
    tags: ['示例板块', '先闻后动'],
  },
  {
    id: 'sample-3',
    rank: 3,
    title: '先动后闻信号需警惕',
    scenario: '先动后闻',
    strength: '中',
    judgement: '部分个股先涨后发消息，存在消息兑现风险。',
    reason: '价格异动早于新闻扩散，消息源头可信度待验证。',
    risk: '消息不及预期、资金快速撤离。',
    next: '跟踪消息真实性与资金流向。',
    evidence: '新闻 7 条 / 股吧 96 条 / 异动 4 条',
    tags: ['风险提示', '先动后闻'],
  },
]
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #fff;
}

.home-topbar {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid #eef2f5;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--radar-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
}

.brand-name {
  font-weight: 600;
  font-size: 16px;
}

.hero {
  text-align: center;
  padding: 88px 24px 72px;
  background: linear-gradient(160deg, #0a3744 0%, #176b87 55%, #2d9596 100%);
  color: #fff;
  position: relative;
  overflow: hidden;
}

/* 漂浮光斑：让品牌渐变更有层次 */
.hero::before {
  content: '';
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(460px 460px at 15% 25%, rgba(116, 199, 199, 0.4), transparent 65%),
    radial-gradient(560px 560px at 88% 80%, rgba(255, 196, 110, 0.18), transparent 60%),
    radial-gradient(320px 320px at 75% 10%, rgba(45, 149, 150, 0.5), transparent 65%);
  filter: blur(12px);
  animation: hero-drift 18s ease-in-out infinite alternate;
}

/* 雷达扫描环：呼应产品主题 */
.hero::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -340px;
  width: 760px;
  height: 760px;
  margin-left: -380px;
  border-radius: 50%;
  background:
    repeating-radial-gradient(circle, rgba(255, 255, 255, 0.09) 0 1px, transparent 1px 76px),
    conic-gradient(from 0deg, rgba(116, 199, 199, 0.22), transparent 75deg, transparent 360deg);
  animation: hero-radar 16s linear infinite;
  pointer-events: none;
}

.hero > * {
  position: relative;
  z-index: 1;
}

@keyframes hero-drift {
  from {
    transform: translate3d(-2%, -2%, 0) scale(1);
  }
  to {
    transform: translate3d(2%, 3%, 0) scale(1.06);
  }
}

@keyframes hero-radar {
  to {
    transform: rotate(360deg);
  }
}

.hero h1 {
  margin: 0 0 18px;
  font-size: 38px;
  letter-spacing: 1px;
}

.hero-sub {
  max-width: 620px;
  margin: 0 auto 32px;
  font-size: 16px;
  line-height: 1.8;
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
}

.hero-disclaimer {
  margin-top: 26px;
  font-size: 12px;
  opacity: 0.7;
}

.section-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px;
}

.features {
  padding: 72px 0;
  /* 柔和过渡到样例区的浅色背景 */
  background:
    radial-gradient(600px 280px at 12% 0%, rgba(45, 149, 150, 0.08), transparent 70%),
    radial-gradient(600px 280px at 88% 100%, rgba(23, 107, 135, 0.07), transparent 70%),
    linear-gradient(180deg, #fff 0%, #f7fafb 100%);
}

.features h2,
.sample-preview h2 {
  text-align: center;
  font-size: 26px;
  margin: 0 0 32px;
}

.feature-card {
  border-radius: 14px;
  text-align: center;
  padding: 12px 8px;
  height: 100%;
  margin-bottom: 16px;
}

.feature-icon {
  color: var(--radar-brand);
  margin-bottom: 10px;
}

.feature-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
}

.feature-card p {
  margin: 0;
  font-size: 13px;
  color: #475669;
  line-height: 1.8;
}

.sample-preview {
  padding: 64px 0 80px;
  background: var(--radar-bg);
}

.sample-sub {
  text-align: center;
  margin: -20px 0 28px;
}

.sample-wrap {
  position: relative;
}

.sample-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  /* 禁用卡片内交互（如「查看证据」按钮） */
  pointer-events: none;
  user-select: none;
}

.sample-mask {
  position: absolute;
  inset: 35% 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  padding-bottom: 28px;
  background: linear-gradient(transparent, rgba(244, 247, 249, 0.96) 62%);
  color: var(--radar-brand);
}

.sample-mask p {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.home-footer {
  text-align: center;
  padding: 36px 24px 44px;
  border-top: 1px solid #eef2f5;
  color: #8492a6;
  font-size: 13px;
}

.footer-text {
  max-width: 680px;
  margin: 10px auto 0;
  font-size: 12px;
  line-height: 1.8;
}
</style>
