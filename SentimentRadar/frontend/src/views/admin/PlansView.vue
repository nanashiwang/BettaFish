<template>
  <el-card shadow="never" class="panel">
    <template #header>订阅套餐管理</template>
    <el-table v-loading="loading" :data="plans">
      <el-table-column prop="name" label="套餐" width="110" />
      <el-table-column label="月价" width="120">
        <template #default="{ row }">
          <el-input-number v-model="row.price_month" :min="0" size="small" controls-position="right" />
        </template>
      </el-table-column>
      <el-table-column label="年价" width="120">
        <template #default="{ row }">
          <el-input-number v-model="row.price_year" :min="0" size="small" controls-position="right" />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-select v-model="row.status" size="small">
            <el-option label="上架中" value="上架中" />
            <el-option label="已下架" value="已下架" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="简介" min-width="200">
        <template #default="{ row }">
          <el-input v-model="row.summary" size="small" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link :loading="savingId === row.id" @click="handleSave(row)">
            保存
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchAdminPlans, updatePlan } from '../../api/admin'
import type { Plan } from '../../api/types'

const plans = ref<Plan[]>([])
const loading = ref(true)
const savingId = ref('')

async function load() {
  try {
    const result = await fetchAdminPlans()
    plans.value = result.plans
  } finally {
    loading.value = false
  }
}

async function handleSave(plan: Plan) {
  savingId.value = plan.id
  try {
    const result = await updatePlan(plan.id, {
      name: plan.name,
      price_month: plan.price_month,
      price_year: plan.price_year,
      status: plan.status,
      summary: plan.summary,
    })
    ElMessage.success(result.message || '套餐已保存')
  } finally {
    savingId.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.panel {
  border-radius: 12px;
}
</style>
