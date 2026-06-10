import http from './http'
import type {
  AdminOverview,
  AdminSettings,
  AdminUser,
  AdminUserDetail,
  AdminUsersResult,
  ApiResult,
  AuditLog,
  Plan,
  RadarPipelineConfig,
  RadarPipelineRun,
} from './types'

export function fetchOverview() {
  return http.get<AdminOverview>('/admin/overview').then((res) => res.data)
}

export function fetchUsers() {
  return http.get<AdminUsersResult>('/admin/users').then((res) => res.data)
}

export function fetchUserDetail(userId: string) {
  return http.get<AdminUserDetail>(`/admin/users/${userId}`).then((res) => res.data)
}

export function updateUser(userId: string, payload: Partial<AdminUser>) {
  return http
    .patch<ApiResult & { user: AdminUser }>(`/admin/users/${userId}`, payload)
    .then((res) => res.data)
}

export function fetchAdminPlans() {
  return http.get<ApiResult & { plans: Plan[] }>('/admin/plans').then((res) => res.data)
}

export function updatePlan(planId: string, payload: Partial<Plan>) {
  return http
    .patch<ApiResult & { plan: Plan }>(`/admin/plans/${planId}`, payload)
    .then((res) => res.data)
}

export function fetchAdminSettings() {
  return http.get<ApiResult & { settings: AdminSettings }>('/admin/settings').then((res) => res.data)
}

export function updateAdminSettings(payload: Partial<AdminSettings>) {
  return http
    .patch<ApiResult & { settings: AdminSettings }>('/admin/settings', payload)
    .then((res) => res.data)
}

export function fetchAuditLogs() {
  return http.get<ApiResult & { logs: AuditLog[] }>('/admin/audit-logs').then((res) => res.data)
}

export function fetchRadarConfig() {
  return http
    .get<ApiResult & { config: RadarPipelineConfig }>('/admin/radar/config')
    .then((res) => res.data)
}

export function updateRadarConfig(payload: Partial<RadarPipelineConfig>) {
  return http
    .patch<ApiResult & { config: RadarPipelineConfig }>('/admin/radar/config', payload)
    .then((res) => res.data)
}

export function runRadarPipeline() {
  return http.post<ApiResult>('/admin/radar/run').then((res) => res.data)
}

export function fetchRadarRuns() {
  return http
    .get<ApiResult & { runs: RadarPipelineRun[] }>('/admin/radar/runs')
    .then((res) => res.data)
}
