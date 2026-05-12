<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  User,
  Inbox,
  Loader2,
  Pencil,
  CheckCircle2,
  CheckCheck,
  Clock,
  FileEdit,
  XCircle,
} from 'lucide-vue-next'
import ActivityCard from '@/components/common/ActivityCard.vue'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import type { ActivityListItem, OwnerPublicProfile, OwnerPublicActivity } from '@/types/activity'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const profile = ref<OwnerPublicProfile | null>(null)
const activities = ref<ActivityListItem[]>([])
const loading = ref(true)
const error = ref('')

// 分页（加载更多）
const page = ref(1)
const pageSize = 12
const total = ref(0)
const hasMore = computed(() => activities.value.length < total.value)
const loadingMore = ref(false)

const ownerId = computed(() => Number(route.params.id))

// 将 API 简化结构映射为完整 ActivityListItem
function mapToActivityListItem(item: OwnerPublicActivity): ActivityListItem {
  return {
    id: item.id,
    title: item.title,
    activity_type: item.activity_type,
    credit_type: item.credit_type,
    credit_value: item.credit_value,
    owner_id: ownerId.value,
    owner_name: profile.value?.name ?? '',
    owner_avatar_url: profile.value?.avatar_url ?? null,
    cover_image_url: item.cover_image_url,
    start_time: '',
    end_time: '',
    location: '',
    registration_deadline: item.registration_deadline,
    participant_count: item.participant_count,
    max_participants: item.max_participants,
    status: item.status,
    created_at: '',
    has_qrcode: false,
    is_favorited: false,
    is_participated: false,
  }
}

