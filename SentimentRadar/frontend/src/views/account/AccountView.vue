<template>
  <div>
    <div class="page-head">
      <h2>我的账户</h2>
    </div>

    <div v-if="loading" v-loading="true" class="loading-block" />
    <template v-else-if="account">
      <el-row :gutter="16">
        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="panel">
            <template #header>基本资料</template>
            <div class="kv"><span class="muted">姓名</span><span>{{ account.user.name }}</span></div>
            <div class="kv"><span class="muted">邮箱</span><span>{{ account.user.email }}</span></div>
            <div class="kv"><span class="muted">手机</span><span>{{ account.user.phone }}</span></div>
            <div class="kv"><span class="muted">角色</span><span>{{ account.user.role_label }}</span></div>
            <div class="kv">
              <span class="muted">风险声明</span>
              <span>{{ account.user.risk_version }}（{{ account.user.risk_confirmed ? '已确认' : '未确认' }}）</span>
            </div>
            <div class="kv"><span class="muted">最近登录</span><span>{{ account.user.last_login_at }}</span></div>
          </el-card>

          <el-card shadow="never" class="panel">
            <template #header>
              <div class="panel-head">
                <span>当前订阅</span>
                <el-button type="primary" link @click="$router.push('/subscription')">去升级 →</el-button>
              </div>
            </template>
            <div class="kv">
              <span class="muted">套餐</span>
              <el-tag size="small">{{ account.subscription.plan_name }}</el-tag>
            </div>
            <div class="kv"><span class="muted">状态</span><span>{{ account.subscription.status }}</span></div>
            <div class="kv"><span class="muted">开始日期</span><span>{{ account.subscription.started_at || '-' }}</span></div>
            <div class="kv"><span class="muted">到期日期</span><span>{{ account.subscription.expires_at }}</span></div>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-card shadow="never" class="panel">
            <template #header>权益用量</template>
            <div v-for="(item, key) in account.usage" :key="key" class="usage-row">
              <div class="usage-label">
                <span>{{ item.label }}</span>
                <span class="muted">{{ item.used }} / {{ item.limit }}</span>
              </div>
              <el-progress
                :percentage="Math.min(100, Math.round((item.used / Math.max(item.limit, 1)) * 100))"
                :stroke-width="8"
                :show-text="false"
              />
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="panel">
        <template #header>账单记录</template>
        <el-table :data="account.bills" size="default">
          <el-table-column prop="id" label="账单号" min-width="160" />
          <el-table-column prop="plan" label="套餐" min-width="120" />
          <el-table-column prop="amount" label="金额" width="100">
            <template #default="{ row }">¥{{ row.amount }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="paid_at" label="支付日期" width="120" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchAccount } from '../../api/account'
import type { AccountAggregate } from '../../api/types'

const account = ref<AccountAggregate | null>(null)
const loading = ref(true)

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

.page-head h2 {
  margin: 0;
}

.loading-block {
  height: 320px;
}

.panel {
  border-radius: 12px;
  margin-bottom: 16px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kv {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 7px 0;
}

.usage-row {
  margin-bottom: 16px;
}

.usage-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 6px;
}
</style>
