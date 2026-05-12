import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { request } from '@/utils/request'

export type UserRole = 'student' | 'activity_owner' | 'admin' | 'super_admin'

export interface User {
  user_id: number
  account: string
  role: UserRole
  name: string
  avatar_url: string | null
  college_id: number
  college_name: string
  status: string
  need_change_password?: boolean
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const loading = ref(false)
  const initialized = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!user.value)
  const userRole = computed(() => user.value?.role ?? null)
  const isStudent = computed(() => user.value?.role === 'student')
  const isOwner = computed(() => user.value?.role === 'activity_owner')
  const isAdmin = computed(() => user.value?.role === 'admin' || user.value?.role === 'super_admin')
  const isSuperAdmin = computed(() => user.value?.role === 'super_admin')

  // Actions
  function setUser(userData: User) {
    user.value = userData
  }

  async function logout() {
    try {
      // 使用原生 fetch 避免递归：request() 的 401 handler 会再次调用 logout()
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // 即使后端调用失败也继续清除本地状态
    }
    user.value = null
  }

  async function fetchUserInfo() {
    loading.value = true
    try {
      const data = await request<User>('/users/me')
      if (data.code === 200) {
        user.value = data.data
      } else {
        logout()
      }
    } catch {
      logout()
    } finally {
      loading.value = false
    }
  }

  async function initAuth() {
    if (initialized.value) return
    initialized.value = true
    try {
      // 使用原生 fetch 绕过 request() 的 401 拦截器
      // 路由守卫期间 currentRoute 尚未更新，isOnPublicPage() 会误判导致触发 logout
      const res = await fetch('/api/users/me', { credentials: 'include' })
      if (res.ok) {
        const json = await res.json()
        if (json.code === 200) {
          const data = json.data
          // 活动主体的 name 存在 owner_name 字段，统一映射
          if (data.owner_name && !data.name) {
            data.name = data.owner_name
          }
          user.value = data
        }
      }
      // 401 或其他错误：未登录，静默忽略
    } catch {
      // 网络错误等，静默忽略
    }
  }

  return {
    user,
    loading,
    initialized,
    isLoggedIn,
    userRole,
    isStudent,
    isOwner,
    isAdmin,
    isSuperAdmin,
    setUser,
    logout,
    fetchUserInfo,
    initAuth,
  }
})
