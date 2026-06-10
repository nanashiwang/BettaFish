import { defineStore } from 'pinia'
import { fetchMe, login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/auth'
import { fetchSubscription } from '../api/account'
import type { LoginPayload, RadarUser, RegisterPayload, Subscription } from '../api/types'

interface AuthState {
  user: RadarUser | null
  subscription: Subscription | null
  loaded: boolean
  loadPromise: Promise<void> | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    subscription: null,
    loaded: false,
    loadPromise: null,
  }),

  getters: {
    isLoggedIn: (state) => Boolean(state.user && state.user.risk_confirmed),
    isAdmin: (state) => ['admin', 'super_admin'].includes(state.user?.role ?? ''),
  },

  actions: {
    // 首次导航时拉取会话；缓存 promise 防止并发导航重复请求
    ensureLoaded(): Promise<void> {
      if (this.loaded) return Promise.resolve()
      if (!this.loadPromise) {
        this.loadPromise = fetchMe()
          .then((result) => {
            this.user = result.user
            this.subscription = result.subscription
          })
          .catch(() => {
            // 401 视为未登录，静默处理
            this.user = null
            this.subscription = null
          })
          .finally(() => {
            this.loaded = true
            this.loadPromise = null
          })
      }
      return this.loadPromise
    },

    async login(payload: LoginPayload) {
      const result = await apiLogin(payload)
      this.user = result.user
      this.subscription = result.subscription
      this.loaded = true
      return result
    },

    async register(payload: RegisterPayload) {
      const result = await apiRegister(payload)
      this.user = result.user
      this.subscription = result.subscription
      this.loaded = true
      return result
    },

    async logout() {
      try {
        await apiLogout()
      } finally {
        this.reset()
      }
    },

    async refreshSubscription() {
      const result = await fetchSubscription()
      this.subscription = result.subscription
    },

    reset() {
      this.user = null
      this.subscription = null
      this.loaded = true
    },
  },
})
