import type { Router } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

export function setupGuards(router: Router) {
  router.beforeEach(async (to) => {
    const auth = useAuthStore()
    await auth.ensureLoaded()

    // 已登录访问公开页（首页/登录/注册）：跳回 redirect 或今日预判
    if (to.meta.public) {
      if (auth.isLoggedIn) {
        const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/today'
        return redirect
      }
      return true
    }

    // 未登录访问受保护页面：去登录页并记录回跳地址
    if (!auth.isLoggedIn) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }

    // 管理后台需要 admin / super_admin 角色
    if (to.matched.some((record) => record.meta.requiresAdmin) && !auth.isAdmin) {
      ElMessage.warning('无管理员权限')
      return '/today'
    }

    return true
  })
}
