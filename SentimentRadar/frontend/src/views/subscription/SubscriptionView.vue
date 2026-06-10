<template>
  <div>
    <div class="page-head">
      <h2>订阅中心</h2>
      <p class="muted" v-if="data">{{ data.disclaimer }}</p>
    </div>

    <div v-if="loading" v-loading="true" class="loading-block" />
    <el-row v-else-if="data" :gutter="16">
      <el-col v-for="plan in data.plans" :key="plan.id" :xs="24" :sm="12" :lg="6">
        <el-card
          shadow="hover"
          class="plan-card"
          :class="{ recommended: plan.recommended }"
        >
          <el-tag v-if="plan.recommended" type="success" size="small" class="rec-tag">推荐</el-tag>
          <div class="audience muted">{{ plan.audience }}</div>
          <h3>{{ plan.name }}</h3>
          <div class="price">
            ¥{{ plan.price_month }}<small> / 月</small>
            <span v-if="plan.price_year" class="muted year">年付 ¥{{ plan.price_year }}</span>
          </div>
          <p class="summary">{{ plan.summary }}</p>
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
        </el-card>
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

.page-head h2 {
  margin: 0 0 6px;
}

.loading-block {
  height: 320px;
}

.plan-card {
  border-radius: 12px;
  margin-bottom: 16px;
  position: relative;
  height: calc(100% - 16px);
}

.plan-card.recommended {
  border-color: #74c7c7;
  box-shadow: 0 12px 36px rgba(23, 107, 135, 0.16);
}

.rec-tag {
  position: absolute;
  top: 14px;
  right: 14px;
}

.audience {
  margin-bottom: 4px;
}

h3 {
  margin: 0 0 8px;
  font-size: 17px;
}

.price {
  font-size: 26px;
  font-weight: 700;
  color: var(--radar-brand);
  margin-bottom: 8px;
}

.price small {
  font-size: 13px;
  font-weight: 400;
  color: #8492a6;
}

.year {
  font-size: 12px;
  font-weight: 400;
  margin-left: 8px;
}

.summary {
  font-size: 13px;
  color: #475669;
  line-height: 1.6;
  min-height: 42px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #475669;
}

.check {
  color: #2d9596;
  margin-right: 6px;
  font-weight: 700;
}

.subscribe-btn {
  width: 100%;
}
</style>
