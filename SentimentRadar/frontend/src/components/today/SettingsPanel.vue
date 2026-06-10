<template>
  <div v-if="loading" v-loading="true" class="loading-block" />
  <template v-else-if="settings">
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="panel">
          <template #header>关注对象</template>
          <div class="group">
            <div class="group-label muted">股票</div>
            <el-tag v-for="item in settings.focus_targets.stocks" :key="item" size="small" effect="plain">
              {{ item }}
            </el-tag>
          </div>
          <div class="group">
            <div class="group-label muted">主题</div>
            <el-tag v-for="item in settings.focus_targets.themes" :key="item" size="small" effect="plain">
              {{ item }}
            </el-tag>
          </div>
          <div class="group">
            <div class="group-label muted">板块</div>
            <el-tag v-for="item in settings.focus_targets.sectors" :key="item" size="small" effect="plain">
              {{ item }}
            </el-tag>
          </div>
        </el-card>

        <el-card shadow="never" class="panel">
          <template #header>风险偏好与推送渠道</template>
          <div class="group">
            <div class="group-label muted">风险偏好</div>
            <el-tag v-for="item in settings.risk_preferences" :key="item" size="small" type="warning" effect="plain">
              {{ item }}
            </el-tag>
          </div>
          <div class="group">
            <div class="group-label muted">推送渠道</div>
            <el-tag v-for="item in settings.channels" :key="item" size="small" effect="plain">
              {{ item }}
            </el-tag>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="panel">
          <template #header>推送模板</template>
          <div v-for="template in settings.push_templates" :key="template.id" class="template-row">
            <div>
              <div>{{ template.name }}</div>
              <div class="muted">{{ template.time }}</div>
            </div>
            <el-switch v-model="template.enabled" />
          </div>
          <el-button type="primary" class="save-btn" :loading="saving" @click="handleSave">
            保存设置
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </template>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchSettings, saveSettings } from '../../api/radar'
import type { RadarSettings } from '../../api/types'

const settings = ref<RadarSettings | null>(null)
const loading = ref(true)
const saving = ref(false)

onMounted(async () => {
  try {
    const result = await fetchSettings()
    settings.value = result.settings
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  if (!settings.value) return
  saving.value = true
  try {
    const result = await saveSettings(settings.value)
    settings.value = result.settings
    ElMessage.success(result.message || '设置已保存')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.loading-block {
  height: 240px;
}

.panel {
  border-radius: 12px;
  margin-bottom: 16px;
}

.group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 0;
}

.group-label {
  width: 40px;
  flex-shrink: 0;
}

.template-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f3f7;
  font-size: 14px;
}

.save-btn {
  margin-top: 16px;
  width: 100%;
}
</style>
