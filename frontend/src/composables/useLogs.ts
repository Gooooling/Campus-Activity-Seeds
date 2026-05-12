import { ref } from 'vue'
import type { LogItem } from '@/types/activity'
import { request } from '@/utils/request'

export function useLogs() {
  const items = ref<LogItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)
  const hasMore = ref(false)

  const operatorFilter = ref('')
  const actionTypeFilter = ref('all')
  const dateFrom = ref('')
  const dateTo = ref('')

  const actionTypes: { value: string; label: string }[] = [
    { value: 'all', label: '全部操作类型' },
    { value: 'create_user', label: '创建账号' },
    { value: 'reset_password', label: '重置密码' },
    { value: 'approve_activity', label: '通过活动' },
    { value: 'reject_activity', label: '驳回活动' },
    { value: 'delete_activity', label: '删除活动' },
    { value: 'approve_owner', label: '通过主体' },
    { value: 'reject_owner', label: '驳回主体' },
    { value: 'post_announcement', label: '发布公告' },
    { value: 'delete_announcement', label: '删除公告' },
    { value: 'toggle_user_status', label: '禁用/启用用户' },
    { value: 'login', label: '登录' },
    { value: 'create_activity', label: '发布活动' },
    { value: 'update_activity', label: '编辑活动' },
    { value: 'update_profile', label: '修改资料' },
  ]

  async function fetchList(resetPage = true) {
    loading.value = true
    error.value = null
    if (resetPage) page.value = 1

    try {
      const params = new URLSearchParams()
      if (operatorFilter.value.trim()) params.set('operator_name', operatorFilter.value.trim())
      if (actionTypeFilter.value !== 'all') params.set('operation', actionTypeFilter.value)
      if (dateFrom.value) params.set('start_date', dateFrom.value)
      if (dateTo.value) params.set('end_date', dateTo.value)
      params.set('page', String(page.value))
      params.set('page_size', String(pageSize.value))

      const data = await request<{ items: LogItem[]; total: number }>(`/admin/logs?${params}`)
      if (data.code === 200) {
        const newItems = data.data.items as LogItem[]
        items.value = resetPage ? newItems : [...items.value, ...newItems]
        total.value = data.data.total
        hasMore.value = page.value * pageSize.value < data.data.total
      } else {
        error.value = data.message || '请求失败'
      }
    } catch (e) {
      error.value = '服务器错误，请稍后重试'
      console.error('Logs fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  function loadMore() {
    page.value++
    fetchList(false)
  }

  function retry() {
    fetchList()
  }

  function resetFilters() {
    operatorFilter.value = ''
    actionTypeFilter.value = 'all'
    dateFrom.value = ''
    dateTo.value = ''
    fetchList()
  }

  return {
    items, loading, error, total, hasMore, page, pageSize,
    operatorFilter, actionTypeFilter, dateFrom, dateTo, actionTypes,
    fetchList, loadMore, retry, resetFilters,
  }
}
