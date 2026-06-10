<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-logo">雷</div>
        <div>
          <h1>A 股舆情雷达</h1>
          <p class="muted">仅供舆情观察 · 不构成投资建议</p>
        </div>
      </div>

      <el-form @submit.prevent="handleLogin">
        <el-form-item label="账号">
          <el-input
            v-model="account"
            placeholder="邮箱或用户名"
            size="large"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            show-password
            placeholder="请输入密码"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="riskConfirmed">
            我已阅读并确认：本产品仅提供舆情观察信息，不构成任何投资建议
          </el-checkbox>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="auth-submit"
          native-type="submit"
          :loading="loading"
          :disabled="!canSubmit"
        >
          登录
        </el-button>
      </el-form>

      <p class="muted auth-hint">
        没有账号？
        <router-link :to="{ path: '/register', query: route.query }">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const account = ref('')
const password = ref('')
const riskConfirmed = ref(false)
const loading = ref(false)

const canSubmit = computed(() => account.value.trim() !== '' && password.value !== '' && riskConfirmed.value)

// 兼容旧版 ?next= 参数
function resolveRedirect(): string {
  const redirect = route.query.redirect ?? route.query.next
  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')) {
    // 旧版 next 带 /radar 前缀，SPA 内部路由需去掉
    return redirect.replace(/^\/radar/, '') || '/today'
  }
  return '/today'
}

async function handleLogin() {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    await auth.login({
      account: account.value.trim(),
      password: password.value,
      risk_confirmed: riskConfirmed.value,
    })
    ElMessage.success('登录成功')
    router.replace(resolveRedirect())
  } catch {
    // 错误提示由 http 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>
