import { ref } from 'vue'
import type { AuditOwnerItem, ContactChangeItem } from '@/types/activity'
import { request } from '@/utils/request'

export function useOwnerAudit() {
  const items = ref<AuditOwnerItem[]>([])
  const contactChanges = ref<ContactChangeItem[]>([])
  const contactChangesLoading = ref(false)
  const contactChangesError = ref<string | null>(null)
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

      const data = await request<{ items: AuditOwnerItem[]; total: number }>(`/admin/owners/pending?${params}`)
      if (data.code === 200) {
        const newItems = data.data.items as AuditOwnerItem[]
        items.value = resetPage ? newItems : [...items.value, ...newItems]
        total.value = data.data.total
        hasMore.value = page.value * pageSize.value < data.data.total
      } else {
        error.value = data.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误，请稍后重试'
      console.error('Owner audit fetch error:', e)
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
      const data = await request(`/admin/owners/${id}/approve`, {
        method: 'PUT',
      })
      return data.code === 200
    } catch (e) {
      console.error('Approve error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function reject(id: number, reason: string): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/owners/${id}/reject`, {
        method: 'PUT',
        body: JSON.stringify({ reason }),
      })
      return data.code === 200
    } catch (e) {
      console.error('Reject error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  function retry() {
    fetchList(currentFilter.value)
  }

  // 负责人变更审核
  async function fetchContactChanges(): Promise<boolean> {
    contactChangesLoading.value = true
    contactChangesError.value = null
    try {
      const data = await request<{ items?: ContactChangeItem[] } | ContactChangeItem[]>('/admin/owners/contact-changes')
      if (data.code === 200) {
        contactChanges.value = (data.data as { items?: ContactChangeItem[] })?.items ?? (data.data as ContactChangeItem[]) ?? []
        return true
      }
      contactChangesError.value = data.message || '请求失败'
      return false
    } catch (e) {
      contactChangesError.value = '服务器错误，请稍后重试'
      console.error('Fetch contact changes error:', e)
      return false
    } finally {
      contactChangesLoading.value = false
    }
  }

  async function approveContactChange(id: number): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/owners/${id}/approve-contact-change`, {
        method: 'PUT',
      })
      return data.code === 200
    } catch (e) {
      console.error('Approve contact change error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function rejectContactChange(id: number, reason: string): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/owners/${id}/reject-contact-change`, {
        method: 'PUT',
        body: JSON.stringify({ reason }),
      })
      return data.code === 200
    } catch (e) {
      console.error('Reject contact change error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  return {
    items, loading, error, total, hasMore, actionLoading, currentFilter,
    fetchList, loadMore, approve, reject, retry,
    contactChanges, contactChangesLoading, contactChangesError,
    fetchContactChanges, approveContactChange, rejectContactChange,
  }
}
