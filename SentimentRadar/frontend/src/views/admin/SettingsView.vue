<template>
  <div>
    <!-- 雷达管线：真实信号产线的配置与运行管理 -->
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="panel-head">
          <span>雷达管线（舆情-价格背离信号）</span>
          <div>
            <el-button :loading="pipelineRunning" type="success" @click="handleRunPipeline">
              立即运行
            </el-button>
            <el-button :loading="pipelineSaving" type="primary" @click="handleSavePipeline">
              保存配置
            </el-button>
          </div>
        </div>
      </template>
      <div v-if="pipelineLoading" v-loading="true" class="loading-block-sm" />
      <template v-else-if="pipeline">
        <el-form label-width="120px">
          <el-form-item label="自动调度">
            <el-switch v-model="pipeline.enabled" />
            <span class="muted form-hint">开启后按下方时间每日自动运行</span>
          </el-form-item>
          <el-form-item label="运行时间">
            <div class="time-list">
              <div v-for="(time, index) in pipeline.run_times" :key="index" class="time-row">
                <el-time-select
                  v-model="pipeline.run_times[index]"
                  start="00:00"
                  end="23:55"
                  step="00:05"
                  placeholder="HH:MM"
                  style="width: 140px"
                />
                <el-button
                  text
                  type="danger"
                  :disabled="pipeline.run_times.length <= 1"
                  @click="pipeline.run_times.splice(index, 1)"
                >
                  删除
                </el-button>
              </div>
              <el-button text type="primary" @click="pipeline.run_times.push('16:35')">
                + 添加时间
              </el-button>
            </div>
          </el-form-item>
          <el-form-item label="LLM 模型">
            <el-input v-model="pipeline.llm_model" placeholder="例如 gpt-5.4-mini" style="max-width: 280px" />
          </el-form-item>
          <el-form-item label="tushare token">
            <el-input
              v-model="pipeline.tushare_token"
              type="password"
              show-password
              placeholder="行情数据源凭证；已配置时显示 ******"
              style="max-width: 400px"
            />
          </el-form-item>
        </el-form>

        <div class="runs-head">
          <span class="muted">最近运行记录</span>
          <el-button text type="primary" @click="loadRuns">刷新</el-button>
        </div>
        <el-table :data="runs" size="small" v-loading="runsLoading">
          <el-table-column prop="id" label="#" width="50" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="runStatusType(row.status)" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="stage" label="阶段" width="90" />
          <el-table-column prop="started_at" label="开始时间" width="170" />
          <el-table-column prop="finished_at" label="结束时间" width="170" />
          <el-table-column prop="message" label="消息" min-width="200" show-overflow-tooltip />
        </el-table>
      </template>
    </el-card>

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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchAdminSettings,
  fetchRadarConfig,
  fetchRadarRuns,
  runRadarPipeline,
  updateAdminSettings,
  updateRadarConfig,
} from '../../api/admin'
import type { AdminSettings, RadarPipelineConfig, RadarPipelineRun } from '../../api/types'

const settings = ref<AdminSettings | null>(null)
const loading = ref(true)
const saving = ref(false)

// ---------- 雷达管线 ----------
const pipeline = ref<RadarPipelineConfig | null>(null)
const pipelineLoading = ref(true)
const pipelineSaving = ref(false)
const pipelineRunning = ref(false)
const runs = ref<RadarPipelineRun[]>([])
const runsLoading = ref(false)

function runStatusType(status: string) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  return 'warning'
}

async function loadPipeline() {
  try {
    const result = await fetchRadarConfig()
    pipeline.value = result.config
  } finally {
    pipelineLoading.value = false
  }
}

async function loadRuns() {
  runsLoading.value = true
  try {
    const result = await fetchRadarRuns()
    runs.value = result.runs
  } finally {
    runsLoading.value = false
  }
}

async function handleSavePipeline() {
  if (!pipeline.value) return
  pipelineSaving.value = true
  try {
    const result = await updateRadarConfig(pipeline.value)
    pipeline.value = result.config
    ElMessage.success('管线配置已保存')
  } finally {
    pipelineSaving.value = false
  }
}

async function handleRunPipeline() {
  pipelineRunning.value = true
  try {
    const result = await runRadarPipeline()
    ElMessage.success(result.message || '管线已启动')
    await loadRuns()
  } finally {
    pipelineRunning.value = false
  }
}

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
  loadPipeline()
  loadRuns()
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

.loading-block-sm {
  height: 120px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-hint {
  margin-left: 12px;
}

.time-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.time-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.runs-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10px 0 6px;
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
