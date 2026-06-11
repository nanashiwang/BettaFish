<template>
  <div>
    <!-- 系统接入配置：从旧首页配置弹窗迁入 Radar 后台 -->
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="panel-head">
          <div>
            <span>系统接入配置</span>
            <span class="muted form-hint">统一管理旧控制台、三大 Engine 与 Radar LLM</span>
          </div>
          <div class="action-row">
            <el-tag v-if="systemStatus" :type="systemStatus.started ? 'success' : systemStatus.starting ? 'warning' : 'info'">
              {{ systemStatus.starting ? '启动中' : systemStatus.started ? '已启动' : '未启动' }}
            </el-tag>
            <el-button :loading="systemLoading" @click="loadSystemConfig">刷新</el-button>
            <el-button :loading="systemSaving" type="primary" @click="handleSaveSystemConfig()">
              保存配置
            </el-button>
            <el-button
              :loading="systemStarting"
              :disabled="systemStatus?.started || systemStatus?.starting"
              type="success"
              @click="handleStartSystem"
            >
              保存并启动系统
            </el-button>
            <el-popconfirm
              title="会停止当前控制台启动的子进程，并可能关闭服务进程，确定继续？"
              confirm-button-text="确定关闭"
              cancel-button-text="取消"
              @confirm="handleShutdownSystem"
            >
              <template #reference>
                <el-button :loading="systemStopping" type="danger" plain>关闭系统</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </template>

      <div v-if="systemLoading" v-loading="true" class="loading-block-sm" />
      <template v-else>
        <el-alert
          class="system-alert"
          type="info"
          :closable="false"
          show-icon
          title="这里承接 http://127.0.0.1:5010/ 旧首页的配置与启动功能；Radar 管线仍在下方单独配置 tushare。"
        />
        <el-collapse v-model="systemActiveGroups">
          <el-collapse-item v-for="group in systemConfigGroups" :key="group.title" :name="group.title">
            <template #title>
              <div>
                <b>{{ group.title }}</b>
                <span class="muted group-subtitle">{{ group.subtitle }}</span>
              </div>
            </template>
            <el-row :gutter="16">
              <el-col
                v-for="field in visibleSystemFields(group.fields)"
                :key="field.key"
                :xs="24"
                :md="field.wide ? 24 : 8"
              >
                <el-form-item :label="field.label">
                  <el-select
                    v-if="field.type === 'select'"
                    v-model="systemConfig[field.key]"
                    style="width: 100%"
                    @change="systemDirty = true"
                  >
                    <el-option v-for="option in field.options" :key="option" :label="option" :value="option" />
                  </el-select>
                  <el-input
                    v-else
                    v-model="systemConfig[field.key]"
                    :type="field.type === 'password' ? 'password' : 'text'"
                    :show-password="field.type === 'password'"
                    :placeholder="`填写${field.label}`"
                    @input="systemDirty = true"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
        <p class="muted config-note">
          配置会写入根目录 .env；端口字段会自动转数字。{{ systemDirty ? '当前有未保存修改。' : '当前配置已同步。' }}
        </p>
      </template>
    </el-card>

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
  fetchSystemConfig,
  fetchSystemStatus,
  runRadarPipeline,
  shutdownSystemServices,
  startSystemServices,
  updateAdminSettings,
  updateRadarConfig,
  updateSystemConfig,
} from '../../api/admin'
import type { AdminSettings, RadarPipelineConfig, RadarPipelineRun, SystemConfig, SystemStatus } from '../../api/types'

const settings = ref<AdminSettings | null>(null)
const loading = ref(true)
const saving = ref(false)

// ---------- 旧首页系统配置 ----------
type SystemConfigField = {
  key: string
  label: string
  type?: 'text' | 'password' | 'select'
  options?: string[]
  wide?: boolean
  condition?: { key: string; value: string }
}

type SystemConfigGroup = {
  title: string
  subtitle: string
  fields: SystemConfigField[]
}

