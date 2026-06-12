<template>
  <div class="settings-page">
    <div class="module-tabs" role="tablist" aria-label="平台设置模块">
      <button
        v-for="tab in moduleTabs"
        :key="tab.key"
        type="button"
        :class="{ active: activeModule === tab.key }"
        :aria-selected="activeModule === tab.key"
        @click="activeModule = tab.key"
      >
        <strong>{{ tab.title }}</strong>
        <span>{{ tab.desc }}</span>
      </button>
    </div>
    <!-- 系统接入配置：从旧首页配置弹窗迁入 Radar 后台 -->
    <el-card v-show="activeModule === 'system'" shadow="never" class="panel">
      <template #header>
        <div class="panel-head">
          <div>
            <span>系统接入配置</span>
            <span class="muted form-hint">统一管理系统接入、Radar LLM 与雷达管线</span>
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
          title="系统接入与雷达管线在本页完成配置和测试，不再放到用户端展示。"
        />
        <div class="system-health">
          <div v-for="item in systemHealthRows" :key="item.key" class="health-row">
            <i class="health-icon" :class="item.tone">{{ item.icon }}</i>
            <div>
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </div>
            <el-tag :type="item.tagType" size="small">{{ item.status }}</el-tag>
            <small>{{ item.action }}</small>
          </div>
        </div>
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
                  <el-switch
                    v-else-if="field.type === 'switch'"
                    v-model="systemConfig[field.key]"
                    @change="systemDirty = true"
                  />
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
        <div class="test-row">
          <el-input v-model="testEmailTo" placeholder="测试收件邮箱" style="max-width: 280px" />
          <el-button :loading="emailTesting" @click="handleSendTestEmail">发送测试邮件</el-button>
        </div>
      </template>
    </el-card>

    <!-- 雷达管线：真实信号产线的配置与运行管理 -->
    <el-card v-show="activeModule === 'pipeline'" shadow="never" class="panel">
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

    <div v-show="platformModuleKeys.includes(activeModule)" class="platform-module">
      <div v-if="loading" v-loading="true" class="loading-block" />
      <template v-else-if="settings">
        <el-row v-show="activeModule === 'rules'" :gutter="16">
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
          </el-col>

          <el-col :xs="24" :md="12">
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
        </el-row>

        <el-row v-show="activeModule === 'risk'" :gutter="16">
          <el-col :xs="24" :md="12">
            <el-card shadow="never" class="panel">
              <template #header>风险规则开关</template>
              <div v-for="(enabled, key) in settings.risk_rules" :key="key" class="rule-row">
                <span>{{ riskRuleLabels[key] ?? key }}</span>
                <el-switch v-model="settings.risk_rules[key]" />
              </div>
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
          </el-col>
        </el-row>

        <el-row v-show="activeModule === 'notify'" :gutter="16">
          <el-col :xs="24" :md="12">
            <el-card shadow="never" class="panel">
              <template #header>推送时间</template>
              <div v-for="(push, key) in settings.push" :key="key" class="rule-row">
                <span>{{ pushLabels[key] ?? key }}（{{ push.time }}）</span>
                <el-switch v-model="settings.push[key].enabled" />
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-card shadow="never" class="panel">
              <template #header>场景窗口（只读）</template>
              <div v-for="(text, key) in settings.scenario_windows" :key="key" class="kv">
                <span class="muted">{{ key }}</span>
                <span>{{ text }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <div class="module-actions">
          <span class="muted">当前模块修改后，统一点击右侧保存。</span>
          <el-button type="primary" size="large" :loading="saving" @click="handleSave">
            保存平台设置
          </el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fetchAdminSettings,
  fetchRadarConfig,
  fetchRadarRuns,
  fetchSystemConfig,
  fetchSystemStatus,
  runRadarPipeline,
  sendTestEmail,
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
const activeModule = ref('system')
const moduleTabs = [
  { key: 'system', title: '系统接入', desc: 'AI / 数据库 / 邮件 / 支付' },
  { key: 'pipeline', title: '雷达管线', desc: '调度 / tushare / 运行记录' },
  { key: 'rules', title: '今日规则', desc: '权重 / 模型成本' },
  { key: 'risk', title: '风控合规', desc: '风险开关 / 禁止词' },
  { key: 'notify', title: '通知场景', desc: '推送时间 / 场景窗口' },
]
const platformModuleKeys = ['rules', 'risk', 'notify']

// ---------- 旧首页系统配置 ----------
type SystemConfigField = {
  key: string
  label: string
  type?: 'text' | 'password' | 'select' | 'switch'
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
  {
    title: '邮件推送',
    subtitle: 'SMTP 发信配置，用于通知、订阅成功提醒和测试邮件',
    fields: [
      { key: 'SMTP_ENABLED', label: '启用 SMTP', type: 'switch' },
      { key: 'SMTP_HOST', label: 'SMTP 主机' },
      { key: 'SMTP_PORT', label: 'SMTP 端口' },
      { key: 'SMTP_USER', label: 'SMTP 用户名' },
      { key: 'SMTP_PASSWORD', label: 'SMTP 密码/授权码', type: 'password' },
      { key: 'SMTP_FROM_EMAIL', label: '发件邮箱' },
      { key: 'SMTP_FROM_NAME', label: '发件人名称' },
      { key: 'SMTP_USE_SSL', label: 'SSL', type: 'switch' },
      { key: 'SMTP_USE_TLS', label: 'STARTTLS', type: 'switch' },
    ],
  },
  {
    title: '在线购买',
    subtitle: '易支付 epay 网关配置，启用后订阅按钮会创建支付订单',
    fields: [
      { key: 'EPAY_ENABLED', label: '启用 epay', type: 'switch' },
      { key: 'EPAY_API_URL', label: '网关地址', wide: true },
      { key: 'EPAY_PID', label: '商户 PID' },
      { key: 'EPAY_KEY', label: '商户密钥', type: 'password' },
      { key: 'EPAY_TYPE', label: '默认支付方式', type: 'select', options: ['alipay', 'wxpay', 'qqpay'] },
      { key: 'EPAY_RETURN_URL', label: '同步跳转 URL', wide: true },
      { key: 'EPAY_NOTIFY_URL', label: '异步通知 URL', wide: true },
      { key: 'EPAY_NAME_PREFIX', label: '订单标题前缀' },
    ],
  },
]

const BOOL_CONFIG_KEYS = new Set(['SMTP_ENABLED', 'SMTP_USE_SSL', 'SMTP_USE_TLS', 'EPAY_ENABLED'])
const systemActiveGroups = ref(['Radar LLM', '数据库连接', '外部检索工具', '邮件推送', '在线购买'])
const systemConfig = ref<SystemConfig>({})
const systemStatus = ref<SystemStatus | null>(null)
const systemLoading = ref(true)
const systemSaving = ref(false)
const systemStarting = ref(false)
const systemStopping = ref(false)
const systemDirty = ref(false)
const emailTesting = ref(false)
const testEmailTo = ref('')

const systemHealthRows = computed(() => {
  const hasRadarBase = Boolean(systemConfig.value.OPENAI_BASE_URL)
  const hasRadarKey = Boolean(systemConfig.value.OPENAI_API_KEY)
  const hasTushare = Boolean(pipeline.value?.tushare_token)
  const dbReady = Boolean(pipeline.value)
  const smtpReady = Boolean(systemConfig.value.SMTP_ENABLED && systemConfig.value.SMTP_HOST && systemConfig.value.SMTP_USER)
  const epayReady = Boolean(systemConfig.value.EPAY_ENABLED && systemConfig.value.EPAY_API_URL && systemConfig.value.EPAY_PID)
  return [
    {
      key: 'ai',
      icon: 'AI',
      tone: 'ai',
      title: 'Radar LLM',
      desc: hasRadarBase ? 'OPENAI_BASE_URL 已配置' : 'OPENAI_BASE_URL 未配置',
      status: hasRadarBase && hasRadarKey ? '已配置' : '待配置',
      tagType: hasRadarBase && hasRadarKey ? 'success' : 'warning',
      action: '保存后可启动系统/运行管线测试',
    },
    {
      key: 'tushare',
      icon: 'TS',
      tone: 'ts',
      title: 'Tushare',
      desc: '行情主源；同花顺不足时自动降级申万行业，Akshare 兜底',
      status: hasTushare ? '已配置' : '待配置',
      tagType: hasTushare ? 'success' : 'warning',
      action: '点击「立即运行」验证权限',
    },
    {
      key: 'db',
      icon: 'DB',
      tone: 'db',
      title: 'PostgreSQL',
      desc: 'Radar 用户 / 管线结果库',
      status: dbReady ? '正常' : '待检查',
      tagType: dbReady ? 'success' : 'info',
      action: '后台接口连通即代表可写',
    },
    {
      key: 'smtp',
      icon: 'EM',
      tone: 'mail',
      title: '邮件推送',
      desc: systemConfig.value.SMTP_ENABLED ? 'SMTP 已启用' : 'SMTP 未启用',
      status: smtpReady ? '已配置' : '待配置',
      tagType: smtpReady ? 'success' : 'info',
      action: '保存后可发送测试邮件',
    },
    {
      key: 'epay',
      icon: '¥',
      tone: 'pay',
      title: '在线购买',
      desc: systemConfig.value.EPAY_ENABLED ? 'epay 已启用' : 'epay 未启用',
      status: epayReady ? '已配置' : '待配置',
      tagType: epayReady ? 'success' : 'info',
      action: '订阅页会跳转到支付网关',
    },
  ]
})

function configBool(value: unknown) {
  if (typeof value === 'boolean') return value
  return ['true', '1', 'yes', 'on'].includes(String(value ?? '').toLowerCase())
}

function normalizeSystemConfig(config: SystemConfig) {
  const normalized: SystemConfig = { ...config }
  for (const key of BOOL_CONFIG_KEYS) {
    normalized[key] = configBool(normalized[key])
  }
  return normalized
}

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
    systemConfig.value = normalizeSystemConfig(configResult.config)
    systemDirty.value = false
  } finally {
    systemLoading.value = false
  }
}

