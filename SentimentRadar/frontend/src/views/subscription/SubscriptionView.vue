<template>
  <div>
    <div class="page-head fade-up">
      <h2 class="section-title">订阅中心</h2>
      <p class="muted" v-if="data">{{ data.disclaimer }}</p>
    </div>

    <div v-if="loading" v-loading="true" class="loading-block" />
    <el-row v-else-if="data" :gutter="16">
      <el-col v-for="(plan, index) in data.plans" :key="plan.id" :xs="24" :sm="12" :lg="6">
        <div
          class="glass-card hoverable plan-card fade-up"
          :class="[`fade-up-${index + 1}`, { recommended: plan.recommended }]"
        >
          <span v-if="plan.recommended" class="rec-tag">推荐</span>
          <div class="audience muted">{{ plan.audience }}</div>
          <h3>{{ plan.name }}</h3>
          <div class="price num">
            ¥{{ plan.price_month }}<small> / 月</small>
            <span class="faint year num" v-if="plan.price_year">年付 ¥{{ plan.price_year }}</span>
          </div>
          <p class="summary muted">{{ plan.summary }}</p>
          <div class="features">
            <div v-for="feature in plan.features" :key="feature" class="feature">
              <span class="check">✓</span>{{ feature }}
            </div>
          </div>
          <el-button
            class="subscribe-btn"
            :type="plan.id === data.current_plan_id ? 'default' : 'primary'"
            :disabled="plan.id === data.current_plan_id"
            :loading="subscribingId === plan.id"
            @click="handleSubscribe(plan)"
          >
            {{ plan.id === data.current_plan_id ? '当前方案' : `选择${plan.name}` }}
          </el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchPlans, subscribePlan } from '../../api/account'
import type { Plan, PlansResult } from '../../api/types'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const data = ref<PlansResult | null>(null)
const loading = ref(true)
const subscribingId = ref('')

async function load() {
  try {
    data.value = await fetchPlans()
  } finally {
    loading.value = false
  }
}

async function handleSubscribe(plan: Plan) {
  subscribingId.value = plan.id
  try {
    const result = await subscribePlan(plan.id)
    ElMessage.success(result.message || '订阅成功')
    // 同步用户菜单中的套餐显示，并刷新当前方案标记
    await Promise.all([auth.refreshSubscription(), load()])
  } finally {
    subscribingId.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.page-head {
  margin-bottom: 20px;
}

.loading-block {
  height: 320px;
}

.plan-card {
  position: relative;
  padding: 24px 22px;
  margin-bottom: 16px;
  height: calc(100% - 16px);
  display: flex;
  flex-direction: column;
}

/* 推荐套餐：渐变描边 + 辉光 */
.plan-card.recommended {
  border-color: transparent;
  background:
    linear-gradient(var(--bg-elevated), var(--bg-elevated)) padding-box,
    linear-gradient(135deg, var(--brand), var(--accent)) border-box;
  box-shadow:
    0 0 32px rgba(45, 212, 191, 0.18),
    0 8px 32px rgba(0, 0, 0, 0.35);
}

.rec-tag {
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  color: #04211d;
  background: linear-gradient(135deg, var(--brand), var(--accent));
}

.audience {
  margin-bottom: 4px;
  font-size: 12px;
}

h3 {
  margin: 0 0 8px;
  font-size: 17px;
}

.price {
  font-size: 28px;
  font-weight: 700;
  color: var(--brand);
  margin-bottom: 8px;
}

.price small {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-faint);
}

.year {
  font-size: 12px;
  font-weight: 400;
  margin-left: 8px;
}

.summary {
  font-size: 13px;
  line-height: 1.6;
  min-height: 42px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 18px;
  font-size: 13px;
  color: var(--text-secondary);
  flex: 1;
}

.check {
  color: var(--brand);
  margin-right: 6px;
  font-weight: 700;
}

.subscribe-btn {
  width: 100%;
}
</style>
