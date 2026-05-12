import { ref } from 'vue'
import type { AdminUserItem } from '@/types/activity'
import { request } from '@/utils/request'

export function useAdminUsers() {
  const items = ref<AdminUserItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const hasMore = ref(false)
  const actionLoading = ref(false)
  const keyword = ref('')
  const roleFilter = ref('all')
  const statusFilter = ref('all')

  async function fetchList(resetPage = true) {
    loading.value = true
    error.value = null
    if (resetPage) page.value = 1

    try {
      const params = new URLSearchParams()
      if (keyword.value.trim()) params.set('search', keyword.value.trim())
      if (roleFilter.value !== 'all') params.set('role', roleFilter.value)
      if (statusFilter.value !== 'all') params.set('status', statusFilter.value)
      params.set('page', String(page.value))
      params.set('page_size', String(pageSize.value))

      const data = await request<{ items: AdminUserItem[]; total: number }>(`/admin/users?${params}`)
      if (data.code === 200) {
        const newItems = data.data.items as AdminUserItem[]
        items.value = resetPage ? newItems : [...items.value, ...newItems]
        total.value = data.data.total
        hasMore.value = page.value * pageSize.value < data.data.total
      } else {
        error.value = data.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误，请稍后重试'
      console.error('Admin users fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  async function loadMore() {
    page.value++
    await fetchList(false)
  }

  async function createUser(role: string, account: string, name: string): Promise<{ ok: boolean; password?: string; msg?: string }> {
    actionLoading.value = true
    try {
      const data = await request<{ initial_password: string }>('/admin/users', {
        method: 'POST',
        body: JSON.stringify({ role, account, name }),
      })
      if (data.code === 200) {
        return { ok: true, password: data.data?.initial_password }
      }
      return { ok: false, msg: data.message || '创建失败' }
    } catch (e) {
      console.error('Create user error:', e)
      return { ok: false, msg: '服务器错误，请稍后重试' }
    } finally {
      actionLoading.value = false
    }
  }

  async function toggleStatus(id: number, enable: boolean): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/users/${id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: enable ? 'active' : 'disabled' }),
      })
      return data.code === 200
    } catch (e) {
      console.error('Toggle status error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function resetPassword(id: number): Promise<{ ok: boolean; password?: string; msg?: string }> {
    actionLoading.value = true
    try {
      const data = await request<{ new_password: string }>(`/admin/users/${id}/reset-password`, {
        method: 'PUT',
      })
      if (data.code === 200) {
        return { ok: true, password: data.data?.new_password }
      }
      return { ok: false, msg: data.message || '重置失败' }
    } catch (e) {
      console.error('Reset password error:', e)
      return { ok: false, msg: '服务器错误，请稍后重试' }
    } finally {
      actionLoading.value = false
    }
  }

  function retry() {
    fetchList()
  }

  return {
    items, loading, error, total, hasMore, actionLoading,
    keyword, roleFilter, statusFilter,
    fetchList, loadMore, createUser, toggleStatus, resetPassword, retry,
  }
}
