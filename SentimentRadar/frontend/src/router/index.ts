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
          path: 'console',
          name: 'console',
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
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/admin/SettingsView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/admin/UsersView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'plans',
          name: 'plans',
          component: () => import('../views/admin/PlansView.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'audit-logs',
          name: 'audit-logs',
          component: () => import('../views/admin/AuditLogsView.vue'),
          meta: { requiresAdmin: true },
        },
      ],
    },
    { path: '/admin', redirect: '/settings' },
    { path: '/admin/overview', redirect: '/settings' },
    { path: '/admin/settings', redirect: '/settings' },
    { path: '/admin/users', redirect: '/users' },
    { path: '/admin/plans', redirect: '/plans' },
    { path: '/admin/audit-logs', redirect: '/audit-logs' },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

setupGuards(router)

export default router
