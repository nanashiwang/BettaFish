<template>
  <div>
    <div class="page-head fade-up">
      <h2 class="section-title">订阅中心</h2>
      <p class="muted" v-if="data">{{ data.disclaimer }}</p>
      <div class="purchase-controls">
        <el-radio-group v-model="period" size="small">
          <el-radio-button value="month">月付</el-radio-button>
          <el-radio-button value="year">年付</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="payType" size="small">
          <el-radio-button value="alipay">支付宝</el-radio-button>
          <el-radio-button value="wxpay">微信</el-radio-button>
          <el-radio-button value="qqpay">QQ</el-radio-button>
        </el-radio-group>
      </div>
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
            ¥{{ planPrice(plan) }}<small> / {{ period === 'year' ? '年' : '月' }}</small>
            <span class="faint year num" v-if="period === 'month' && plan.price_year">年付 ¥{{ plan.price_year }}</span>
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
const period = ref<'month' | 'year'>('month')
const payType = ref('alipay')

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
    const result = await subscribePlan(plan.id, period.value, payType.value)
    if (result.payment_required && result.payment_url) {
      ElMessage.success(result.message || '订单已创建')
      window.location.href = result.payment_url
      return
    }
    ElMessage.success(result.message || '订阅成功')
    await Promise.all([auth.refreshSubscription(), load()])
  } finally {
    subscribingId.value = ''
  }
}

function planPrice(plan: Plan) {
  return period.value === 'year' ? plan.price_year : plan.price_month
}

onMounted(load)
</script>

<style scoped>
.page-head {
  margin-bottom: 20px;
}

.purchase-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
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
