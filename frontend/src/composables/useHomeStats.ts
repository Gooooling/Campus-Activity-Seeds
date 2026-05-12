import { ref } from 'vue'
import type { ActivityListItem } from '@/types/activity'

export interface HomeStatsBase {
  total_users: number
  total_activities: number
  hot_activities: ActivityListItem[]
}

export interface HomeStatsStudent extends HomeStatsBase {
  my_participation_count: number
  upcoming_activities: { id: number; title: string; start_time: string }[]
  expiring_favorites: ActivityListItem[]
  credit_advice_preview: string
}

export interface PendingIssue {
  activity_id: number
  title: string
  status: string
  reject_reason: string
}

export interface StatusSummary {
  active: number
  pending: number
  recruiting: number
  draft: number
  ended: number
}

export interface HomeStatsOwner extends HomeStatsBase {
  my_activity_count: number
  pending_issues: PendingIssue[]
  status_summary: StatusSummary
  recruiting_activities: ActivityListItem[]
}

export type HomeStatsData = HomeStatsBase | HomeStatsStudent | HomeStatsOwner

export function useHomeStats() {
  const data = ref<HomeStatsData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchStats() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/home/stats', {
        credentials: 'include',
      })
      if (res.ok) {
        const json = await res.json()
        if (json.code === 200) {
          data.value = json.data
        } else {
          error.value = json.message || '请求失败'
        }
      } else {
        error.value = '服务器错误，请稍后重试'
      }
    } catch (e) {
      error.value = '服务器错误，请稍后重试'
      console.error('Home stats fetch error:', e)
    } finally {
      loading.value = false
    }
  }

  function retry() {
    fetchStats()
  }

  return { data, loading, error, fetchStats, retry }
}
