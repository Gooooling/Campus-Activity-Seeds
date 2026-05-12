<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Inbox,
  Loader2,
  AlertTriangle,
} from 'lucide-vue-next'
import MyActivityCard from '@/components/common/MyActivityCard.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import type { MyActivityItem } from '@/types/activity'

const router = useRouter()
const authStore = useAuthStore()

// 状态筛选
type StatusFilter = '' | 'draft' | 'pending' | 'active' | 'ended' | 'rejected'
const currentStatus = ref<StatusFilter>('')

const statusFilters: { value: StatusFilter; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'draft', label: '草稿' },
  { value: 'pending', label: '待审核' },
  { value: 'active', label: '报名中' },
  { value: 'ended', label: '已结束' },
  { value: 'rejected', label: '已驳回' },
]

// 活动列表
const activities = ref<MyActivityItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const total = ref(0)
const hasMore = computed(() => activities.value.length < total.value)
const loadingMore = ref(false)

// 删除确认弹窗
const showDeleteModal = ref(false)
const deleteTarget = ref<MyActivityItem | null>(null)
const deleting = ref(false)

// 加载活动列表
async function loadActivities(reset = false) {
  if (loading.value && reset) return
  if (loadingMore.value && !reset) return

  if (reset) {
    page.value = 1
    activities.value = []
    loading.value = true
  }

  try {
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('page_size', String(pageSize))
    if (currentStatus.value) params.set('status', currentStatus.value)

    const data = await request(`/activities/my?${params.toString()}`)

    if (data.code === 200) {
      const items: MyActivityItem[] = data.data.items ?? []
      if (reset) {
        activities.value = items
      } else {
        activities.value.push(...items)
      }
      total.value = data.data.total
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 加载更多
function loadMore() {
  page.value++
  loadingMore.value = true
  loadActivities()
}

// 筛选切换
function setFilter(status: StatusFilter) {
  if (currentStatus.value === status) return
  currentStatus.value = status
  loadActivities(true)
}

// 点击活动卡片 → 跳转详情
function handleActivityClick(id: number) {
  router.push(`/activities/${id}`)
}

// 编辑/去修改 → 跳转编辑页
function handleEdit(id: number) {
  router.push(`/edit-activity?edit=${id}`)
}

// 追加照片 → 跳转详情页（详情页已有追加照片功能）
function handleAddPhotos(id: number) {
  router.push(`/activities/${id}`)
}

// 删除
function handleDeleteRequest(id: number) {
  const item = activities.value.find(a => a.id === id)
  if (item) {
    deleteTarget.value = item
    showDeleteModal.value = true
  }
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return
  deleting.value = true
  try {
    const data = await request(`/activities/${deleteTarget.value.id}`, {
      method: 'DELETE',
    })
    if (data.code === 200) {
      activities.value = activities.value.filter(a => a.id !== deleteTarget.value!.id)
      total.value--
      showDeleteModal.value = false
      deleteTarget.value = null
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

function cancelDelete() {
  showDeleteModal.value = false
  deleteTarget.value = null
}

onMounted(() => {
  loadActivities(true)
})
</script>

<template>
  <div class="my-activities-page">
    <!-- 页面标题 -->
    <h1 class="page-title">我的活动</h1>

    <!-- 状态筛选 -->
    <div class="filter-bar">
      <div class="filter-scroll">
        <button
          v-for="f in statusFilters"
          :key="f.value"
          class="filter-pill"
          :class="{ active: currentStatus === f.value }"
          @click="setFilter(f.value)"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && activities.length === 0" class="loading-state">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
      <span>加载中...</span>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && activities.length === 0" class="empty-state">
      <Inbox class="w-12 h-12 text-text-disabled mb-3" />
      <p class="empty-title">暂无活动</p>
      <p class="empty-desc">{{ currentStatus ? '该状态下暂无活动' : '你还没有发布过活动' }}</p>
      <button v-if="!currentStatus" class="publish-btn" @click="router.push('/publish')">
        发布活动
      </button>
    </div>

    <!-- 活动列表 -->
    <div v-else class="activity-list">
      <MyActivityCard
        v-for="item in activities"
        :key="item.id"
        :data="item"
        @click="handleActivityClick"
        @edit="handleEdit"
        @delete="handleDeleteRequest"
        @add-photos="handleAddPhotos"
      />
    </div>

    <!-- 加载更多 -->
    <div v-if="activities.length > 0" class="load-more">
      <button
        v-if="hasMore && !loadingMore && !loading"
        class="load-more-btn"
        @click="loadMore"
      >
        加载更多
      </button>
      <div v-if="loadingMore" class="loading-indicator">
        <Loader2 class="w-5 h-5 animate-spin text-primary" />
        <span>加载中...</span>
      </div>
      <p v-if="!hasMore && !loadingMore && !loading" class="no-more">
        已加载全部 {{ total }} 个活动
      </p>
    </div>

    <!-- 删除确认弹窗 -->
    <GlassModal v-model:modelValue="showDeleteModal" title="确认删除" width="400px">
      <div class="delete-modal-body">
        <AlertTriangle class="w-10 h-10 text-danger mb-3" />
        <p class="delete-msg">
          删除后不可恢复，确认删除「{{ deleteTarget?.title }}」吗？
        </p>
      </div>
      <template #footer="{ close }">
        <button class="btn-cancel" @click="cancelDelete">取消</button>
        <button class="btn-danger" :disabled="deleting" @click="confirmDelete">
          <Loader2 v-if="deleting" class="w-4 h-4 animate-spin" />
          确认删除
        </button>
      </template>
    </GlassModal>
  </div>
</template>

<style scoped>
.my-activities-page {
  min-height: calc(100dvh - 64px);
  padding: 16px;
  max-width: 1024px;
  margin: 0 auto;
}
@media (min-width: 768px) {
  .my-activities-page {
    padding: 24px 32px;
  }
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 16px;
}

/* 状态筛选 */
.filter-bar {
  margin-bottom: 20px;
}
.filter-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding-bottom: 4px;
}
.filter-scroll::-webkit-scrollbar {
  display: none;
}

.filter-pill {
  flex-shrink: 0;
  padding: 8px 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  background: #F1F5F9;
  transition: all 150ms ease;
  white-space: nowrap;
}
.filter-pill:hover {
  background: #E2E8F0;
}
.filter-pill.active {
  background: #3B82F6;
  color: white;
}

/* 加载/空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  color: #64748B;
  font-size: 14px;
  gap: 4px;
}
.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 4px;
}
.empty-desc {
  font-size: 14px;
  color: #94A3B8;
  margin-bottom: 16px;
}
.publish-btn {
  padding: 10px 24px;
  background: #3B82F6;
  color: white;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  transition: all 150ms ease;
}
.publish-btn:hover {
  background: #2563EB;
}

/* 活动列表 */
.activity-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 768px) {
  .activity-list {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 加载更多 */
.load-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 24px;
  margin-bottom: 32px;
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

/* 删除弹窗 */
.delete-modal-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 0;
}
.delete-msg {
  font-size: 15px;
  color: #1E293B;
  line-height: 1.6;
}

.btn-cancel {
  padding: 8px 20px;
  background: #F1F5F9;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  transition: all 150ms ease;
}
.btn-cancel:hover {
  background: #E2E8F0;
}

.btn-danger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: var(--color-danger);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  transition: all 150ms ease;
}
.btn-danger:hover {
  background: var(--color-danger-hover);
}
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
