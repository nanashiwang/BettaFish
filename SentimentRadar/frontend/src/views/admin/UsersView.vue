<template>
  <div>
    <el-card shadow="never" class="panel user-panel">
      <template #header>
        <div class="panel-head">
          <span>用户管理</span>
          <small class="muted">显示 {{ filteredUsers.length }} / {{ total }} 人</small>
        </div>
      </template>

      <div class="toolbar">
        <div class="left-actions">
          <el-button type="primary" link>添加用户</el-button>
          <el-button>IP 黑名单</el-button>
          <el-button disabled>批量启用</el-button>
          <el-button disabled>批量禁用</el-button>
          <el-button disabled>批量拉黑IP</el-button>
          <el-button disabled>批量删除</el-button>
        </div>
        <div class="filters">
          <el-input v-model="keyword" clearable placeholder="ID/用户名" class="search-input" />
          <el-select v-model="groupFilter" clearable placeholder="选择分组" class="group-select">
            <el-option v-for="item in groupOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="advancedOpen = !advancedOpen">高级筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>

      <div v-if="advancedOpen" class="advanced-row">
        <el-tag>状态、角色、余额区间后续可接后端筛选</el-tag>
      </div>

      <el-table v-loading="loading" :data="filteredUsers" :fit="false" size="small" class="users-table" border>
        <el-table-column type="selection" width="42" />
        <el-table-column label="ID" width="76">
          <template #default="{ row }">{{ displayId(row) }}</template>
        </el-table-column>
        <el-table-column label="用户名" min-width="120">
          <template #default="{ row }">{{ row.username || row.name }}</template>
        </el-table-column>
        <el-table-column label="邮箱" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.email }}</span>
            <el-button link size="small" @click="copyEmail(row.email)">copy</el-button>
          </template>
        </el-table-column>
        <el-table-column label="注册来源" width="112">
          <template #default="{ row }">
            <el-tag size="small">{{ row.registration_source || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册 IP" width="132">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.register_ip || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="套餐情况" width="108">
          <template #default="{ row }">
            <el-button link size="small">{{ row.plan || '无套餐' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="已使用余额" width="108">
          <template #default="{ row }">
            <el-tag :type="balanceTagType(row.used_balance)" size="small">{{ row.used_balance || '$0.00' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分组" width="92">
          <template #default="{ row }">
            <el-button link size="small">{{ row.group || 'default' }}</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="232" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button :type="row.status === '已启用' ? 'danger' : 'success'" link @click="toggleStatus(row)">
                {{ row.status === '已启用' ? '禁用' : '启用' }}
              </el-button>
              <el-button link @click="openDetail(row)">编辑</el-button>
              <el-button type="warning" link @click="promote(row)">提升</el-button>
              <el-button type="primary" link @click="demote(row)">降级</el-button>
              <el-dropdown trigger="click" @command="(command: string) => handleMore(command, row)">
                <el-button link class="more-button">more</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="subscription">订阅管理</el-dropdown-item>
                    <el-dropdown-item command="blacklist-ip" class="danger-item">拉黑注册 IP</el-dropdown-item>
                    <el-dropdown-item command="passkey">重置 Passkey</el-dropdown-item>
                    <el-dropdown-item command="2fa">重置 2FA</el-dropdown-item>
                    <el-dropdown-item command="close" divided class="danger-item">注销</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="`编辑用户：${editing?.username || editing?.name || ''}`" width="620px">
      <div v-if="detailLoading" v-loading="true" class="loading-block" />
      <template v-else-if="detail && editing">
        <el-descriptions :column="2" border size="small" class="detail-desc">
          <el-descriptions-item label="ID">{{ displayId(detail.user) }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detail.user.email }}</el-descriptions-item>
          <el-descriptions-item label="注册来源">{{ detail.user.registration_source || '-' }}</el-descriptions-item>
          <el-descriptions-item label="注册 IP">{{ detail.user.register_ip || '-' }}</el-descriptions-item>
          <el-descriptions-item label="到期">{{ detail.user.expires_at }}</el-descriptions-item>
          <el-descriptions-item label="用量">{{ detail.user.usage }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-width="84px" class="edit-form">
          <el-form-item label="状态">
            <el-select v-model="editing.status">
              <el-option v-for="item in ['已启用', '已禁用', '冻结']" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="editing.role">
              <el-option v-for="item in ['普通用户', '订阅用户', '创作者', '管理员']" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="分组">
            <el-input v-model="editing.group" placeholder="default" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="editing.note" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchUserDetail, fetchUsers, updateUser } from '../../api/admin'
import type { AdminUser, AdminUserDetail } from '../../api/types'

const users = ref<AdminUser[]>([])
const total = ref(0)
const loading = ref(true)
const keyword = ref('')
const groupFilter = ref('')
const advancedOpen = ref(false)

const dialogVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<AdminUserDetail | null>(null)
const editing = ref<AdminUser | null>(null)
const saving = ref(false)

const groupOptions = computed(() => (
  [...new Set(users.value.map((user) => user.group || 'default'))]
))

const filteredUsers = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return users.value.filter((user) => {
    const matchKeyword = !kw || [displayId(user), user.username, user.name, user.email]
      .some((value) => String(value || '').toLowerCase().includes(kw))
    const matchGroup = !groupFilter.value || (user.group || 'default') === groupFilter.value
    return matchKeyword && matchGroup
  })
})

function displayId(user: AdminUser) {
  return String(user.id || '').replace(/^u_/, '')
}

function statusTagType(status: string) {
  if (status === '已启用') return 'success'
  if (status === '冻结' || status === '已禁用') return 'danger'
  return 'info'
}

function balanceTagType(value = '') {
  const amount = Number(String(value).replace(/[^0-9.-]/g, ''))
  if (Number.isNaN(amount)) return 'info'
  if (amount > 10) return 'warning'
  return 'info'
}

async function copyEmail(email: string) {
  await navigator.clipboard?.writeText(email)
  ElMessage.success('邮箱已复制')
}

function resetFilters() {
  keyword.value = ''
  groupFilter.value = ''
  advancedOpen.value = false
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

async function patchUser(user: AdminUser, payload: Partial<AdminUser>, message: string) {
  const result = await updateUser(user.id, payload)
  ElMessage.success(result.message || message)
  await load()
}

async function toggleStatus(user: AdminUser) {
  const status = user.status === '已启用' ? '已禁用' : '已启用'
  await patchUser(user, { status }, status === '已启用' ? '已启用' : '已禁用')
}

async function promote(user: AdminUser) {
  await patchUser(user, { role: '管理员' }, '已提升为管理员')
}

async function demote(user: AdminUser) {
  await patchUser(user, { role: '普通用户' }, '已降级为普通用户')
}

function handleMore(command: string, user: AdminUser) {
  const labels: Record<string, string> = {
    subscription: '订阅管理',
    'blacklist-ip': '拉黑注册 IP',
    passkey: '重置 Passkey',
    '2fa': '重置 2FA',
    close: '注销',
  }
  ElMessage.info(`${labels[command] || command}：${user.username || user.name}`)
}

async function handleSave() {
  if (!editing.value) return
  saving.value = true
  try {
    const result = await updateUser(editing.value.id, {
      status: editing.value.status,
      role: editing.value.role,
      group: editing.value.group,
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

.panel-head,
.toolbar,
.left-actions,
.filters,
.row-actions {
  display: flex;
  align-items: center;
}

.panel-head {
  justify-content: space-between;
}

.toolbar {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.left-actions,
.filters,
.row-actions {
  gap: 6px;
  flex-wrap: wrap;
}

.search-input {
  width: 220px;
}

.group-select {
  width: 150px;
}

.advanced-row {
  margin-bottom: 10px;
}

.users-table :deep(.el-table__cell) {
  padding: 7px 0;
}

.users-table :deep(.cell) {
  white-space: nowrap;
}

.users-table :deep(.el-table__body),
.users-table :deep(.el-table__header) {
  min-width: 1292px;
}

.row-actions {
  flex-wrap: nowrap;
  white-space: nowrap;
}

.more-button {
  color: var(--text-muted);
}

:deep(.danger-item) {
  color: #f87171;
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
</style>
