import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/HomeView.vue'),
      meta: { public: true },
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true, guestOnly: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true, guestOnly: true },
    },
    {
      path: '/activities',
      name: 'ActivityHall',
      component: () => import('@/views/ActivityHallView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/participations/:id/memento',
      name: 'Memento',
      component: () => import('@/views/MementoView.vue'),
      meta: { requiresAuth: true, role: 'student' },
    },
    {
      path: '/activities/:id',
      name: 'ActivityDetail',
      component: () => import('@/views/ActivityDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/owners/:id',
      name: 'OwnerProfile',
      component: () => import('@/views/OwnerProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'StudentProfile',
      component: () => import('@/views/StudentProfileView.vue'),
      meta: { requiresAuth: true, role: 'student' },
    },
    {
      path: '/owner-profile',
      name: 'OwnerCenter',
      component: () => import('@/views/OwnerCenterView.vue'),
      meta: { requiresAuth: true, role: 'activity_owner' },
    },
    {
      path: '/my-activities',
      name: 'MyActivities',
      component: () => import('@/views/MyActivitiesView.vue'),
      meta: { requiresAuth: true, role: 'activity_owner' },
    },
    {
      path: '/edit-activity',
      name: 'EditActivity',
      component: () => import('@/views/EditActivityView.vue'),
      meta: { requiresAuth: true, role: 'activity_owner' },
    },
    {
      path: '/publish',
      name: 'PublishActivity',
      component: () => import('@/views/PublishActivityView.vue'),
      meta: { requiresAuth: true, role: 'activity_owner' },
    },
    {
      path: '/notifications',
      name: 'Notifications',
      component: () => import('@/views/NotificationsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/credit-analysis',
      name: 'CreditAnalysis',
      component: () => import('@/views/CreditAnalysisView.vue'),
      meta: { requiresAuth: true, role: 'student' },
    },
    {
      path: '/change-password',
      name: 'ChangePassword',
      component: () => import('@/views/ChangePasswordView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'AdminDashboard',
      component: () => import('@/views/admin/AdminDashboardView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/activity-audit',
      name: 'AdminActivityAudit',
      component: () => import('@/views/admin/AdminActivityAuditView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/owner-audit',
      name: 'AdminOwnerAudit',
      component: () => import('@/views/admin/AdminOwnerAuditView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/activities',
      name: 'AdminActivities',
      component: () => import('@/views/admin/AdminActivitiesView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/users',
      name: 'AdminUsers',
      component: () => import('@/views/admin/AdminUsersView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/logs',
      name: 'AdminLogs',
      component: () => import('@/views/admin/AdminLogsView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/announcements',
      name: 'AdminAnnouncements',
      component: () => import('@/views/admin/AdminAnnouncementsView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/admin/banners',
      name: 'AdminBanners',
      component: () => import('@/views/admin/AdminBannersView.vue'),
      meta: { requiresAuth: true, role: 'admin' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // 首次访问时通过 Cookie 恢复登录态
  if (!authStore.initialized) {
    await authStore.initAuth()
  }

  if (to.meta.public && !to.meta.guestOnly) {
    next()
    return
  }

  if (to.meta.guestOnly && authStore.isLoggedIn) {
    next('/')
    return
  }

  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  if (to.meta.role === 'admin' && !authStore.isAdmin) {
    next('/')
    return
  }

  if (to.meta.role === 'student' && !authStore.isStudent) {
    next('/')
    return
  }

  if (to.meta.role === 'activity_owner' && !authStore.isOwner) {
    next('/')
    return
  }

  // 首次登录强制改密守卫
  if (authStore.user?.need_change_password && to.path !== '/change-password') {
    next('/change-password')
    return
  }

  next()
})

export default router
