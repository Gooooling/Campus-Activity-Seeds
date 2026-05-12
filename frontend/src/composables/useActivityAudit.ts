import { ref } from 'vue'
import type { AuditActivityItem } from '@/types/activity'
import { request } from '@/utils/request'

export function useActivityAudit() {
  const items = ref<AuditActivityItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const hasMore = ref(false)
  const actionLoading = ref(false)
  const currentFilter = ref('all')

  async function fetchList(status: string = 'all', resetPage = true) {
    loading.value = true
    error.value = null
    currentFilter.value = status
    if (resetPage) page.value = 1

    try {
      const params = new URLSearchParams()
      if (status !== 'all') params.set('status', status)
      params.set('page', String(page.value))
      params.set('page_size', String(pageSize.value))

      const data = await request<{ items: AuditActivityItem[]; total: number }>(`/admin/activities/pending?${params}`)
      if (data.code === 200) {
        const newItems = data.data.items as AuditActivityItem[]
        items.value = resetPage ? newItems : [...items.value, ...newItems]
        total.value = data.data.total
        hasMore.value = page.value * pageSize.value < data.data.total
      } else {
        error.value = data.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误请稍后重试'
      console.error('Activity audit fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    page.value++
    await fetchList(currentFilter.value, false)
  }

  async function approve(id: number): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/activities/${id}/approve`, {
        method: 'PUT',
      })
      return data.code === 200
    } catch {
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function reject(id: number, reason: string): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/activities/${id}/reject`, {
        method: 'PUT',
        body: JSON.stringify({ reason }),
      })
      return data.code === 200
    } catch {
      return false
    } finally {
      actionLoading.value = false
    }
  }

  function retry() {
    fetchList(currentFilter.value)
  }

  return {
    items, loading, error, total, hasMore, actionLoading, currentFilter,
    fetchList, loadMore, approve, reject, retry,
  }
}
