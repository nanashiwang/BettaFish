import http from './http'
import type { ApiResult, AuthResult, LoginPayload } from './types'

export function login(payload: LoginPayload) {
  return http.post<AuthResult>('/auth/login', payload).then((res) => res.data)
}

export function logout() {
  return http.post<ApiResult>('/auth/logout').then((res) => res.data)
}

export function fetchMe() {
  return http.get<AuthResult>('/auth/me').then((res) => res.data)
}
