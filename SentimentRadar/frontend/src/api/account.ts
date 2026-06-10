import http from './http'
import type { AccountAggregate, ApiResult, PlansResult, Subscription } from './types'

export function fetchPlans() {
  return http.get<PlansResult>('/account/plans').then((res) => res.data)
}

export function subscribePlan(planId: string) {
  return http
    .post<ApiResult & { subscription: Subscription }>('/account/subscribe', { plan_id: planId })
    .then((res) => res.data)
}

export function fetchSubscription() {
  return http
    .get<ApiResult & { subscription: Subscription }>('/account/subscription')
    .then((res) => res.data)
}

export function fetchAccount() {
  return http.get<AccountAggregate>('/account').then((res) => res.data)
}
