<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import {
  Clock,
  MapPin,
  Tag,
  Users,
  Building2,
  CheckCircle2,
  XCircle,
  Eye,
  Inbox,
  Loader2,
  AlertTriangle,
  RotateCcw,
  Image as ImageIcon,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useActivityAudit } from '@/composables/useActivityAudit'
import type { AuditActivityItem } from '@/types/activity'

const {
  items, loading, error, total, hasMore, actionLoading,
  fetchList, loadMore, approve, reject, retry,
} = useActivityAudit()

// 筛选
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待审核' },
  { key: 'active', label: '报名中' },
  { key: 'ended', label: '已结束' },
  { key: 'rejected', label: '已驳回' },
]
const activeFilter = ref('all')

function onFilterChange(key: string) {
  activeFilter.value = key
  fetchList(key)
}

// 状态标签
const statusMap: Record<string, { label: string; cls: string; icon: typeof Clock }> = {
  pending:  { label: '待审核', cls: 'status-pending',  icon: Clock },
  active:   { label: '报名中', cls: 'status-active',   icon: CheckCircle2 },
  ended:    { label: '已结束', cls: 'status-ended',    icon: CheckCircle2 },
  rejected: { label: '已驳回', cls: 'status-rejected', icon: XCircle },
}

// 查看详情弹窗
const detailModal = ref(false)
const detailItem = ref<AuditActivityItem | null>(null)

function openDetail(item: AuditActivityItem) {
  detailItem.value = item
  detailModal.value = true
}

// 驳回弹窗
const rejectModal = ref(false)
const rejectTarget = ref<AuditActivityItem | null>(null)
const rejectReason = ref('')
const rejectError = ref('')

function openRejectModal(item: AuditActivityItem) {
  rejectTarget.value = item
  rejectReason.value = ''
  rejectError.value = ''
  rejectModal.value = true
}

async function confirmReject() {
  if (rejectReason.value.trim().length < 2) {
    rejectError.value = '驳回原因至少 2 个字'
    return
  }
  if (!rejectTarget.value) return
  const ok = await reject(rejectTarget.value.id, rejectReason.value.trim())
  rejectModal.value = false
  if (ok) {
    showToast('已驳回')
    fetchList(activeFilter.value)
  } else {
    showToast('操作失败，请重试')
  }
}

// 通过
const approvingId = ref<number | null>(null)

