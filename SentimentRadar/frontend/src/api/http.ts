import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

// 同源部署 + dev proxy，session cookie 自动往返，无需 CORS
const http = axios.create({
  baseURL: '/api',
  withCredentials: true,
  timeout: 15000,
})

// /auth/me 的 401 表示"未登录"，由 auth store 静默处理，不弹错误也不跳转
const SILENT_401_PATHS = ['/auth/me']

http.interceptors.response.use(
  (response) => {
    const data = response.data
    // 后端约定：HTTP 2xx 但 success=false 也是业务失败
    if (data && data.success === false) {
      const message = data.message || '请求失败'
      ElMessage.error(message)
      return Promise.reject(new Error(message))
    }
    return response
  },
  async (error: AxiosError<{ message?: string }>) => {
    const status = error.response?.status
    const requestPath = error.config?.url || ''
    const silent = SILENT_401_PATHS.some((path) => requestPath.includes(path))

    if (status === 401 && !silent) {
      // 会话过期：清空登录态并跳转登录页，登录后回跳当前页
      const { useAuthStore } = await import('../stores/auth')
      const { default: router } = await import('../router')
      useAuthStore().reset()
      const current = router.currentRoute.value
      if (current.path !== '/login') {
        ElMessage.warning('登录已过期，请重新登录')
        router.replace({ path: '/login', query: { redirect: current.fullPath } })
      }
    } else if (status === 403) {
      ElMessage.error(error.response?.data?.message || '无访问权限')
      const { default: router } = await import('../router')
      if (['/settings', '/users', '/plans', '/audit-logs'].includes(router.currentRoute.value.path)) {
        router.replace('/today')
      }
    } else if (!silent) {
      ElMessage.error(error.response?.data?.message || '网络请求失败，请稍后重试')
    }
    return Promise.reject(error)
  },
)

export default http
