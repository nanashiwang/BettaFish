<template>
  <div class="app-shell">
    <header class="topbar">
      <router-link to="/today" class="brand">
        <div class="logo">雷</div>
        <div>
          <div class="brand-title">A 股舆情雷达</div>
          <div class="brand-sub muted">舆情 × 行情 背离信号</div>
        </div>
      </router-link>

      <nav class="nav">
        <router-link to="/today" active-class="active">今日信号</router-link>
        <router-link to="/history" active-class="active">信号历史</router-link>
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

    <footer class="footer faint">仅供舆情观察 · 不构成投资建议</footer>
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
    // 退出后回公开首页
    router.replace('/')
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
  height: 62px;
  background: rgba(10, 15, 26, 0.75);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--glass-border);
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
  border-radius: 11px;
  background: linear-gradient(135deg, var(--brand), #0d9488);
  color: #04211d;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  box-shadow: 0 0 18px rgba(45, 212, 191, 0.3);
}

.brand-title {
  font-weight: 600;
  font-size: 15px;
}

.brand-sub {
  font-size: 11px;
}

.nav {
  display: flex;
  gap: 4px;
  flex: 1;
}

.nav a {
  position: relative;
  padding: 8px 16px;
  border-radius: 10px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  transition: color 0.2s ease, background 0.2s ease;
}

.nav a:hover {
  color: var(--text-primary);
  background: var(--glass-bg);
}

.nav a.active {
  color: var(--brand);
  font-weight: 600;
}

.nav a.active::after {
  content: '';
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 2px;
  height: 2px;
  border-radius: 2px;
  background: var(--brand);
  box-shadow: 0 0 8px var(--brand);
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
}

.avatar {
  background: linear-gradient(135deg, var(--brand), var(--accent));
  color: #04211d;
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
  font-size: 12px;
}
</style>
