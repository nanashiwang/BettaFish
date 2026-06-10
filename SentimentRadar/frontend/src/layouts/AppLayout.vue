<template>
  <div class="app-shell">
    <header class="topbar">
      <router-link to="/" class="brand">
        <div class="logo">雷</div>
        <div>
          <div class="brand-title">A 股舆情雷达</div>
          <div class="brand-sub">极简预判版</div>
        </div>
      </router-link>

      <nav class="nav">
        <router-link to="/" exact-active-class="active">今日预判</router-link>
        <router-link to="/subscription" active-class="active">订阅</router-link>
        <router-link to="/account" active-class="active">账户</router-link>
      </nav>

      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-trigger">
          <el-avatar :size="30" class="avatar">{{ avatarText }}</el-avatar>
          <span class="user-name">{{ auth.user?.name }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <div class="user-meta">
                <div>{{ auth.user?.email }}</div>
                <div class="muted">当前套餐：{{ auth.subscription?.plan_name || '-' }}</div>
              </div>
            </el-dropdown-item>
            <el-dropdown-item v-if="auth.isAdmin" command="admin" divided>管理后台</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </header>

    <main class="page-container">
      <router-view />
    </main>

    <footer class="footer muted">仅供舆情观察 · 不构成投资建议</footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const avatarText = computed(() => auth.user?.name?.charAt(0) ?? '用')

async function handleCommand(command: string) {
  if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'logout') {
    await auth.logout()
    router.replace('/login')
  }
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e4e9ef;
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--radar-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
}

.brand-title {
  font-weight: 600;
  font-size: 15px;
}

.brand-sub {
  font-size: 12px;
  color: #8492a6;
}

.nav {
  display: flex;
  gap: 6px;
  flex: 1;
}

.nav a {
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #475669;
  font-size: 14px;
}

.nav a:hover {
  background: #f0f5f7;
}

.nav a.active {
  background: #e9f6f6;
  color: var(--radar-brand);
  font-weight: 600;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.avatar {
  background: var(--radar-brand);
}

.user-name {
  font-size: 14px;
}

.user-meta {
  line-height: 1.6;
}

.footer {
  text-align: center;
  padding: 18px 0 26px;
}
</style>
