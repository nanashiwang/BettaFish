<template>
  <div>
    <el-card shadow="never" class="panel">
      <template #header>用户管理（共 {{ total }} 人）</template>
      <el-table v-loading="loading" :data="users">
        <el-table-column prop="name" label="用户" min-width="100" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column prop="role" label="角色" width="100" />
        <el-table-column prop="plan" label="套餐" width="100" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_active" label="最近活跃" width="110" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">详情 / 编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="`用户详情：${editing?.name ?? ''}`" width="560px">
      <div v-if="detailLoading" v-loading="true" class="loading-block" />
      <template v-else-if="detail && editing">
        <el-descriptions :column="2" border size="small" class="detail-desc">
          <el-descriptions-item label="邮箱">{{ detail.user.email }}</el-descriptions-item>
          <el-descriptions-item label="手机">{{ detail.user.phone }}</el-descriptions-item>
          <el-descriptions-item label="到期">{{ detail.user.expires_at }}</el-descriptions-item>
          <el-descriptions-item label="用量">{{ detail.user.usage }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-width="60px" class="edit-form">
          <el-form-item label="状态">
            <el-select v-model="editing.status">
              <el-option v-for="item in ['正常', '高用量', '未订阅', '冻结']" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="editing.role">
              <el-option
                v-for="item in ['订阅用户', '免费用户', '创作者', '管理员']"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="editing.note" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>

        <h4 class="sub-title">推送记录</h4>
        <el-table :data="detail.push_logs" size="small">
          <el-table-column prop="template" label="模板" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column prop="sent_at" label="时间" width="90" />
        </el-table>
      </template>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchUserDetail, fetchUsers, updateUser } from '../../api/admin'
import type { AdminUser, AdminUserDetail } from '../../api/types'

const users = ref<AdminUser[]>([])
const total = ref(0)
const loading = ref(true)

const dialogVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<AdminUserDetail | null>(null)
const editing = ref<AdminUser | null>(null)
const saving = ref(false)

function statusTagType(status: string) {
  if (status === '正常') return 'success'
  if (status === '高用量') return 'warning'
  if (status === '冻结') return 'danger'
  return 'info'
}

async function load() {
  loading.value = true
  try {
    const result = await fetchUsers()
    users.value = result.users
    total.value = result.total
  } finally {
    loading.value = false
  }
}

async function openDetail(user: AdminUser) {
  editing.value = { ...user }
  dialogVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await fetchUserDetail(user.id)
  } finally {
    detailLoading.value = false
  }
}

async function handleSave() {
  if (!editing.value) return
  saving.value = true
  try {
    const result = await updateUser(editing.value.id, {
      status: editing.value.status,
      role: editing.value.role,
      note: editing.value.note,
    })
    ElMessage.success(result.message || '已保存')
    dialogVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.panel {
  border-radius: 12px;
}

.loading-block {
  height: 200px;
}

.detail-desc {
  margin-bottom: 16px;
}

.edit-form {
  margin-bottom: 8px;
}

.sub-title {
  margin: 8px 0;
  font-size: 14px;
  color: var(--brand);
}
</style>
