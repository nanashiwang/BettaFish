import http from './http'
import type { AccountAggregate, ApiResult, PlansResult, SubscribeResult, Subscription } from './types'

export function fetchPlans() {
  return http.get<PlansResult>('/account/plans').then((res) => res.data)
}

export function subscribePlan(planId: string, period: 'month' | 'year', payType: string) {
  return http
    .post<SubscribeResult>('/account/subscribe', { plan_id: planId, period, pay_type: payType })
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
