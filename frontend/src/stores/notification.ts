import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { request } from '@/utils/request'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const pollInterval = ref(600_000)  // 默认 10 分钟
  let pollTimer: ReturnType<typeof setInterval> | null = null

  async function fetchUnreadCount() {
    try {
      const res = await request<{ unread_count: number }>('/notifications?page=1&page_size=1')
      if (res.code === 200) {
        unreadCount.value = res.data.unread_count ?? 0
      }
    } catch {
      // 静默失败
    }
  }

  async function initPollInterval() {
    try {
      const res = await request<{ notification_poll_interval: number }>('/config/public')
      if (res.code === 200 && res.data.notification_poll_interval > 0) {
        pollInterval.value = res.data.notification_poll_interval
      }
    } catch {
      // 使用默认值
    }
  }

  async function startPolling() {
    await initPollInterval()
    fetchUnreadCount()
    if (!pollTimer) {
      pollTimer = setInterval(fetchUnreadCount, pollInterval.value)
    }
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function decrement() {
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  function resetToZero() {
    unreadCount.value = 0
  }

  return {
    unreadCount: computed(() => unreadCount.value),
    fetchUnreadCount,
    startPolling,
    stopPolling,
    decrement,
    resetToZero,
  }
})
