import http from './http'
import type {
  ApiResult,
  HistoryResult,
  MyFocusResult,
  PredictionDetail,
  SettingsResult,
  TodayBriefing,
  WatchItem,
} from './types'

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

export function fetchHistory() {
  return http.get<HistoryResult>('/radar/history').then((res) => res.data)
}

export function fetchWatchlist() {
  return http.get<ApiResult & { items: WatchItem[] }>('/radar/watchlist').then((res) => res.data)
}

export function addWatchItem(type: string, name: string) {
  return http
    .post<ApiResult & { items: WatchItem[] }>('/radar/watchlist', { type, name })
    .then((res) => res.data)
}

export function removeWatchItem(itemId: number) {
  return http
    .delete<ApiResult & { items: WatchItem[] }>(`/radar/watchlist/${itemId}`)
    .then((res) => res.data)
}
