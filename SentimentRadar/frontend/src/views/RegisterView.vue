<template>
  <div class="register-page">
    <div class="register-card">
      <div class="brand">
        <div class="logo">雷</div>
        <div>
          <h1>注册 A 股舆情雷达</h1>
          <p class="muted">仅供舆情观察 · 不构成投资建议</p>
        </div>
      </div>

      <el-form @submit.prevent="handleRegister">
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
          class="submit-btn"
          native-type="submit"
          :loading="loading"
          :disabled="!canSubmit"
        >
          注册并进入
        </el-button>
      </el-form>

      <p class="muted hint">
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

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const riskConfirmed = ref(false)
const loading = ref(false)

const canSubmit = computed(
  () =>
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

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f4c5c 0%, #176b87 55%, #2d9596 100%);
  padding: 20px;
}

.register-card {
  width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 36px 32px 28px;
  box-shadow: 0 24px 64px rgba(8, 48, 62, 0.35);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.logo {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--radar-brand);
  color: #fff;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand h1 {
  margin: 0;
  font-size: 20px;
}

.submit-btn {
  width: 100%;
}

.hint {
  text-align: center;
  margin-top: 18px;
}
</style>