// 加载主体信息（含初始活动列表）
async function loadProfile() {
  loading.value = true
  error.value = ''
  try {
    const data = await request(`/owners/${ownerId.value}`)
    if (data.code === 200) {
      profile.value = data.data
      total.value = data.data.activity_count
      activities.value = (data.data.activities ?? []).map(mapToActivityListItem)
      page.value = 1
    } else {
      error.value = data.message || '加载失败'
    }
  } catch {
    error.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 加载更多活动
async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  try {
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('page_size', String(pageSize))
    const data = await request(`/activities/owner/${ownerId.value}?${params.toString()}`)
    if (data.code === 200) {
      const items: ActivityListItem[] = (data.data.items ?? []).map(mapToActivityListItem)
      activities.value.push(...items)
      total.value = data.data.total
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loadingMore.value = false
  }
}

// 点击活动卡片
function handleActivityClick(id: number) {
  router.push(`/activities/${id}`)
}

// ── 活动状态标签 ──
type ActivityStatus = 'draft' | 'pending' | 'active' | 'ongoing' | 'ended' | 'rejected'

interface StatusDisplay {
  label: string
  bgClass: string
  textClass: string
  icon: typeof FileEdit
}

const statusConfig: Record<string, StatusDisplay> = {
  draft: { label: '草稿', bgClass: 'status-bg-draft', textClass: 'status-text-draft', icon: FileEdit },
  pending: { label: '待审核', bgClass: 'status-bg-pending', textClass: 'status-text-pending', icon: Clock },
  active_recruiting: { label: '报名中', bgClass: 'status-bg-active', textClass: 'status-text-active', icon: CheckCircle2 },
  active_ongoing: { label: '进行中', bgClass: 'status-bg-ongoing', textClass: 'status-text-ongoing', icon: CheckCircle2 },
  ended: { label: '已结束', bgClass: 'status-bg-ended', textClass: 'status-text-ended', icon: CheckCheck },
  rejected: { label: '已驳回', bgClass: 'status-bg-rejected', textClass: 'status-text-rejected', icon: XCircle },
}

function getStatusKey(activity: ActivityListItem): string {
  if (activity.status === 'active') {
    return new Date(activity.registration_deadline) > new Date() ? 'active_recruiting' : 'active_ongoing'
  }
  return activity.status
}

function getStatusDisplay(activity: ActivityListItem): StatusDisplay {
  return statusConfig[getStatusKey(activity)] ?? statusConfig.draft
}

// 收藏切换
async function handleFavorite(id: number) {
  try {
    const data = await request('/favorites', {
      method: 'POST',
      body: JSON.stringify({ activity_id: id }),
    })
    if (data.code === 200) {
      const item = activities.value.find(a => a.id === id)
      if (item) item.is_favorited = data.data.is_favorited
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

// 返回
function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/activities')
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <div class="owner-profile-page">
    <!-- 返回栏 -->
    <div class="back-bar">
      <button class="back-btn" @click="goBack">
        <ArrowLeft class="w-4 h-4" />
        <span>返回</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
      <span>加载中...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <Inbox class="w-12 h-12 text-text-disabled mb-3" />
      <p>{{ error }}</p>
      <button class="retry-btn" @click="loadProfile">重试</button>
    </div>

    <!-- 主内容 -->
    <template v-else-if="profile">
      <div class="owner-layout">
        <!-- 左栏：主体信息 -->
        <div class="owner-info-card">
          <div class="avatar-wrapper">
            <img v-if="profile.avatar_url" :src="profile.avatar_url" :alt="profile.name" class="avatar-img" />
            <div v-else class="avatar-placeholder">
              <User class="w-8 h-8 text-text-disabled" />
            </div>
          </div>

          <h1 class="owner-name">{{ profile.name }}</h1>
          <p class="owner-count">已发布 {{ profile.activity_count }} 个活动</p>

          <p v-if="profile.bio" class="owner-bio">{{ profile.bio }}</p>

          <button
            v-if="profile.is_self"
            class="edit-profile-btn"
            @click="router.push('/owner-profile')"
          >
            <Pencil class="w-3.5 h-3.5" />
            编辑资料
          </button>
        </div>

        <!-- 右栏：活动列表 -->
        <div class="activities-section">
          <h2 class="section-title">发布的活动</h2>

          <!-- 空状态 -->
          <div v-if="activities.length === 0" class="empty-state">
            <Inbox class="w-12 h-12 text-text-disabled mb-3" />
            <p>该主体暂无发布活动</p>
          </div>

          <!-- 活动网格 -->
          <div v-else class="activity-grid">
            <div
              v-for="activity in activities"
              :key="activity.id"
              class="activity-card-wrapper"
            >
              <div class="status-badge" :class="[getStatusDisplay(activity).bgClass, getStatusDisplay(activity).textClass]">
                <component :is="getStatusDisplay(activity).icon" class="w-3 h-3" />
                {{ getStatusDisplay(activity).label }}
              </div>
              <ActivityCard
                :data="activity"
                show-favorite
                @click="handleActivityClick"
                @favorite="handleFavorite"
              />
            </div>
          </div>

          <!-- 加载更多 -->
          <div v-if="activities.length > 0" class="load-more">
            <button
              v-if="hasMore && !loadingMore"
              class="load-more-btn"
              @click="loadMore"
            >
              加载更多
            </button>
            <div v-if="loadingMore" class="loading-indicator">
              <Loader2 class="w-5 h-5 animate-spin text-primary" />
              <span>加载中...</span>
            </div>
            <p v-if="!hasMore && !loadingMore" class="no-more">
              已加载全部 {{ total }} 个活动
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.owner-profile-page {
  min-height: calc(100dvh - 64px);
  padding: 0 16px 32px;
  max-width: 1280px;
  margin: 0 auto;
}
@media (min-width: 768px) {
  .owner-profile-page {
    padding: 0 24px 40px;
  }
}

/* 返回栏 */
.back-bar {
  padding: 12px 0;
  margin-bottom: 4px;
}
.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: #64748B;
  transition: all 150ms ease;
}
.back-btn:hover {
  background: #F1F5F9;
  color: #1E293B;
}

/* 加载/错误状态 */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  text-align: center;
  color: #64748B;
  font-size: 14px;
  gap: 8px;
}
.retry-btn {
  margin-top: 12px;
  padding: 8px 20px;
  background: #F1F5F9;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  transition: all 150ms ease;
}
.retry-btn:hover {
  background: #E2E8F0;
}

/* 布局 */
.owner-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
@media (min-width: 1024px) {
  .owner-layout {
    flex-direction: row;
    align-items: flex-start;
    gap: 32px;
  }
}

/* 主体信息卡片 */
.owner-info-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 32px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
}
@media (min-width: 1024px) {
  .owner-info-card {
    width: 40%;
    min-width: 280px;
    position: sticky;
    top: 80px;
  }
}

.avatar-wrapper {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  border-radius: 50%;
  overflow: hidden;
  background: #F1F5F9;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.owner-name {
  font-size: 18px;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 6px;
}
.owner-count {
  font-size: 13px;
  color: #64748B;
  margin-bottom: 16px;
}
.owner-bio {
  font-size: 14px;
  color: #64748B;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-align: left;
  margin-bottom: 16px;
}

.edit-profile-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: rgba(59, 130, 246, 0.08);
  color: #3B82F6;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 150ms ease;
}
.edit-profile-btn:hover {
  background: rgba(59, 130, 246, 0.15);
}

/* 活动列表区 */
.activities-section {
  flex: 1;
  min-width: 0;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 16px;
}

.activity-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 640px) {
  .activity-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 活动卡片包装器（含状态标签） */
.activity-card-wrapper {
  position: relative;
}
.activity-card-wrapper :deep(.activity-card) {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  border-radius: 12px;
  overflow: hidden;
}

/* 状态标签 */
.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
.status-bg-draft { background: rgba(241, 245, 249, 0.92); }
.status-text-draft { color: #475569; }

.status-bg-pending { background: rgba(255, 251, 235, 0.92); }
.status-text-pending { color: #B45309; }

.status-bg-active { background: rgba(236, 253, 245, 0.92); }
.status-text-active { color: #047857; }

.status-bg-ongoing { background: rgba(238, 242, 255, 0.92); }
.status-text-ongoing { color: #3730A3; }

.status-bg-ended { background: rgba(238, 242, 255, 0.92); }
.status-text-ended { color: #4338CA; }

.status-bg-rejected { background: rgba(254, 242, 242, 0.92); }
.status-text-rejected { color: #B91C1C; }

/* 加载更多 */
.load-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 24px;
  gap: 8px;
}
.load-more-btn {
  padding: 10px 32px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #1E293B;
  transition: all 150ms ease;
}
.load-more-btn:hover {
  border-color: #3B82F6;
  color: #3B82F6;
}
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748B;
}
.no-more {
  font-size: 13px;
  color: #94A3B8;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: #94A3B8;
  font-size: 14px;
}

/* 动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
