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
          <router-link to="/history" active-class="active">复盘</router-link>
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
              <el-dropdown-item v-if="auth.isAdmin" command="settings" divided>平台设置</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <div class="body-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-head">
          <span class="rail-title">雷达导航</span>
          <button class="collapse-toggle" :aria-label="sidebarCollapsed ? '展开侧栏' : '收起侧栏'" @click="sidebarCollapsed = !sidebarCollapsed">
            {{ sidebarCollapsed ? '›' : '‹' }}
          </button>
        </div>

        <div class="side-group">
          <div class="side-label">工作台</div>
          <router-link to="/today" class="side-item" active-class="active">
            <span class="side-icon">▣</span><span class="side-text">今日信号</span>
          </router-link>
          <router-link to="/today?tab=my" class="side-item">
            <span class="side-icon">★</span><span class="side-text">我的关注</span>
          </router-link>
          <router-link to="/history" class="side-item" active-class="active">
            <span class="side-icon">⌁</span><span class="side-text">历史复盘</span>
          </router-link>
        </div>

        <div v-if="auth.isAdmin" class="side-group">
          <div class="side-label">管理员</div>
          <router-link to="/settings" class="side-item" active-class="active">
            <span class="side-icon">⚙</span><span class="side-text">平台设置</span>
          </router-link>
          <router-link to="/users" class="side-item" active-class="active">
            <span class="side-icon">○</span><span class="side-text">用户管理</span>
          </router-link>
          <router-link to="/plans" class="side-item" active-class="active">
            <span class="side-icon">▤</span><span class="side-text">订阅管理</span>
          </router-link>
          <router-link to="/audit-logs" class="side-item" active-class="active">
            <span class="side-icon">✦</span><span class="side-text">审计日志</span>
          </router-link>
        </div>
      </aside>

      <main class="page-container">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const sidebarCollapsed = ref(false)

const avatarText = computed(() => auth.user?.name?.charAt(0) ?? '用')

async function handleCommand(command: string) {
  if (command === 'settings') {
    router.push('/settings')
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
  grid-template-columns: 176px minmax(0, 1fr);
  min-height: calc(100vh - 56px);
  transition: grid-template-columns 0.22s ease;
}

.body-shell.sidebar-collapsed {
  grid-template-columns: 70px minmax(0, 1fr);
}

.sidebar {
  position: sticky;
  top: 56px;
  height: calc(100vh - 56px);
  padding: 14px 10px;
  border-right: 1px solid var(--border);
  background: rgba(10, 15, 26, 0.9);
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-x: hidden;
  overflow-y: auto;
}

.sidebar-head {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 4px 0 8px;
}

.rail-title {
  color: var(--text-faint);
  font-size: 12px;
  font-weight: 800;
}

.collapse-toggle {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-panel);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.collapse-toggle:hover {
  color: var(--brand);
  border-color: rgba(59, 164, 247, 0.45);
  background: var(--bg-hover);
}

.side-group {
  display: grid;
  gap: 6px;
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
  white-space: nowrap;
  transition: color 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.side-icon {
  width: 18px;
  flex: 0 0 18px;
  text-align: center;
  color: inherit;
}

.side-text {
  overflow: hidden;
  text-overflow: ellipsis;
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

.sidebar.collapsed .rail-title,
.sidebar.collapsed .side-label,
.sidebar.collapsed .side-text,
.sidebar.collapsed .system-mini {
  display: none;
}

.sidebar.collapsed .sidebar-head {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .side-item {
  justify-content: center;
  padding: 0;
}

@media (max-width: 960px) {
  .body-shell {
    grid-template-columns: 1fr;
  }

  .body-shell.sidebar-collapsed {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: sticky;
    top: 56px;
    z-index: 8;
    height: auto;
    min-width: 0;
    flex-direction: row;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-right: 0;
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: thin;
  }

  .sidebar-head,
  .side-group {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
  }

  .rail-title,
  .side-label,
  .system-mini {
    display: none;
  }

  .side-item,
  .sidebar.collapsed .side-item {
    width: auto;
    min-width: max-content;
    justify-content: flex-start;
    padding: 0 12px;
  }

  .sidebar.collapsed .side-text {
    display: inline;
  }

  .sidebar.collapsed .sidebar-head {
    justify-content: flex-start;
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
