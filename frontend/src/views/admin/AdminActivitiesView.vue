<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import {
  Search,
  Clock,
  MapPin,
  Users,
  Building2,
  CheckCircle2,
  XCircle,
  Eye,
  Trash2,
  Ban,
  Inbox,
  Loader2,
  AlertTriangle,
  Image as ImageIcon,
  X,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useAdminActivities } from '@/composables/useAdminActivities'
import type { AdminActivityItem } from '@/types/activity'

const {
  items, loading, error, total, hasMore, actionLoading,
  keyword, statusFilter,
  fetchList, loadMore, forceDelete, rejectActivity, retry,
} = useAdminActivities()

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout>
const searchInput = ref('')
watch(searchInput, (val) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    keyword.value = val
    fetchList()
  }, 400)
})

// 状态筛选
const statusOptions = [
  { key: 'all', label: '全部状态' },
  { key: 'draft', label: '草稿' },
  { key: 'pending', label: '待审核' },
  { key: 'active', label: '报名中' },
  { key: 'ended', label: '已结束' },
  { key: 'rejected', label: '已驳回' },
]

function onStatusChange(e: Event) {
  statusFilter.value = (e.target as HTMLSelectElement).value
  fetchList()
}

// 状态标签
const statusMap: Record<string, { label: string; cls: string; icon: typeof Clock }> = {
  draft:    { label: '草稿',   cls: 'status-draft',    icon: Clock },
  pending:  { label: '待审核', cls: 'status-pending',  icon: Clock },
  active:   { label: '报名中', cls: 'status-active',   icon: CheckCircle2 },
  ended:    { label: '已结束', cls: 'status-ended',    icon: CheckCircle2 },
  rejected: { label: '已驳回', cls: 'status-rejected', icon: XCircle },
}

// 查看详情弹窗
const detailModal = ref(false)
const detailItem = ref<AdminActivityItem | null>(null)

function openDetail(item: AdminActivityItem) {
  detailItem.value = item
  detailModal.value = true
}

// 驳回弹窗
const rejectModal = ref(false)
const rejectTarget = ref<AdminActivityItem | null>(null)
const rejectReason = ref('')
const rejectError = ref('')

function openRejectModal(item: AdminActivityItem) {
  rejectTarget.value = item
  rejectReason.value = ''
  rejectError.value = ''
  rejectModal.value = true
}

async function confirmReject() {
  if (!rejectTarget.value) return
  const reason = rejectReason.value.trim()
  if (reason.length < 2) {
    rejectError.value = '驳回原因至少需要2个字'
    return
  }
  const ok = await rejectActivity(rejectTarget.value.id, reason)
  rejectModal.value = false
  if (ok) {
    showToast('已驳回')
    fetchList()
  } else {
    showToast('驳回失败，请重试')
  }
}

// 删除确认弹窗
const deleteModal = ref(false)
const deleteTarget = ref<AdminActivityItem | null>(null)
const deleteReason = ref('')
const deleteError = ref('')

function openDeleteModal(item: AdminActivityItem) {
  deleteTarget.value = item
  deleteReason.value = ''
  deleteError.value = ''
  deleteModal.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  const reason = deleteReason.value.trim()
  if (reason.length < 2) {
    deleteError.value = '删除原因至少需要2个字'
    return
  }
  const ok = await forceDelete(deleteTarget.value.id, reason)
  deleteModal.value = false
  if (ok) {
    showToast('已删除')
    fetchList()
  } else {
    showToast('删除失败，请重试')
  }
}

// Toast
const toastVisible = ref(false)
const toastMsg = ref('')
let toastTimer: ReturnType<typeof setTimeout>

function showToast(msg: string) {
  toastMsg.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2000)
}

