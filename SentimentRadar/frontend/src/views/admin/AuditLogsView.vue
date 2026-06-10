<template>
  <el-card shadow="never" class="panel">
    <template #header>审计日志</template>
    <el-table v-loading="loading" :data="logs">
      <el-table-column prop="time" label="时间" width="190" />
      <el-table-column prop="actor" label="操作人" width="160" />
      <el-table-column prop="action" label="动作" width="140" />
      <el-table-column prop="target" label="对象" />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { fetchAuditLogs } from '../../api/admin'
import type { AuditLog } from '../../api/types'

const logs = ref<AuditLog[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const result = await fetchAuditLogs()
    logs.value = result.logs
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.panel {
  border-radius: 12px;
}
</style>
