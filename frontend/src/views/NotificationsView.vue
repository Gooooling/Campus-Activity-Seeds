<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft,
  Megaphone,
  Star,
  ClipboardCheck,
  BellOff,
  ChevronRight,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { request } from '@/utils/request'
import type { NotificationItem, NotificationListData } from '@/types/activity'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

type FilterType = 'all' | 'announcement' | 'favorite_reminder' | 'audit_result'

const activeFilter = ref<FilterType>('all')
const loading = ref(false)
const loadingMore = ref(false)
const items = ref<NotificationItem[]>([])
const currentPage = ref(1)
const hasMore = ref(false)
const pageSize = 20
const expandedId = ref<number | null>(null)

const filters: { key: FilterType; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'announcement', label: '公告' },
  { key: 'favorite_reminder', label: '收藏提醒' },
  { key: 'audit_result', label: '审核通知' },
]

const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value
  return items.value.filter(i => i.type === activeFilter.value)
})

const typeIconMap = {
  announcement: Megaphone,
  favorite_reminder: Star,
  audit_result: ClipboardCheck,
}

const typeTitleMap = {
  announcement: '系统公告',
  favorite_reminder: '收藏提醒',
  audit_result: '审核通知',
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.floor((+target - +today) / (1000 * 60 * 60 * 24))

  const hh = d.getHours().toString().padStart(2, '0')
  const mm = d.getMinutes().toString().padStart(2, '0')

  if (diffDays === 0) return `今天 ${hh}:${mm}`
  if (diffDays === -1) return `昨天 ${hh}:${mm}`
  if (diffDays >= -6 && diffDays < 0) {
    const weekdays = ['日', '一', '二', '三', '四', '五', '六']
    return `周${weekdays[d.getDay()]} ${hh}:${mm}`
  }
  return `${d.getMonth() + 1}月${d.getDate()}日 ${hh}:${mm}`
}

function formatTimeDesktop(dateStr: string): string {
  const d = new Date(dateStr)
  const yyyy = d.getFullYear()
  const MM = (d.getMonth() + 1).toString().padStart(2, '0')
  const dd = d.getDate().toString().padStart(2, '0')
  const hh = d.getHours().toString().padStart(2, '0')
  const mm = d.getMinutes().toString().padStart(2, '0')
  return `${yyyy}-${MM}-${dd} ${hh}:${mm}`
}