const systemConfigGroups: SystemConfigGroup[] = [
  {
    title: 'Radar LLM',
    subtitle: '雷达管线使用的 OpenAI 兼容接口',
    fields: [
      { key: 'OPENAI_API_KEY', label: 'API Key', type: 'password' },
      { key: 'OPENAI_BASE_URL', label: 'Base URL', wide: true },
    ],
  },
  {
    title: '数据库连接',
    subtitle: '用于连接社媒数据库；Radar 用户库由 RADAR_DB_URL/Compose 管理',
    fields: [
      { key: 'DB_DIALECT', label: '数据库类型', type: 'select', options: ['mysql', 'postgresql'] },
      { key: 'DB_HOST', label: '主机地址' },
      { key: 'DB_PORT', label: '端口' },
      { key: 'DB_USER', label: '用户名' },
      { key: 'DB_PASSWORD', label: '密码', type: 'password' },
      { key: 'DB_NAME', label: '数据库名称' },
      { key: 'DB_CHARSET', label: '字符集' },
    ],
  },
  {
    title: 'Insight Agent',
    subtitle: '推荐 kimi-k2',
    fields: [
      { key: 'INSIGHT_ENGINE_API_KEY', label: 'API Key', type: 'password' },
      { key: 'INSIGHT_ENGINE_BASE_URL', label: 'Base URL', wide: true },
      { key: 'INSIGHT_ENGINE_MODEL_NAME', label: '模型名称' },
    ],
  },
  {
    title: 'Media Agent',
    subtitle: '推荐 gemini-2.5-pro',
    fields: [
      { key: 'MEDIA_ENGINE_API_KEY', label: 'API Key', type: 'password' },
      { key: 'MEDIA_ENGINE_BASE_URL', label: 'Base URL', wide: true },
      { key: 'MEDIA_ENGINE_MODEL_NAME', label: '模型名称' },
    ],
  },
  {
    title: 'Query Agent',
    subtitle: '推荐 deepseek-chat',
    fields: [
      { key: 'QUERY_ENGINE_API_KEY', label: 'API Key', type: 'password' },
      { key: 'QUERY_ENGINE_BASE_URL', label: 'Base URL', wide: true },
      { key: 'QUERY_ENGINE_MODEL_NAME', label: '模型名称' },
    ],
  },
  {
    title: 'Report Agent',
    subtitle: '推荐 gemini-2.5-pro',
    fields: [
      { key: 'REPORT_ENGINE_API_KEY', label: 'API Key', type: 'password' },
      { key: 'REPORT_ENGINE_BASE_URL', label: 'Base URL', wide: true },
      { key: 'REPORT_ENGINE_MODEL_NAME', label: '模型名称' },
    ],
  },
  {
    title: 'Forum Host',
    subtitle: '推荐 qwen-plus',
    fields: [
      { key: 'FORUM_HOST_API_KEY', label: 'API Key', type: 'password' },
      { key: 'FORUM_HOST_BASE_URL', label: 'Base URL', wide: true },
      { key: 'FORUM_HOST_MODEL_NAME', label: '模型名称' },
    ],
  },
  {
    title: 'Keyword Optimizer',
    subtitle: '推荐 qwen-plus',
    fields: [
      { key: 'KEYWORD_OPTIMIZER_API_KEY', label: 'API Key', type: 'password' },
      { key: 'KEYWORD_OPTIMIZER_BASE_URL', label: 'Base URL', wide: true },
      { key: 'KEYWORD_OPTIMIZER_MODEL_NAME', label: '模型名称' },
    ],
  },
  {
    title: '外部检索工具',
    subtitle: 'Tavily + Anspire/Bocha',
    fields: [
      { key: 'SEARCH_TOOL_TYPE', label: '选择检索工具', type: 'select', options: ['AnspireAPI', 'BochaAPI'] },
      { key: 'TAVILY_API_KEY', label: 'Tavily API Key', type: 'password' },
      { key: 'ANSPIRE_API_KEY', label: 'Anspire API Key', type: 'password', condition: { key: 'SEARCH_TOOL_TYPE', value: 'AnspireAPI' } },
      { key: 'BOCHA_WEB_SEARCH_API_KEY', label: 'Bocha API Key', type: 'password', condition: { key: 'SEARCH_TOOL_TYPE', value: 'BochaAPI' } },
    ],
  },
]

const systemActiveGroups = ref(['Radar LLM', '数据库连接', '外部检索工具'])
const systemConfig = ref<SystemConfig>({})
const systemStatus = ref<SystemStatus | null>(null)
const systemLoading = ref(true)
const systemSaving = ref(false)
const systemStarting = ref(false)
const systemStopping = ref(false)
const systemDirty = ref(false)

function visibleSystemFields(fields: SystemConfigField[]) {
  return fields.filter((field) => !field.condition || systemConfig.value[field.condition.key] === field.condition.value)
}

function systemConfigPayload() {
  const payload: SystemConfig = {}
  for (const group of systemConfigGroups) {
    for (const field of group.fields) {
      const rawValue = systemConfig.value[field.key] ?? ''
      if (/PORT$/i.test(field.key) && rawValue !== '') {
        const numeric = Number(rawValue)
        payload[field.key] = Number.isNaN(numeric) ? rawValue : numeric
      } else {
        payload[field.key] = rawValue
      }
    }
  }
  return payload
}

async function loadSystemStatus() {
  systemStatus.value = await fetchSystemStatus()
}

async function loadSystemConfig() {
  systemLoading.value = true
  try {
    const [configResult] = await Promise.all([fetchSystemConfig(), loadSystemStatus()])
    systemConfig.value = { ...configResult.config }
    systemDirty.value = false
  } finally {
    systemLoading.value = false
  }
}

async function handleSaveSystemConfig(silent = false) {
  systemSaving.value = true
  try {
    const result = await updateSystemConfig(systemConfigPayload())
    systemConfig.value = { ...result.config }
    systemDirty.value = false
    if (!silent) ElMessage.success('系统配置已保存')
    return true
  } finally {
    systemSaving.value = false
  }
}

async function handleStartSystem() {
  systemStarting.value = true
  try {
    if (systemDirty.value) {
      await handleSaveSystemConfig(true)
    }
    const result = await startSystemServices()
    ElMessage.success(result.message || '系统启动成功')
    await loadSystemStatus()
  } finally {
    systemStarting.value = false
  }
}

async function handleShutdownSystem() {
  systemStopping.value = true
  try {
    const result = await shutdownSystemServices()
    ElMessage.success(result.message || '关闭指令已下发')
    await loadSystemStatus()
  } finally {
    systemStopping.value = false
  }
}

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
  loadSystemConfig()
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
  gap: 12px;
  flex-wrap: wrap;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.form-hint {
  margin-left: 12px;
}

.system-alert {
  margin-bottom: 14px;
}

.group-subtitle {
  margin-left: 10px;
  font-weight: 400;
}

.config-note {
  margin: 12px 0 0;
  font-size: 13px;
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
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