// 日期格式化
function formatDateTime(iso: string) {
  const d = new Date(iso)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${h}:${m}`
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="admin-layout">
    <AdminSidebar />

    <main class="admin-content">
      <h1 class="page-title">活动管理</h1>

      <!-- 搜索 + 筛选 -->
      <div class="toolbar">
        <div class="search-box">
          <Search class="search-icon" />
          <input
            v-model="searchInput"
            class="search-input"
            type="text"
            placeholder="搜索活动标题 / 主办方"
          />
          <button v-if="searchInput" class="search-clear" @click="searchInput = ''">
            <X class="w-3.5 h-3.5" />
          </button>
        </div>
        <select class="filter-select" :value="statusFilter" @change="onStatusChange">
          <option v-for="opt in statusOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
        </select>
      </div>

      <!-- 加载骨架 -->
      <template v-if="loading && !items.length">
        <div class="skeleton-list">
          <div v-for="i in 3" :key="i" class="skeleton-card" />
        </div>
      </template>

      <!-- 错误 -->
      <template v-else-if="error">
        <div class="error-card">
          <AlertTriangle class="w-8 h-8 text-danger" />
          <p class="text-text-primary font-medium">数据加载失败</p>
          <p class="text-text-secondary text-sm">{{ error }}</p>
          <button class="btn-primary mt-4" @click="retry">重新加载</button>
        </div>
      </template>

      <!-- 空状态 -->
      <template v-else-if="!items.length">
        <div class="empty-state">
          <Inbox class="w-12 h-12 text-text-disabled" />
          <p class="text-text-secondary">暂无匹配的活动</p>
        </div>
      </template>

      <!-- 列表 -->
      <template v-else>
        <div class="activity-list">
          <div v-for="item in items" :key="item.id" class="activity-card">
            <!-- 封面 -->
            <div class="card-cover">
              <img v-if="item.cover_image_url" :src="item.cover_image_url" alt="" class="cover-img" />
              <ImageIcon v-else class="cover-placeholder" />
            </div>

            <!-- 信息 -->
            <div class="card-body">
              <div class="card-header">
                <span class="card-title">{{ item.title }}</span>
                <span class="status-tag" :class="statusMap[item.status]?.cls">
                  <component :is="statusMap[item.status]?.icon" class="w-3.5 h-3.5" />
                  {{ statusMap[item.status]?.label }}
                </span>
              </div>

              <div class="card-meta">
                <span class="meta-row">
                  <Building2 class="w-3.5 h-3.5" />
                  {{ item.owner_name }}
                </span>
                <span class="meta-row">
                  <Users class="w-3.5 h-3.5" />
                  {{ item.participant_count }}人参与
                </span>
                <span class="meta-row">
                  <Clock class="w-3.5 h-3.5" />
                  截止：{{ formatDateTime(item.registration_deadline) }}
                </span>
                <span class="meta-row">
                  <MapPin class="w-3.5 h-3.5" />
                  {{ item.location }}
                </span>
              </div>

              <!-- 操作按钮 -->
              <div class="card-actions">
                <button class="btn-text" @click="openDetail(item)">
                  <Eye class="w-3.5 h-3.5" />
                  查看
                </button>
                <button
                  v-if="item.status === 'pending' || item.status === 'active'"
                  class="btn-reject"
                  @click="openRejectModal(item)"
                >
                  <Ban class="w-3.5 h-3.5" />
                  驳回
                </button>
                <button
                  class="btn-delete"
                  title="强制删除"
                  @click="openDeleteModal(item)"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="hasMore" class="load-more">
          <button class="btn-outline" :disabled="loading" @click="loadMore">
            <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
            加载更多
          </button>
        </div>
        <p v-else-if="items.length" class="all-loaded">已加载全部</p>
      </template>

      <!-- 底部警告 -->
      <div class="warning-bar">
        <AlertTriangle class="w-4 h-4 shrink-0" />
        <span>删除活动将同时清除所有参与记录，操作不可逆，请谨慎操作</span>
      </div>

      <!-- 查看详情弹窗 -->
      <GlassModal v-model="detailModal" title="活动详情" width="520px">
        <template v-if="detailItem">
          <div class="detail-cover">
            <img v-if="detailItem.cover_image_url" :src="detailItem.cover_image_url" alt="" class="detail-cover-img" />
            <div v-else class="detail-cover-placeholder">
              <ImageIcon class="w-10 h-10" />
            </div>
          </div>

          <h3 class="detail-title">{{ detailItem.title }}</h3>
          <div class="detail-tags">
            <span class="detail-credit-tag">{{ detailItem.credit_type }}</span>
            <span class="detail-credit-value">+{{ detailItem.credit_value ?? '-' }} 学分</span>
          </div>

          <div class="detail-info">
            <div class="detail-row">
              <Building2 class="w-4 h-4" />
              <span class="detail-label">主办方</span>
              <span>{{ detailItem.owner_name }}</span>
            </div>
            <div class="detail-row">
              <Clock class="w-4 h-4" />
              <span class="detail-label">活动时间</span>
              <span>{{ formatDateTime(detailItem.start_time) }} - {{ formatDateTime(detailItem.end_time) }}</span>
            </div>
            <div class="detail-row">
              <Clock class="w-4 h-4" />
              <span class="detail-label">报名截止</span>
              <span>{{ formatDateTime(detailItem.registration_deadline) }}</span>
            </div>
            <div class="detail-row">
              <MapPin class="w-4 h-4" />
              <span class="detail-label">地点</span>
              <span>{{ detailItem.location }}</span>
            </div>
            <div class="detail-row">
              <Users class="w-4 h-4" />
              <span class="detail-label">参与人数</span>
              <span>{{ detailItem.participant_count }} 人</span>
            </div>
          </div>
        </template>
      </GlassModal>

      <!-- 删除确认弹窗 -->
      <GlassModal v-model="deleteModal" title="确认删除活动" width="440px">
        <div class="delete-notice">
          <AlertTriangle class="w-5 h-5 shrink-0" />
          <div>
            <p class="font-medium" style="color: #B91C1C;">此操作不可逆</p>
            <p class="text-sm" style="color: #DC2626; margin-top: 4px;">
              活动「{{ deleteTarget?.title }}」将被永久删除，同时清除所有参与记录、学分记录。
              系统将自动通知参与学生和活动主体。
            </p>
          </div>
        </div>

        <div style="margin-top: 16px;">
          <label class="form-label" style="display:block; margin-bottom:6px; font-weight:500; color:#1e293b;">
            删除原因 <span style="color:#DC2626;">*</span>
          </label>
          <textarea
            v-model="deleteReason"
            class="reject-textarea"
            :class="{ 'reject-textarea--error': deleteError }"
            placeholder="请填写删除原因（至少2个字），将通知参与学生和活动主体..."
            rows="3"
          />
          <p v-if="deleteError" style="color: #DC2626; font-size: 12px; margin-top: 4px;">{{ deleteError }}</p>
        </div>

        <template #footer="{ close }">
          <button class="btn-cancel" @click="close">取消</button>
          <button
            class="btn-delete-confirm"
            :disabled="actionLoading"
            @click="confirmDelete"
          >
            <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
            确认删除
          </button>
        </template>
      </GlassModal>

      <!-- 驳回弹窗 -->
      <GlassModal v-model="rejectModal" title="驳回活动" width="400px">
        <p class="text-sm" style="color: var(--color-text-secondary); margin-bottom: 12px;">
          驳回活动「{{ rejectTarget?.title }}」，请填写驳回原因：
        </p>
        <textarea
          v-model="rejectReason"
          class="reject-textarea"
          :class="{ 'reject-textarea--error': rejectError }"
          placeholder="请输入驳回原因（至少2个字）..."
          rows="3"
          @input="rejectError = ''"
        />
        <p v-if="rejectError" class="reject-error">{{ rejectError }}</p>

        <template #footer="{ close }">
          <button class="btn-cancel" @click="close">取消</button>
          <button
            class="btn-reject-confirm"
            :disabled="actionLoading || !rejectReason.trim()"
            @click="confirmReject"
          >
            <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
            确认驳回
          </button>
        </template>
      </GlassModal>

      <!-- Toast -->
      <Teleport to="body">
        <Transition name="toast">
          <div v-if="toastVisible" class="toast-bar">{{ toastMsg }}</div>
        </Transition>
      </Teleport>
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100dvh;
}

.admin-content {
  flex: 1;
  background: var(--color-bg);
  padding: 24px;
  overflow-y: auto;
}

/* ── 页面标题 ── */
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 20px;
}

/* ── 工具栏 ── */
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-box {
  flex: 1;
  max-width: 400px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  width: 16px;
  height: 16px;
  color: var(--color-text-disabled);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 8px 36px 8px 38px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  transition: border-color 150ms;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.search-clear {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: var(--color-text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: background 150ms;
}

.search-clear:hover {
  background: var(--color-surface-alt);
}

.filter-select {
  padding: 8px 32px 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  cursor: pointer;
  transition: border-color 150ms;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

/* ── 活动卡片列表 ── */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.activity-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-card);
  display: flex;
  gap: 16px;
  transition: box-shadow 150ms;
}

.activity-card:hover {
  box-shadow: var(--shadow-card-hover);
}

/* 封面 */
.card-cover {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 28px;
  height: 28px;
  color: var(--color-text-disabled);
}

/* 卡片信息 */
.card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 状态标签 */
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
  white-space: nowrap;
}

.status-draft {
  background: rgba(148, 163, 184, 0.1);
  color: #64748B;
}

.status-pending {
  background: rgba(245, 158, 11, 0.1);
  color: #B45309;
}

.status-active {
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
}

.status-ended {
  background: rgba(99, 102, 241, 0.1);
  color: #4338CA;
}

.status-rejected {
  background: rgba(239, 68, 68, 0.1);
  color: #B91C1C;
}

/* 元信息 */
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
}

.meta-row {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 操作按钮 */
.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.btn-text {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 13px;
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 150ms;
}

.btn-text:hover {
  background: var(--color-primary-light);
}

.btn-delete {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 13px;
  color: var(--color-danger);
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 150ms;
}

.btn-delete:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.08);
}

.btn-delete:disabled {
  color: var(--color-text-disabled);
  cursor: not-allowed;
}

.btn-reject {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 13px;
  color: var(--color-accent);
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 150ms;
}

.btn-reject:hover {
  background: var(--color-accent-light, rgba(245, 158, 11, 0.08));
}

/* ── 驳回弹窗 ── */
.reject-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  resize: vertical;
  transition: border-color 150ms;
}

.reject-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.reject-textarea--error {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15);
}

.reject-error {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-danger);
}

.btn-reject-confirm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 150ms;
}

.btn-reject-confirm:hover { opacity: 0.9; }
.btn-reject-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── 底部警告 ── */
.warning-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(245, 158, 11, 0.08);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: #92400E;
  margin-top: 16px;
}

/* ── 删除确认弹窗 ── */
.delete-notice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--radius-sm);
}

.btn-cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 20px;
  font-size: 14px;
  color: var(--color-text-secondary);
  background: var(--color-surface-alt);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 150ms;
}

.btn-cancel:hover { background: var(--color-border); }

.btn-delete-confirm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: var(--color-danger);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 150ms;
}

.btn-delete-confirm:hover { opacity: 0.9; }
.btn-delete-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── 详情弹窗 ── */
.detail-cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 16px;
  background: var(--color-surface-alt);
}

.detail-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-disabled);
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.detail-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.detail-credit-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.detail-credit-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-accent);
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
}

.detail-row svg {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.detail-label {
  color: var(--color-text-secondary);
  min-width: 64px;
}

/* ── 分页 ── */
.load-more {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 24px;
  font-size: 14px;
  color: var(--color-primary);
  background: none;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 150ms;
}

.btn-outline:hover { background: var(--color-primary-light); }
.btn-outline:disabled { opacity: 0.6; cursor: not-allowed; }

.all-loaded {
  text-align: center;
  font-size: 13px;
  color: var(--color-text-disabled);
  margin-top: 16px;
}

/* ── 空状态 / 错误 / 骨架屏 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  gap: 12px;
}

.error-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
  gap: 8px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 150ms;
}

.btn-primary:hover { background: var(--color-primary-hover); }

.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-card {
  height: 112px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-alt);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ── Toast ── */
.toast-bar {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 24px;
  background: var(--color-text-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  z-index: 200;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 200ms, transform 200ms;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

/* ── 减少动效 ── */
@media (prefers-reduced-motion: reduce) {
  .skeleton-card { animation: none; }
  .toast-enter-active,
  .toast-leave-active { transition: none; }
}
</style>
