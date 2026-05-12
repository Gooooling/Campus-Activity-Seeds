import { ref } from 'vue'
import type { AnnouncementItem } from '@/types/activity'
import { request } from '@/utils/request'

export function useAnnouncements() {
  const items = ref<AnnouncementItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const actionLoading = ref(false)

  async function fetchList() {
    loading.value = true
    error.value = null
    try {
      const data = await request<{ items: AnnouncementItem[] } | AnnouncementItem[]>('/admin/announcements')
      if (data.code === 200) {
        items.value = ((data.data as { items?: AnnouncementItem[] })?.items || data.data) as AnnouncementItem[]
      } else {
        error.value = data.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误，请稍后重试'
      console.error('Announcements fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  async function create(content: string): Promise<boolean> {
    if (!content.trim()) return false
    actionLoading.value = true
    try {
      const data = await request('/admin/announcements', {
        method: 'POST',
        body: JSON.stringify({ content: content.trim() }),
      })
      if (data.code === 200) {
        await fetchList()
        return true
      }
      return false
    } catch (e) {
      console.error('Create announcement error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function remove(id: number): Promise<boolean> {
    actionLoading.value = true
    try {
      const data = await request(`/admin/announcements/${id}`, {
        method: 'DELETE',
      })
      if (data.code === 200) {
        items.value = items.value.filter(a => a.id !== id)
        return true
      }
      return false
    } catch (e) {
      console.error('Remove announcement error:', e)
      return false
    } finally {
      actionLoading.value = false
    }
  }

  function retry() {
    fetchList()
  }

  return {
    items, loading, error, actionLoading,
    fetchList, create, remove, retry,
  }
}
