<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-logo">雷</div>
        <div>
          <h1>注册 A 股舆情雷达</h1>
          <p class="muted">仅供舆情观察 · 不构成投资建议</p>
        </div>
      </div>

      <el-form @submit.prevent="handleRegister">
        <el-form-item label="用户名">
          <el-input
            v-model="username"
            placeholder="2-20 个字符，登录时可用"
            size="large"
            maxlength="20"
            clearable
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="email" placeholder="用于登录的邮箱地址" size="large" clearable />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            show-password
            placeholder="至少 6 位"
            size="large"
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="confirmPassword"
            type="password"
            show-password
            placeholder="再次输入密码"
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
          注册并进入
        </el-button>
      </el-form>

      <p class="muted auth-hint">
        已有账号？
        <router-link :to="{ path: '/login', query: route.query }">去登录</router-link>
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

const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const riskConfirmed = ref(false)
const loading = ref(false)

const canSubmit = computed(
  () =>
    username.value.trim().length >= 2 &&
    !username.value.includes('@') &&
    email.value.includes('@') &&
    password.value.length >= 6 &&
    password.value === confirmPassword.value &&
    riskConfirmed.value,
)

function resolveRedirect(): string {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')) {
    return redirect
  }
  return '/today'
}

async function handleRegister() {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    await auth.register({
      email: email.value.trim(),
      username: username.value.trim(),
      password: password.value,
      risk_confirmed: riskConfirmed.value,
    })
    ElMessage.success('注册成功，已自动登录')
    router.replace(resolveRedirect())
  } catch {
    // 错误提示由 http 拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>