async function fetchNotifications(reset = true) {
  if (!authStore.isLoggedIn) return
  if (reset) {
    loading.value = true
    currentPage.value = 1
    items.value = []
  } else {
    loadingMore.value = true
  }

  try {
    const page = reset ? 1 : currentPage.value
    const data = await request(`/notifications?type=${activeFilter.value}&page=${page}&page_size=${pageSize}`)
    if (data.code === 200) {
      const newItems = data.data.items ?? []
      if (reset) {
        items.value = newItems
      } else {
        items.value.push(...newItems)
      }
      hasMore.value = newItems.length === pageSize
    }
  } catch (e) {
    console.error('Notifications fetch error:', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  currentPage.value += 1
  await fetchNotifications(false)
}

async function markAsRead(id: number) {
  if (!authStore.isLoggedIn) return
  const item = items.value.find(i => i.id === id)
  if (!item || item.is_read) return
  try {
    const data = await request(`/notifications/${id}/read`, {
      method: 'PUT',
    })
    if (data.code === 200) {
      item.is_read = true
      notificationStore.decrement()
    }
  } catch (e) {
    console.error('Mark as read error:', e)
    // 不做本地降级
  }
}

async function markAllRead() {
  if (!authStore.isLoggedIn || notificationStore.unreadCount === 0) return
  try {
    const data = await request('/notifications/read-all', {
      method: 'PUT',
    })
    if (data.code === 200) {
      items.value.forEach(i => { i.is_read = true })
      notificationStore.resetToZero()
    }
  } catch (e) {
    console.error('Mark all read error:', e)
    // 不做本地降级
  }
}

function handleClick(item: NotificationItem) {
  // 公告类型展开/收起
  if (item.type === 'announcement' && !item.link) {
    expandedId.value = expandedId.value === item.id ? null : item.id
    return
  }
  if (!item.is_read) markAsRead(item.id)
  if (!item.link) return
  if (item.link.type === 'activity') {
    router.push(`/activities/${item.link.id}`)
  } else if (item.link.type === 'my_activities') {
    router.push('/my-activities')
  } else if (item.link.type === 'profile') {
    router.push('/owner-profile')
  }
}

function handleActionClick(e: Event, item: NotificationItem) {
  e.stopPropagation()
  if (!item.is_read) markAsRead(item.id)
  if (item.action === 'edit_activity' && item.link) {
    router.push(`/activities/${item.link.id}/edit`)
  } else if (item.action === 'edit_profile') {
    router.push('/owner-profile')
  }
}

onMounted(() => fetchNotifications(true))
</script>

<template>
  <div class="notifications-page">
    <!-- 移动端顶部导航 -->
    <div class="mobile-header">
      <button class="back-btn" @click="router.back()">
        <ChevronLeft class="w-5 h-5" />
      </button>
      <h1 class="page-title">消息中心</h1>
      <div class="w-10" />
    </div>

    <!-- 桌面端标题栏 -->
    <div class="desktop-header">
      <h1 class="page-title">消息中心</h1>
      <button
        v-if="notificationStore.unreadCount > 0"
        class="mark-all-btn"
        @click="markAllRead"
      >
        全部标记为已读
      </button>
    </div>

    <!-- 筛选标签 -->
    <div class="filter-bar">
      <div class="filter-scroll">
        <button
          v-for="f in filters"
          :key="f.key"
          class="filter-pill"
          :class="{ active: activeFilter === f.key }"
          @click="activeFilter = f.key; fetchNotifications(true)"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="notification-list">
      <div v-if="loading" class="loading-hint">加载中...</div>

      <div v-else-if="filteredItems.length === 0" class="empty-hint">
        <BellOff class="w-12 h-12 text-text-disabled mb-3" />
        <p>暂无消息</p>
        <p class="empty-sub">有新通知时会在这里显示</p>
      </div>

      <template v-else>
        <div
          v-for="item in filteredItems"
          :key="item.id"
          class="notification-card"
          :class="{ unread: !item.is_read }"
          @click="handleClick(item)"
        >
          <div class="card-accent" />
          <div class="card-body">
            <div class="card-header">
              <div class="card-type">
                <component
                  :is="typeIconMap[item.type]"
                  class="w-4 h-4 shrink-0"
                  :class="item.is_read ? 'text-text-secondary' : 'text-primary'"
                />
                <span
                  class="type-label"
                  :class="item.is_read ? 'text-text-secondary' : 'text-text-primary'"
                >
                  {{ typeTitleMap[item.type] }}
                </span>
              </div>
              <div class="card-meta">
                <span v-if="!item.is_read" class="unread-dot" />
                <span class="time-mobile text-text-disabled">{{ formatTime(item.created_at) }}</span>
                <span class="time-desktop text-text-disabled">{{ formatTimeDesktop(item.created_at) }}</span>
              </div>
            </div>
            <p class="card-content" :class="{ 'text-text-secondary': item.is_read, 'card-content-expanded': expandedId === item.id }">
              {{ item.content }}
            </p>
            <div v-if="item.action" class="card-action">
              <span class="action-link" @click="handleActionClick($event, item)">
                {{ item.action === 'edit_activity' ? '去修改活动' : '去修改资料' }}
                <ChevronRight class="w-3.5 h-3.5" />
              </span>
            </div>
            <div v-else-if="item.link && item.type === 'favorite_reminder'" class="card-action">
              <span class="action-link" @click.stop="router.push(`/activities/${item.link.id}`)">
                去看看
                <ChevronRight class="w-3.5 h-3.5" />
              </span>
            </div>
            <div v-else-if="item.type === 'announcement'" class="card-action">
              <span class="action-link">
                {{ expandedId === item.id ? '收起' : '查看详情' }}
                <ChevronRight class="w-3.5 h-3.5" :class="{ 'rotate-90': expandedId === item.id }" />
              </span>
            </div>
          </div>
        </div>
      </template>

      <!-- 加载更多 -->
      <div v-if="!loading && hasMore" class="load-more-wrap">
        <button class="load-more-btn" :disabled="loadingMore" @click="loadMore">
          {{ loadingMore ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </div>

    <!-- 移动端全部已读 -->
    <div v-if="notificationStore.unreadCount > 0 && filteredItems.length > 0" class="mobile-footer">
      <button class="mark-all-btn-mobile" @click="markAllRead">
        全部标记为已读
      </button>
    </div>
  </div>
</template>

<style scoped>
.notifications-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 16px;
  min-height: calc(100dvh - 64px);
}

@media (min-width: 640px) {
  .notifications-page {
    padding: 24px;
  }
}

/* ── 移动端顶部导航 ── */
.mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #64748B;
  transition: background 150ms ease;
}
.back-btn:hover {
  background: #F1F5F9;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
}

/* ── 桌面端标题栏 ── */
.desktop-header {
  display: none;
}
@media (min-width: 768px) {
  .mobile-header {
    display: none;
  }
  .desktop-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
  }
  .page-title {
    font-size: 20px;
  }
  .mark-all-btn {
    font-size: 13px;
    font-weight: 500;
    color: #3B82F6;
    padding: 6px 12px;
    border-radius: 8px;
    transition: background 150ms ease;
  }
  .mark-all-btn:hover {
    background: rgba(59, 130, 246, 0.08);
  }
}

/* ── 筛选标签 ── */
.filter-bar {
  margin-bottom: 16px;
}
.filter-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
}
.filter-scroll::-webkit-scrollbar {
  display: none;
}
.filter-pill {
  padding: 7px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  background: #F1F5F9;
  transition: all 150ms ease;
  white-space: nowrap;
  flex-shrink: 0;
}
.filter-pill:hover {
  background: #E2E8F0;
}
.filter-pill.active {
  background: #3B82F6;
  color: white;
}

