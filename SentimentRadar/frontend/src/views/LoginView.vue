<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <div class="logo">雷</div>
        <div>
          <h1>A 股舆情雷达</h1>
          <p class="muted">仅供舆情观察 · 不构成投资建议</p>
        </div>
      </div>

      <el-form @submit.prevent="handleLogin">
        <el-form-item label="账号">
          <el-input
            v-model="account"
            placeholder="邮箱或手机号（演示：user@example.com / ops@radar.cn）"
            size="large"
            clearable
          />
        </el-form-item>
        <el-form-item label="验证码">
          <el-input
            v-model="code"
            placeholder="原型模式：任意验证码"
            size="large"
            maxlength="6"
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
          登录
        </el-button>
      </el-form>

      <p class="muted hint">登录后即可查看今日预判、管理订阅与账户</p>
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

const account = ref('user@example.com')
const code = ref('')
const riskConfirmed = ref(false)
const loading = ref(false)

const canSubmit = computed(() => account.value.trim() !== '' && code.value.trim() !== '' && riskConfirmed.value)

// 兼容旧版 ?next= 参数
function resolveRedirect(): string {
  const redirect = route.query.redirect ?? route.query.next
  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')) {
    // 旧版 next 带 /radar 前缀，SPA 内部路由需去掉
    return redirect.replace(/^\/radar/, '') || '/'
  }
  return '/'
}

async function handleLogin() {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    await auth.login({
      account: account.value.trim(),
      code: code.value.trim(),
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

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f4c5c 0%, #176b87 55%, #2d9596 100%);
  padding: 20px;
}

.login-card {
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
