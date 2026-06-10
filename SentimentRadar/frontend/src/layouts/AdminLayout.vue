<template>
  <el-container class="admin-shell">
    <el-aside width="220px" class="sidebar">
      <div class="side-brand">
        <div class="logo">雷</div>
        <div>
          <div class="side-title">管理后台</div>
          <div class="muted">A 股舆情雷达</div>
        </div>
      </div>
      <el-menu :default-active="$route.path" router class="side-menu">
        <el-menu-item index="/admin/overview">概览</el-menu-item>
        <el-menu-item index="/admin/users">用户管理</el-menu-item>
        <el-menu-item index="/admin/plans">订阅管理</el-menu-item>
        <el-menu-item index="/admin/settings">平台设置</el-menu-item>
        <el-menu-item index="/admin/audit-logs">审计日志</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-topbar">
        <el-button text @click="$router.push('/today')">← 返回用户端</el-button>
        <div class="spacer" />
        <span class="muted">{{ auth.user?.name }}（{{ auth.user?.role_label }}）</span>
        <el-button text type="danger" @click="handleLogout">退出登录</el-button>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  // 退出后回公开首页
  router.replace('/')
}
</script>

<style scoped>
.admin-shell {
  min-height: 100vh;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e4e9ef;
}

.side-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
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
}

.side-title {
  font-weight: 600;
  font-size: 15px;
}

.side-menu {
  border-right: none;
}

.admin-topbar {
  background: #fff;
  border-bottom: 1px solid #e4e9ef;
  display: flex;
  align-items: center;
  gap: 12px;
}

.spacer {
  flex: 1;
}

.admin-main {
  padding: 24px;
}
</style>