/* ── 消息列表 ── */
.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-card {
  display: flex;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease;
}
.notification-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-accent {
  width: 3px;
  flex-shrink: 0;
  background: transparent;
  transition: background 150ms ease;
}
.notification-card.unread .card-accent {
  background: #3B82F6;
}

.card-body {
  flex: 1;
  padding: 14px 16px;
  min-width: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.card-type {
  display: flex;
  align-items: center;
  gap: 6px;
}
.type-label {
  font-size: 14px;
  font-weight: 600;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #F59E0B;
  flex-shrink: 0;
}
.time-mobile {
  font-size: 12px;
}
.time-desktop {
  display: none;
  font-size: 13px;
}
@media (min-width: 768px) {
  .time-mobile {
    display: none;
  }
  .time-desktop {
    display: inline;
  }
}

.card-content {
  font-size: 14px;
  line-height: 1.5;
  color: #1E293B;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-content-expanded {
  display: block;
  -webkit-line-clamp: unset;
  overflow: visible;
}

.card-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.action-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 500;
  color: #3B82F6;
  transition: opacity 150ms ease;
}
.action-link:hover {
  opacity: 0.8;
}
.rotate-90 {
  transform: rotate(90deg);
}

/* ── 通用状态 ── */
.loading-hint {
  text-align: center;
  padding: 40px 0;
  color: #94A3B8;
  font-size: 14px;
}
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 0;
  color: #94A3B8;
  font-size: 14px;
}
.empty-sub {
  font-size: 13px;
  margin-top: 4px;
}

/* ── 移动端底部 ── */
.mobile-footer {
  display: flex;
  justify-content: center;
  padding: 24px 0 8px;
}
.mark-all-btn-mobile {
  font-size: 14px;
  font-weight: 500;
  color: #3B82F6;
  padding: 8px 16px;
  border-radius: 10px;
  transition: background 150ms ease;
}
.mark-all-btn-mobile:hover {
  background: rgba(59, 130, 246, 0.08);
}
@media (min-width: 768px) {
  .mobile-footer {
    display: none;
  }
}

/* ── 加载更多 -- */
.load-more-wrap {
  display: flex;
  justify-content: center;
  padding: 20px 0 8px;
}
.load-more-btn {
  font-size: 14px;
  font-weight: 500;
  color: #3B82F6;
  padding: 8px 20px;
  border-radius: 10px;
  background: #F1F5F9;
  transition: all 150ms ease;
}
.load-more-btn:hover:not(:disabled) {
  background: #E2E8F0;
}
.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
