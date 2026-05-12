import { ref } from 'vue'
import type { AdminActivityItem } from '@/types/activity'
import { request } from '@/utils/request'

export function useAdminActivities() {
  const items = ref<AdminActivityItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const hasMore = ref(false)
  const actionLoading = ref(false)
  const keyword = ref('')
  const statusFilter = ref('all')

  async function fetchList(resetPage = true) {
    loading.value = true
    error.value = null
    if (resetPage) page.value = 1

    try {
      const params = new URLSearchParams()
      if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
      if (statusFilter.value !== 'all') params.set('status', statusFilter.value)
      params.set('page', String(page.value))
      params.set('page_size', String(pageSize.value))

      const data = await request<{ items: AdminActivityItem[]; total: number }>(`/admin/activities?${params}`)
      if (data.code === 200) {
        const newItems = data.data.items as AdminActivityItem[]
        items.value = resetPage ? newItems : [...items.value, ...newItems]
        total.value = data.data.total
        hasMore.value = page.value * pageSize.value < data.data.total
      } else {
        error.value = data.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误，请稍后重试'
      console.error('Admin activities fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    page.value++
    await fetchList(false)
  }

  async function rejectActivity(id: number, reason: string): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/activities/${id}/reject`, {
        method: 'PUT',
        body: JSON.stringify({ reason }),
      })
      return data.code === 200
    } catch (e) {
      console.error('Reject activity error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function forceDelete(id: number, reason: string): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/activities/${id}`, {
        method: 'DELETE',
        body: JSON.stringify({ reason }),
      })
      return data.code === 200
    } catch (e) {
      console.error('Force delete error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  function retry() {
    fetchList()
  }

  return {
    items, loading, error, total, hasMore, actionLoading,
    keyword, statusFilter,
    fetchList, loadMore, forceDelete, rejectActivity, retry,
  }
}
