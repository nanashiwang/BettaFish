import { createRouter, createWebHistory } from 'vue-router'
import { setupGuards } from './guards'

const router = createRouter({
  history: createWebHistory('/radar/'),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { public: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: 'today',
          name: 'today',
          component: () => import('../views/today/TodayView.vue'),
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('../views/history/HistoryView.vue'),
        },
        {
          path: 'subscription',
          name: 'subscription',
          component: () => import('../views/subscription/SubscriptionView.vue'),
        },
        {
          path: 'account',
          name: 'account',
          component: () => import('../views/account/AccountView.vue'),
        },
      ],
    },
    {
      path: '/admin',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
      redirect: '/admin/overview',
      children: [
        {
          path: 'overview',
          name: 'admin-overview',
          component: () => import('../views/admin/OverviewView.vue'),
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('../views/admin/UsersView.vue'),
        },
        {
          path: 'plans',
          name: 'admin-plans',
          component: () => import('../views/admin/PlansView.vue'),
        },
        {
          path: 'settings',
          name: 'admin-settings',
          component: () => import('../views/admin/SettingsView.vue'),
        },
        {
          path: 'audit-logs',
          name: 'admin-audit-logs',
          component: () => import('../views/admin/AuditLogsView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

setupGuards(router)

export default router
