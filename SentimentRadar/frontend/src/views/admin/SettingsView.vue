<template>
  <div v-if="loading" v-loading="true" class="loading-block" />
  <template v-else-if="settings">
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="panel">
          <template #header>今日规则权重</template>
          <el-form label-width="120px" size="default">
            <el-form-item label="主题热度权重">
              <el-slider v-model="settings.today_rules.topic_heat_weight" show-input :max="100" />
            </el-form-item>
            <el-form-item label="热度增速权重">
              <el-slider v-model="settings.today_rules.heat_growth_weight" show-input :max="100" />
            </el-form-item>
            <el-form-item label="用户相关性权重">
              <el-slider v-model="settings.today_rules.user_relevance_weight" show-input :max="100" />
            </el-form-item>
            <el-form-item label="风险降权">
              <el-switch v-model="settings.today_rules.risk_penalty_enabled" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="panel">
          <template #header>风险规则开关</template>
          <div v-for="(enabled, key) in settings.risk_rules" :key="key" class="rule-row">
            <span>{{ riskRuleLabels[key] ?? key }}</span>
            <el-switch v-model="settings.risk_rules[key]" />
          </div>
        </el-card>

        <el-card shadow="never" class="panel">
          <template #header>模型与成本</template>
          <el-form label-width="120px">
            <el-form-item label="主用模型">
              <el-input v-model="settings.model.primary_model" />
            </el-form-item>
            <el-form-item label="日成本上限">
              <el-input-number v-model="settings.model.daily_cost_limit" :min="0" :step="500" />
            </el-form-item>
            <el-form-item label="超时（秒）">
              <el-input-number v-model="settings.model.timeout_seconds" :min="5" :max="600" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="panel">
          <template #header>合规输出</template>
          <el-form label-width="80px">
            <el-form-item label="禁止词">
              <el-input-tag v-model="settings.compliance.forbidden_words" />
            </el-form-item>
            <el-form-item label="免责声明">
              <el-input v-model="settings.compliance.disclaimer" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="panel">
          <template #header>推送时间</template>
          <div v-for="(push, key) in settings.push" :key="key" class="rule-row">
            <span>{{ pushLabels[key] ?? key }}（{{ push.time }}）</span>
            <el-switch v-model="settings.push[key].enabled" />
          </div>
        </el-card>

        <el-card shadow="never" class="panel">
          <template #header>场景窗口（只读）</template>
          <div v-for="(text, key) in settings.scenario_windows" :key="key" class="kv">
            <span class="muted">{{ key }}</span>
            <span>{{ text }}</span>
          </div>
        </el-card>

        <el-button type="primary" size="large" class="save-btn" :loading="saving" @click="handleSave">
          保存平台设置
        </el-button>
      </el-col>
    </el-row>
  </template>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchAdminSettings, updateAdminSettings } from '../../api/admin'
import type { AdminSettings } from '../../api/types'

const settings = ref<AdminSettings | null>(null)
const loading = ref(true)
const saving = ref(false)

const riskRuleLabels: Record<string, string> = {
  cash_out: '消息兑现风险',
  overheat: '过热风险',
  unknown_source: '来源不明',
  regulatory: '监管风险',
}

const pushLabels: Record<string, string> = {
  morning: '早间推送',
  noon: '午间推送',
  close: '收盘推送',
}

onMounted(async () => {
  try {
    const result = await fetchAdminSettings()
    settings.value = result.settings
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  if (!settings.value) return
  saving.value = true
  try {
    const result = await updateAdminSettings(settings.value)
    settings.value = result.settings
    ElMessage.success(result.message || '平台设置已保存')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.loading-block {
  height: 320px;
}

.panel {
  border-radius: 12px;
  margin-bottom: 16px;
}

.rule-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 0;
  font-size: 14px;
  border-bottom: 1px solid #f0f3f7;
}

.rule-row:last-child {
  border-bottom: none;
}

.kv {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 13px;
  padding: 6px 0;
}

.save-btn {
  width: 100%;
}
</style>