async function handleSendTestEmail() {
  emailTesting.value = true
  try {
    if (systemDirty.value) {
      await handleSaveSystemConfig(true)
    }
    const result = await sendTestEmail(testEmailTo.value)
    ElMessage.success(result.message || '测试邮件已发送')
  } finally {
    emailTesting.value = false
  }
}

async function handleSaveSystemConfig(silent = false) {
  systemSaving.value = true
  try {
    const result = await updateSystemConfig(systemConfigPayload())
    systemConfig.value = normalizeSystemConfig(result.config)
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
.settings-page {
  display: grid;
  gap: 16px;
}

.module-tabs {
  position: sticky;
  top: 72px;
  z-index: 6;
  display: grid;
  grid-template-columns: repeat(5, minmax(128px, 1fr));
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background:
    radial-gradient(circle at 8% 0%, rgba(59, 164, 247, 0.12), transparent 32%),
    rgba(10, 15, 26, 0.9);
  backdrop-filter: blur(18px);
}

.module-tabs button {
  min-height: 64px;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.035);
  color: rgba(219, 234, 254, 0.82);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.module-tabs button:hover,
.module-tabs button.active {
  color: #f8fafc;
  border-color: rgba(59, 164, 247, 0.48);
  background: linear-gradient(135deg, rgba(59, 164, 247, 0.18), rgba(45, 212, 191, 0.08));
}

.module-tabs strong,
.module-tabs span {
  display: block;
}

.module-tabs strong {
  font-size: 14px;
}

.module-tabs span {
  margin-top: 4px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.35;
}

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

.system-health {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.health-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
}

.health-row strong,
.health-row span,
.health-row small {
  display: block;
}

.health-row strong {
  font-size: 14px;
}

.health-row span,
.health-row small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.45;
}

.health-row small {
  grid-column: 2 / 4;
}

.health-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  color: var(--text-primary);
  font-style: normal;
  font-weight: 900;
}

.health-icon.ai {
  background: var(--brand);
}

.health-icon.ts {
  background: var(--down);
}

.health-icon.db {
  background: var(--warning);
  color: #111827;
}

.health-icon.mail {
  background: var(--accent);
  color: #04211d;
}

.health-icon.pay {
  background: #fbbf24;
  color: #111827;
}

.group-subtitle {
  margin-left: 10px;
  font-weight: 400;
}

.config-note {
  margin: 12px 0 0;
  font-size: 13px;
}

.test-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
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

.module-actions {
  position: sticky;
  bottom: 16px;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: rgba(10, 15, 26, 0.88);
  color: #f8fafc;
  backdrop-filter: blur(16px);
}

@media (max-width: 960px) {
  .module-tabs {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .system-health {
    grid-template-columns: 1fr;
  }

  .module-actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