async function handleApprove(item: AuditActivityItem) {
  approvingId.value = item.id
  const ok = await approve(item.id)
  approvingId.value = null
  if (ok) {
    showToast('已通过')
    fetchList(activeFilter.value)
  } else {
    showToast('操作失败，请重试')
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
function formatDate(iso: string) {
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function formatDateTime(iso: string) {
  const d = new Date(iso)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${h}:${m}`
}

// 能否打回
function canReject(item: AuditActivityItem) {
  return item.status === 'pending' || item.status === 'active'
}

onMounted(() => {
  fetchList('all')
})
</script>

<template>
  <div class="admin-layout">
    <AdminSidebar />

    <main class="admin-content">
      <h1 class="page-title">活动审核</h1>

      <!-- 筛选 -->
      <div class="filter-bar">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          class="filter-pill"
          :class="{ active: activeFilter === tab.key }"
          @click="onFilterChange(tab.key)"
        >{{ tab.label }}</button>
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
          <p class="text-text-secondary">暂无{{ activeFilter === 'all' ? '' : filterTabs.find(t => t.key === activeFilter)?.label }}活动</p>
        </div>
      </template>

      <!-- 列表 -->
      <template v-else>
        <div class="audit-list">
          <div v-for="item in items" :key="item.id" class="audit-card">
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
                  <Clock class="w-3.5 h-3.5" />
                  活动时间：{{ formatDateTime(item.start_time) }}
                </span>
                <span class="meta-row">
                  <Clock class="w-3.5 h-3.5" />
                  报名截止：{{ formatDateTime(item.registration_deadline) }}
                </span>
                <span class="meta-row">
                  <MapPin class="w-3.5 h-3.5" />
                  {{ item.location }}
                </span>
                <span class="meta-row">
                  <Tag class="w-3.5 h-3.5" />
                  {{ item.credit_type }}
                  <Users class="w-3.5 h-3.5 ml-2" />
                  {{ item.max_participants > 0 ? `限报 ${item.max_participants} 人` : '不限人数' }}
                </span>
              </div>

              <!-- 驳回原因 -->
              <div v-if="item.status === 'rejected' && item.reject_reason" class="reject-reason">
                <XCircle class="w-4 h-4 shrink-0" />
                <span>驳回原因：{{ item.reject_reason }}</span>
              </div>

              <!-- 操作按钮 -->
              <div class="card-actions">
                <button class="btn-text" @click="openDetail(item)">
                  <Eye class="w-3.5 h-3.5" />
                  查看详情
                </button>
                <template v-if="item.status === 'pending'">
                  <button
                    class="btn-approve"
                    :disabled="actionLoading && approvingId === item.id"
                    @click="handleApprove(item)"
                  >
                    <Loader2 v-if="actionLoading && approvingId === item.id" class="w-3.5 h-3.5 animate-spin" />
                    <CheckCircle2 v-else class="w-3.5 h-3.5" />
                    通过
                  </button>
                  <button class="btn-reject" @click="openRejectModal(item)">
                    <XCircle class="w-3.5 h-3.5" />
                    驳回
                  </button>
                </template>
                <template v-else-if="item.status === 'active'">
                  <button class="btn-reject" @click="openRejectModal(item)">
                    <RotateCcw class="w-3.5 h-3.5" />
                    打回
                  </button>
                </template>
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

      <!-- 查看详情弹窗 -->
      <GlassModal v-model="detailModal" title="活动详情" width="520px">
        <template v-if="detailItem">
          <!-- 封面 -->
          <div class="detail-cover">
            <img v-if="detailItem.cover_image_url" :src="detailItem.cover_image_url" alt="" class="detail-cover-img" />
            <div v-else class="detail-cover-placeholder">
              <ImageIcon class="w-10 h-10" />
            </div>
          </div>

          <h3 class="detail-title">{{ detailItem.title }}</h3>
          <div class="detail-tags">
            <span class="detail-credit-tag">
              <Tag class="w-3.5 h-3.5" />
              {{ detailItem.credit_type }}
            </span>
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
              <span class="detail-label">限报人数</span>
              <span>{{ detailItem.max_participants > 0 ? `${detailItem.max_participants} 人` : '不限' }}</span>
            </div>
          </div>

          <div class="detail-desc">
            <h4 class="detail-desc-title">活动描述</h4>
            <p class="detail-desc-text">{{ detailItem.description }}</p>
          </div>

          <div v-if="detailItem.status === 'rejected' && detailItem.reject_reason" class="reject-reason">
            <XCircle class="w-4 h-4 shrink-0" />
            <span>驳回原因：{{ detailItem.reject_reason }}</span>
          </div>
        </template>

        <template #footer="{ close }">
          <template v-if="detailItem && canReject(detailItem)">
            <button class="btn-approve" @click="close(); handleApprove(detailItem!)">
              <CheckCircle2 class="w-3.5 h-3.5" />
              <span>通过</span>
            </button>
            <button class="btn-reject" @click="close(); openRejectModal(detailItem!)">
              <XCircle v-if="detailItem!.status === 'pending'" class="w-3.5 h-3.5" />
              <RotateCcw v-else class="w-3.5 h-3.5" />
              {{ detailItem!.status === 'pending' ? '驳回' : '打回' }}
            </button>
          </template>
        </template>
      </GlassModal>

      <!-- 驳回弹窗 -->
      <GlassModal v-model="rejectModal" title="驳回活动" width="400px">
        <div class="reject-notice">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>驳回后活动发布者将收到通知，请填写具体原因以便修改。</span>
        </div>

        <label class="reject-label">驳回原因 <span class="text-danger">*</span></label>
        <textarea
          v-model="rejectReason"
          class="reject-textarea"
          placeholder="至少 2 个字"
          rows="3"
        ></textarea>
        <p v-if="rejectError" class="reject-error">{{ rejectError }}</p>

        <template #footer="{ close }">
          <button class="btn-cancel" @click="close">取消</button>
          <button
            class="btn-reject"
            :disabled="actionLoading"
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

/* ── 筛选栏 ── */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-pill {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 150ms;
}

.filter-pill:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.filter-pill.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

/* ── 审核卡片列表 ── */
.audit-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audit-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-card);
  display: flex;
  gap: 16px;
  transition: box-shadow 150ms;
}

.audit-card:hover {
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

/* 驳回原因 */
.reject-reason {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: #DC2626;
  line-height: 1.5;
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

.btn-approve {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  background: var(--color-success);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 150ms;
}

.btn-approve:hover { opacity: 0.9; }
.btn-approve:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-reject {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  background: var(--color-danger);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 150ms;
}

.btn-reject:hover { opacity: 0.9; }
.btn-reject:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── 驳回弹窗 ── */
.reject-notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(245, 158, 11, 0.08);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: #92400E;
  margin-bottom: 16px;
  line-height: 1.5;
}

.reject-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.reject-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  resize: vertical;
  min-height: 72px;
  transition: border-color 150ms;
  font-family: inherit;
}

.reject-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.reject-error {
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 4px;
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
  margin-bottom: 16px;
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

.detail-desc {
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
  margin-bottom: 8px;
}

.detail-desc-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.detail-desc-text {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
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

/* ── 空状态 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  gap: 12px;
}

/* ── 骨架屏 ── */
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

/* ── 错误卡片 ── */
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
