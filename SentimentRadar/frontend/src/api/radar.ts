import http from './http'
import type { MyFocusResult, PredictionDetail, RadarSettings, SettingsResult, TodayBriefing } from './types'

export function fetchToday() {
  return http.get<TodayBriefing>('/radar/today').then((res) => res.data)
}

export function fetchPredictionDetail(cardId: string) {
  return http.get<PredictionDetail>(`/radar/predictions/${cardId}`).then((res) => res.data)
}

export function fetchMyFocus() {
  return http.get<MyFocusResult>('/radar/my').then((res) => res.data)
}

export function fetchSettings() {
  return http.get<SettingsResult>('/radar/settings').then((res) => res.data)
}

export function saveSettings(settings: RadarSettings) {
  return http.post<SettingsResult>('/radar/settings', settings).then((res) => res.data)
}
