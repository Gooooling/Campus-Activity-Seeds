import { ref } from 'vue'
import type { DashboardData } from '@/types/activity'
import { request } from '@/utils/request'

export function useDashboard() {
  const data = ref<DashboardData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchDashboard() {
    loading.value = true
    error.value = null
    try {
      const res = await request<DashboardData>('/admin/dashboard')
      if (res.code === 200) {
        data.value = res.data
      } else {
        error.value = res.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误请稍后重试'
      console.error('Dashboard fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  function retry() {
    fetchDashboard()
  }

  return { data, loading, error, fetchDashboard, retry }
}
