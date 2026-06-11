<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="top-left">
        <router-link to="/today" class="brand">
          <div class="logo">B</div>
          <div class="brand-title">BettaFish 雷达</div>
        </router-link>

        <nav class="nav">
          <router-link to="/today" active-class="active">首页</router-link>
          <router-link to="/history" active-class="active">控制台</router-link>
          <router-link to="/subscription" active-class="active">订阅</router-link>
          <router-link to="/account" active-class="active">账户</router-link>
        </nav>
      </div>

      <div class="top-actions">
        <button class="top-icon" aria-label="通知">♧</button>
        <button class="top-icon" aria-label="主题">☼</button>
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="user-trigger">
            <el-avatar :size="26" class="avatar">{{ avatarText }}</el-avatar>
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
      </div>
    </header>

    <div class="body-shell">
      <aside class="sidebar">
        <div class="side-group">
          <div class="side-label">工作台</div>
          <router-link to="/today" class="side-item" active-class="active">
            <span>▣</span>今日信号
          </router-link>
          <router-link to="/today?tab=my" class="side-item">
            <span>★</span>我的关注
          </router-link>
          <router-link to="/history" class="side-item" active-class="active">
            <span>⌁</span>历史复盘
          </router-link>
        </div>

        <div class="side-group">
          <div class="side-label">控制台</div>
          <router-link to="/history" class="side-item">
            <span>◇</span>数据看板
          </router-link>
          <button v-if="auth.isAdmin" class="side-item button-item" @click="router.push('/admin/settings')">
            <span>⚙</span>管线配置
          </button>
          <button v-if="auth.isAdmin" class="side-item button-item" @click="router.push('/admin/settings')">
            <span>☷</span>系统接入
          </button>
        </div>

        <div v-if="auth.isAdmin" class="side-group">
          <div class="side-label">管理员</div>
          <button class="side-item button-item" @click="router.push('/admin/users')">
            <span>○</span>用户管理
          </button>
          <button class="side-item button-item" @click="router.push('/admin/plans')">
            <span>▤</span>订阅管理
          </button>
          <button class="side-item button-item" @click="router.push('/admin/audit-logs')">
            <span>✦</span>审计日志
          </button>
        </div>

        <div class="system-mini">
          <div class="system-title">系统状态</div>
          <div class="system-row"><span>AI 服务</span><b>正常</b></div>
          <div class="system-row"><span>行情服务</span><b>正常</b></div>
          <div class="system-row"><span>数据库</span><b>正常</b></div>
          <div class="system-row faint"><span>更新时间</span><span>16:35:28</span></div>
        </div>
      </aside>

      <main class="page-container">
        <router-view />
      </main>
    </div>
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
}

.topbar {
  height: 56px;
  background: rgba(10, 15, 26, 0.92);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 26px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}

.logo {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(145deg, var(--brand), var(--brand-secondary));
  color: var(--bg-page);
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  box-shadow: 0 0 22px rgba(59, 164, 247, 0.34);
}

.brand-title {
  font-weight: 800;
  font-size: 16px;
  letter-spacing: 0.2px;
}

.nav {
  display: flex;
  height: 56px;
}

.nav a {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 18px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 650;
  transition: color 0.2s ease, background 0.2s ease;
}

.nav a:hover {
  color: var(--text-primary);
  background: rgba(59, 164, 247, 0.08);
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
  bottom: 0;
  height: 2px;
  border-radius: 2px;
  background: var(--brand);
  box-shadow: 0 0 8px var(--brand);
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.top-icon {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-panel);
  color: var(--text-secondary);
  cursor: pointer;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
  padding: 5px 10px 5px 6px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-panel);
}

.avatar {
  background: linear-gradient(135deg, var(--brand), var(--accent));
  color: var(--text-primary);
}

.user-name {
  font-size: 14px;
}

.user-meta {
  line-height: 1.6;
}

.body-shell {
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  min-height: calc(100vh - 56px);
}

.sidebar {
  position: sticky;
  top: 56px;
  height: calc(100vh - 56px);
  padding: 22px 10px 14px;
  border-right: 1px solid var(--border);
  background: rgba(10, 15, 26, 0.9);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.side-label {
  margin: 0 8px 8px;
  color: var(--text-faint);
  font-size: 12px;
}

.side-item {
  width: 100%;
  height: 38px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 700;
}

.side-item:hover,
.side-item.active {
  color: var(--brand);
  border-color: rgba(59, 164, 247, 0.45);
  background: rgba(59, 164, 247, 0.12);
  box-shadow: inset 3px 0 0 var(--brand);
}

.button-item {
  cursor: pointer;
  font-family: inherit;
  background: transparent;
}

.system-mini {
  margin-top: auto;
  padding: 14px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-panel);
}

.system-title {
  margin-bottom: 9px;
  font-size: 13px;
  font-weight: 800;
}

.system-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 12px;
  color: var(--text-muted);
}

.system-row b {
  color: var(--down);
}

@media (max-width: 960px) {
  .body-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    display: none;
  }

  .nav {
    display: none;
  }

  .brand-title {
    font-size: 14px;
  }

  .user-name {
    display: none;
  }
}
</style>
