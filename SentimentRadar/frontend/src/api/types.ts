// 后端数据契约类型定义，形状来源：SentimentRadar/platform_service.py 与 service.py

// ---------- 通用 ----------
export interface ApiResult {
  success: boolean
  message?: string
}

// ---------- 认证 ----------
export interface RadarUser {
  id: string
  name: string
  username?: string
  email: string
  phone: string
  role: 'subscriber' | 'admin' | 'super_admin' | string
  role_label: string
  plan_id: string
  risk_confirmed: boolean
  risk_version: string
  last_login_at: string
}

export interface Subscription {
  plan_id: string
  plan_name: string
  status: string
  renewal?: boolean
  started_at?: string
  expires_at: string
}

export interface LoginPayload {
  account: string
  password: string
  risk_confirmed: boolean
}

export interface RegisterPayload {
  email: string
  username: string
  password: string
  risk_confirmed: boolean
}

export interface AuthResult extends ApiResult {
  user: RadarUser
  subscription: Subscription
}

// ---------- 今日预判 ----------
export interface PredictionCard {
  id: string
  rank: number
  title: string
  scenario: string
  strength: string
  judgement: string
  reason: string
  risk: string
  next: string
  evidence: string
  tags: string[]
  heat_z?: number | null
  price_z?: number | null
  board_name?: string
  board_trend?: number[]
}

export interface ScatterPoint {
  name: string
  heat_z: number
  price_z: number
  scenario: string | null
}

export interface TodayBriefing extends ApiResult {
  updated_at: string
  product: string
  version: string
  disclaimer: string
  headline: string
  cards: PredictionCard[]
  signals_scatter: ScatterPoint[]
  my_related: {
    summary: string
    highlight: string
    items: { label: string; value: string }[]
  }
  top_risk: {
    title: string
    level: string
    scope: string
    reason: string
  }
  evidence_overview: { name: string; count: number }[]
}

export interface PredictionDetail extends ApiResult {
  id: string
  updated_at: string
  disclaimer: string
  detail: {
    title: string
    scenario: string
    summary: string
    why: string[]
    timeline: { time: string; label: string; text: string }[]
    evidence_chain: { source: string; count: number; credibility: string; note: string }[]
    risk_boundary: string[]
    next_watch: string[]
  }
}

export interface FocusHit {
  name: string
  type: string
  match: string
  scenario: string
  risk: string
  next: string
  card_id?: string | null
}

export interface WatchItem {
  id: number
  type: 'stock' | 'theme' | 'sector' | string
  name: string
}

export interface RadarSettings {
  watchlist: WatchItem[]
  push_templates: { id: string; name: string; enabled: boolean; time: string }[]
}

export interface MyFocusResult extends ApiResult {
  updated_at: string
  disclaimer: string
  hits: FocusHit[]
  watchlist: WatchItem[]
}

export interface SettingsResult extends ApiResult {
  updated_at: string
  settings: RadarSettings
}

// ---------- 信号历史 ----------
export interface HistoryCard {
  id: string
  title: string
  scenario: string
  strength: string
  judgement: string
  boards: { code: string; name: string; type: string }[]
  heat_z: number | null
  price_z: number | null
  return_1d: number | null
  return_3d: number | null
  return_5d: number | null
}

export interface HistoryStats {
  total: number
  evaluated: number
  win_rate_3d: number | null
  avg_return_3d: number | null
  by_scenario: Record<string, { count: number; evaluated: number; wins: number; win_rate: number | null }>
}

export interface HistoryResult extends ApiResult {
  disclaimer: string
  stats: HistoryStats
  days: { date: string; cards: HistoryCard[] }[]
}

// ---------- 订阅与账户 ----------
export interface Plan {
  id: string
  name: string
  price_month: number
  price_year: number
  audience: string
  status: string
  recommended?: boolean
  summary: string
  features: string[]
  limits: {
    today_predictions: number
    evidence_depth: string
    watchlist_limit: number
    push_templates: string[]
    history_days: number
    ai_quota: number
  }
}

export interface PlansResult extends ApiResult {
  plans: Plan[]
  current_plan_id: string
  disclaimer: string
}

export interface UsageItem {
  label: string
  used: number
  limit: number
}

export interface Bill {
  id: string
  plan: string
  amount: number
  status: string
  paid_at: string
}

export interface RiskConfirmation {
  version: string
  confirmed_at: string
  ip: string
  status: string
}

export interface AccountAggregate extends ApiResult {
  user: RadarUser
  subscription: Subscription
  usage: Record<string, UsageItem>
  bills: Bill[]
  risk_confirmations: RiskConfirmation[]
}

// ---------- 管理后台 ----------
export interface AdminStat {
  label: string
  value: string
  trend: string
  tone: 'blue' | 'ok' | 'warn' | 'danger' | string
}

export interface AdminOverview extends ApiResult {
  updated_at: string
  stats: AdminStat[]
  trend: { day: string; active: number }[]
  data_sources: { name: string; status: string; note: string }[]
}

export interface AdminUser {
  id: string
  name: string
  email: string
  phone: string
  role: string
  plan: string
  expires_at: string
  usage: string
  status: string
  last_active: string
  note: string
}

export interface AdminUsersResult extends ApiResult {
  users: AdminUser[]
  total: number
}

export interface AdminUserDetail extends ApiResult {
  user: AdminUser
  subscription: Subscription
  usage: Record<string, UsageItem>
  risk_confirmations: RiskConfirmation[]
  push_logs: { template: string; status: string; sent_at: string }[]
}

export interface AdminSettings {
  today_rules: {
    topic_heat_weight: number
    heat_growth_weight: number
    user_relevance_weight: number
    risk_penalty_enabled: boolean
  }
  scenario_windows: Record<string, string>
  risk_rules: Record<string, boolean>
  compliance: {
    forbidden_words: string[]
    disclaimer: string
  }
  push: Record<string, { enabled: boolean; time: string }>
  model: {
    primary_model: string
    daily_cost_limit: number
    timeout_seconds: number
  }
}

export interface AuditLog {
  time: string
  actor: string
  action: string
  target: string
}

// ---------- 雷达管线 ----------
export interface RadarPipelineConfig {
  enabled: boolean
  run_times: string[]
  llm_model: string
  tushare_token: string
}

export interface RadarPipelineRun {
  id: number
  started_at: string
  finished_at: string | null
  status: 'running' | 'success' | 'failed' | string
  stage: string
  message: string
  stats: Record<string, unknown>
}
