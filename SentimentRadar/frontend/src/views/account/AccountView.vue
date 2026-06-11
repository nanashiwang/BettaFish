<template>
  <div>
    <div class="page-head fade-up">
      <h2 class="section-title">我的账户</h2>
    </div>

    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="account">
      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <div class="glass-card panel fade-up fade-up-1">
            <h3 class="section-title">基本资料</h3>
            <div class="kv"><span class="muted">用户名</span><span>{{ account.user.name }}</span></div>
            <div class="kv"><span class="muted">邮箱</span><span>{{ account.user.email }}</span></div>
            <div class="kv"><span class="muted">角色</span><span>{{ account.user.role_label }}</span></div>
            <div class="kv">
              <span class="muted">风险声明</span>
              <span>{{ account.user.risk_version }}（{{ account.user.risk_confirmed ? '已确认' : '未确认' }}）</span>
            </div>
            <div class="kv"><span class="muted">最近登录</span><span class="num">{{ account.user.last_login_at }}</span></div>
          </div>

          <div class="glass-card panel fade-up fade-up-2">
            <div class="panel-head">
              <h3 class="section-title">当前订阅</h3>
              <el-button type="primary" link @click="$router.push('/subscription')">去升级 →</el-button>
            </div>
            <div class="kv">
              <span class="muted">套餐</span>
              <el-tag size="small">{{ account.subscription.plan_name }}</el-tag>
            </div>
            <div class="kv"><span class="muted">状态</span><span>{{ account.subscription.status }}</span></div>
            <div class="kv"><span class="muted">开始日期</span><span class="num">{{ account.subscription.started_at || '-' }}</span></div>
            <div class="kv"><span class="muted">到期日期</span><span class="num">{{ account.subscription.expires_at }}</span></div>
          </div>
        </el-col>

        <el-col :xs="24" :md="12">
          <div class="glass-card panel fade-up fade-up-3">
            <h3 class="section-title">权益用量</h3>
            <div v-for="(item, key) in account.usage" :key="key" class="usage-row">
              <div class="usage-label">
                <span>{{ item.label }}</span>
                <span class="muted num">{{ item.used }} / {{ item.limit }}</span>
              </div>
              <el-progress
                :percentage="Math.min(100, Math.round((item.used / Math.max(item.limit, 1)) * 100))"
                :stroke-width="8"
                :show-text="false"
                :color="progressColor"
              />
            </div>
          </div>
        </el-col>
      </el-row>

      <div class="glass-card panel fade-up fade-up-4">
        <h3 class="section-title">账单记录</h3>
        <el-table :data="account.bills">
          <el-table-column prop="id" label="账单号" min-width="160" />
          <el-table-column prop="plan" label="套餐" min-width="120" />
          <el-table-column prop="amount" label="金额" width="100">
            <template #default="{ row }"><span class="num">¥{{ row.amount }}</span></template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="paid_at" label="支付日期" width="120" />
        </el-table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchAccount } from '../../api/account'
import type { AccountAggregate } from '../../api/types'

const account = ref<AccountAggregate | null>(null)
const loading = ref(true)

const progressColor = [
  { color: '#2dd4bf', percentage: 70 },
  { color: '#fbbf24', percentage: 90 },
  { color: '#f87171', percentage: 100 },
]

onMounted(async () => {
  try {
    account.value = await fetchAccount()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-head {
  margin-bottom: 20px;
}

.loading-block {
  height: 320px;
}

.panel {
  padding: 20px 22px;
  margin-bottom: 16px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.kv {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 7px 0;
}

.usage-row {
  margin-bottom: 18px;
}

.usage-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
}
</style>
