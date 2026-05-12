<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  Clock,
  Building2,
  User,
  Phone,
  BookOpen,
  CheckCircle2,
  XCircle,
  Eye,
  Inbox,
  Loader2,
  AlertTriangle,
  Image as ImageIcon,
  ArrowRightLeft,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useOwnerAudit } from '@/composables/useOwnerAudit'
import type { AuditOwnerItem, ContactChangeItem } from '@/types/activity'

const {
  items, loading, error, total, hasMore, actionLoading,
  fetchList, loadMore, approve, reject, retry,
  contactChanges, contactChangesLoading, contactChangesError,
  fetchContactChanges, approveContactChange, rejectContactChange,
} = useOwnerAudit()

// 主 Tab
const mainTabs = [
  { key: 'register', label: '主体注册审核' },
  { key: 'contact', label: '负责人变更审核' },
]
const activeMainTab = ref('register')

function onMainTabChange(key: string) {
  activeMainTab.value = key
  if (key === 'contact' && contactChanges.value.length === 0) {
    fetchContactChanges()
  }
}

// 筛选
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待审核' },
  { key: 'approved', label: '已通过' },
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
  approved: { label: '已通过', cls: 'status-approved', icon: CheckCircle2 },
  rejected: { label: '已驳回', cls: 'status-rejected', icon: XCircle },
}

// 手机号脱敏
const revealedPhones = ref<Set<number>>(new Set())

function maskPhone(phone: string, id: number): string {
  if (revealedPhones.value.has(id)) return phone
  if (phone.length >= 7) {
    return phone.slice(0, 3) + '****' + phone.slice(-4)
  }
  return phone
}

function togglePhone(id: number) {
  if (revealedPhones.value.has(id)) {
    revealedPhones.value.delete(id)
  } else {
    revealedPhones.value.add(id)
  }
}

// 指导老师联系方式脱敏
const revealedAdvisorContacts = ref<Set<number>>(new Set())

function maskAdvisorContact(contact: string, id: number): string {
  if (revealedAdvisorContacts.value.has(id)) return contact
  if (contact.length >= 7) {
    return contact.slice(0, 3) + '****' + contact.slice(-4)
  }
  return contact
}

function toggleAdvisorContact(id: number) {
  if (revealedAdvisorContacts.value.has(id)) {
    revealedAdvisorContacts.value.delete(id)
  } else {
    revealedAdvisorContacts.value.add(id)
  }
}

// 查看详情弹窗
const detailModal = ref(false)
const detailItem = ref<AuditOwnerItem | null>(null)
const detailPhoneRevealed = ref(false)

function openDetail(item: AuditOwnerItem) {
  detailItem.value = item
  detailPhoneRevealed.value = false
  detailModal.value = true
}

// 驳回弹窗
const rejectModal = ref(false)
const rejectTarget = ref<AuditOwnerItem | null>(null)
const rejectReason = ref('')
const rejectError = ref('')

function openRejectModal(item: AuditOwnerItem) {
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

async function handleApprove(item: AuditOwnerItem) {
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

// 负责人变更审核 —— 通过
const ccApprovingId = ref<number | null>(null)

async function handleCcApprove(item: ContactChangeItem) {
  ccApprovingId.value = item.id
  const ok = await approveContactChange(item.id)
  ccApprovingId.value = null
  if (ok) {
    showToast('已通过')
    fetchContactChanges()
  } else {
    showToast('操作失败，请重试')
  }
}

// 负责人变更审核 —— 驳回弹窗
const ccRejectModal = ref(false)
const ccRejectTarget = ref<ContactChangeItem | null>(null)
const ccRejectReason = ref('')
const ccRejectError = ref('')

function openCcRejectModal(item: ContactChangeItem) {
  ccRejectTarget.value = item
  ccRejectReason.value = ''
  ccRejectError.value = ''
  ccRejectModal.value = true
}

async function confirmCcReject() {
  if (ccRejectReason.value.trim().length < 2) {
    ccRejectError.value = '驳回原因至少 2 个字'
    return
  }
  if (!ccRejectTarget.value) return
  const ok = await rejectContactChange(ccRejectTarget.value.id, ccRejectReason.value.trim())
  ccRejectModal.value = false
  if (ok) {
    showToast('已驳回')
    fetchContactChanges()
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
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  fetchList('all')
})
</script>

<template>
  <div class="admin-layout">
    <AdminSidebar />

    <main class="admin-content">
      <h1 class="page-title">主体审核</h1>

      <!-- 主 Tab -->
      <div class="filter-bar">
        <button
          v-for="tab in mainTabs"
          :key="tab.key"
          class="filter-pill"
          :class="{ active: activeMainTab === tab.key }"
          @click="onMainTabChange(tab.key)"
        >{{ tab.label }}</button>
      </div>

      <!-- ===== 主体注册审核 ===== -->
      <template v-if="activeMainTab === 'register'">
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
          <p class="text-text-secondary">暂无{{ activeFilter === 'all' ? '' : filterTabs.find(t => t.key === activeFilter)?.label }}主体</p>
        </div>
      </template>

      <!-- 列表 -->
      <template v-else>
        <div class="audit-list">
          <div v-for="item in items" :key="item.id" class="audit-card">
            <!-- 头像 -->
            <div class="card-avatar">
              <img v-if="item.avatar_url" :src="item.avatar_url" alt="" class="avatar-img" />
              <Building2 v-else class="avatar-placeholder" />
            </div>

            <!-- 信息 -->
            <div class="card-body">
              <div class="card-header">
                <span class="card-title">{{ item.owner_name }}</span>
                <span class="status-tag" :class="statusMap[item.status]?.cls">
                  <component :is="statusMap[item.status]?.icon" class="w-3.5 h-3.5" />
                  {{ statusMap[item.status]?.label }}
                </span>
              </div>

              <div class="card-meta">
                <span class="meta-row">
                  <User class="w-3.5 h-3.5" />
                  账号：{{ item.account }}
                </span>
                <span class="meta-row">
                  <Building2 class="w-3.5 h-3.5" />
                  类型：{{ item.owner_type }}
                </span>
                <span class="meta-row">
                  <BookOpen class="w-3.5 h-3.5" />
                  所属：{{ item.college_name }}
                </span>
                <span class="meta-row">
                  <User class="w-3.5 h-3.5" />
                  负责人：{{ item.contact_name }}（{{ item.contact_student_id }}）
                </span>
                <span class="meta-row meta-phone" @click="togglePhone(item.id)">
                  <Phone class="w-3.5 h-3.5" />
                  手机：{{ maskPhone(item.contact_phone, item.id) }}
                  <Eye class="w-3 h-3 eye-icon" />
                </span>
                <span v-if="item.advisor_name" class="meta-row meta-phone" @click="toggleAdvisorContact(item.id)">
                  <BookOpen class="w-3.5 h-3.5" />
                  指导老师：{{ item.advisor_name }} {{ maskAdvisorContact(item.advisor_contact, item.id) }}
                  <Eye class="w-3 h-3 eye-icon" />
                </span>
                <span v-if="item.bio" class="meta-row meta-bio">
                  介绍：{{ item.bio }}
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
      <GlassModal v-model="detailModal" title="主体详情" width="480px">
        <template v-if="detailItem">
          <div class="detail-avatar-row">
            <div class="detail-avatar">
              <img v-if="detailItem.avatar_url" :src="detailItem.avatar_url" alt="" class="detail-avatar-img" />
              <Building2 v-else class="detail-avatar-placeholder" />
            </div>
            <div>
              <h3 class="detail-name">{{ detailItem.owner_name }}</h3>
              <span class="status-tag" :class="statusMap[detailItem.status]?.cls">
                <component :is="statusMap[detailItem.status]?.icon" class="w-3.5 h-3.5" />
                {{ statusMap[detailItem.status]?.label }}
              </span>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="detail-section-title">基本信息</h4>
            <div class="detail-info">
              <div class="detail-row">
                <User class="w-4 h-4" />
                <span class="detail-label">账号</span>
                <span>{{ detailItem.account }}</span>
              </div>
              <div class="detail-row">
                <Building2 class="w-4 h-4" />
                <span class="detail-label">类型</span>
                <span>{{ detailItem.owner_type }}</span>
              </div>
              <div class="detail-row">
                <BookOpen class="w-4 h-4" />
                <span class="detail-label">所属学院</span>
                <span>{{ detailItem.college_name }}</span>
              </div>
              <div v-if="detailItem.bio" class="detail-row detail-row--top">
                <BookOpen class="w-4 h-4" />
                <span class="detail-label">个性介绍</span>
                <span class="detail-bio-text">{{ detailItem.bio }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="detail-section-title">负责人信息</h4>
            <div class="detail-info">
              <div class="detail-row">
                <User class="w-4 h-4" />
                <span class="detail-label">姓名</span>
                <span>{{ detailItem.contact_name }}</span>
              </div>
              <div class="detail-row">
                <User class="w-4 h-4" />
                <span class="detail-label">学号</span>
                <span>{{ detailItem.contact_student_id }}</span>
              </div>
              <div class="detail-row meta-phone" @click="detailPhoneRevealed = !detailPhoneRevealed">
                <Phone class="w-4 h-4" />
                <span class="detail-label">手机号</span>
                <span>{{ detailPhoneRevealed ? detailItem.contact_phone : maskPhone(detailItem.contact_phone, -1) }}</span>
                <Eye class="w-3.5 h-3.5 eye-icon" />
              </div>
            </div>
          </div>

          <div v-if="detailItem.advisor_name" class="detail-section">
            <h4 class="detail-section-title">指导老师</h4>
            <div class="detail-info">
              <div class="detail-row">
                <BookOpen class="w-4 h-4" />
                <span class="detail-label">姓名</span>
                <span>{{ detailItem.advisor_name }}</span>
              </div>
              <div class="detail-row meta-phone" @click="toggleAdvisorContact(detailItem.id)">
                <Phone class="w-4 h-4" />
                <span class="detail-label">联系方式</span>
                <span>{{ maskAdvisorContact(detailItem.advisor_contact, detailItem.id) }}</span>
                <Eye class="w-3.5 h-3.5 eye-icon" />
              </div>
            </div>
          </div>

          <div v-if="detailItem.status === 'rejected' && detailItem.reject_reason" class="reject-reason">
            <XCircle class="w-4 h-4 shrink-0" />
            <span>驳回原因：{{ detailItem.reject_reason }}</span>
          </div>
        </template>

        <template #footer="{ close }">
          <template v-if="detailItem && detailItem.status === 'pending'">
            <button class="btn-approve" @click="close(); handleApprove(detailItem!)">
              <CheckCircle2 class="w-3.5 h-3.5" />
              通过
            </button>
            <button class="btn-reject" @click="close(); openRejectModal(detailItem!)">
              <XCircle class="w-3.5 h-3.5" />
              驳回
            </button>
          </template>
        </template>
      </GlassModal>

      <!-- 驳回弹窗 -->
      <GlassModal v-model="rejectModal" title="驳回主体注册" width="400px">
        <div class="reject-notice">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>驳回后申请者将收到通知，请填写具体原因。</span>
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
      </template>

      <!-- ===== 负责人变更审核 ===== -->
      <template v-if="activeMainTab === 'contact'">
        <!-- 加载骨架 -->
        <template v-if="contactChangesLoading && !contactChanges.length">
          <div class="skeleton-list">
            <div v-for="i in 3" :key="i" class="skeleton-card" />
          </div>
        </template>

        <!-- 错误 -->
        <template v-else-if="contactChangesError">
          <div class="error-card">
            <AlertTriangle class="w-8 h-8 text-danger" />
            <p class="text-text-primary font-medium">数据加载失败</p>
            <p class="text-text-secondary text-sm">{{ contactChangesError }}</p>
            <button class="btn-primary mt-4" @click="fetchContactChanges">重新加载</button>
          </div>
        </template>

        <!-- 空状态 -->
        <template v-else-if="!contactChanges.length">
          <div class="empty-state">
            <Inbox class="w-12 h-12 text-text-disabled" />
            <p class="text-text-secondary">暂无负责人变更申请</p>
          </div>
        </template>

        <!-- 列表 -->
        <template v-else>
          <div class="audit-list">
            <div v-for="item in contactChanges" :key="item.id" class="audit-card">
              <div class="card-avatar">
                <ArrowRightLeft class="avatar-placeholder" />
              </div>
              <div class="card-body">
                <div class="card-header">
                  <span class="card-title">{{ item.owner_name }}</span>
                  <span class="status-tag" :class="statusMap[item.status]?.cls">
                    <component :is="statusMap[item.status]?.icon" class="w-3.5 h-3.5" />
                    {{ statusMap[item.status]?.label }}
                  </span>
                </div>
                <div class="card-meta">
                  <span class="meta-row">
                    <User class="w-3.5 h-3.5" />
                    主体 ID：{{ item.owner_id }}
                  </span>
                  <span class="meta-row change-field">
                    <User class="w-3.5 h-3.5" />
                    负责人：{{ item.old_contact_name }}（{{ item.old_contact_student_id }}）
                    <ArrowRightLeft class="w-3 h-3" />
                    {{ item.new_contact_name }}（{{ item.new_contact_student_id }}）
                  </span>
                  <span class="meta-row change-field">
                    <Phone class="w-3.5 h-3.5" />
                    手机：{{ item.old_contact_phone }}
                    <ArrowRightLeft class="w-3 h-3" />
                    {{ item.new_contact_phone }}
                  </span>
                  <span class="meta-row">
                    <Clock class="w-3.5 h-3.5" />
                    提交时间：{{ formatDate(item.submitted_at) }}
                  </span>
                </div>
                <div class="card-actions">
                  <template v-if="item.status === 'pending'">
                    <button
                      class="btn-approve"
                      :disabled="actionLoading && ccApprovingId === item.id"
                      @click="handleCcApprove(item)"
                    >
                      <Loader2 v-if="actionLoading && ccApprovingId === item.id" class="w-3.5 h-3.5 animate-spin" />
                      <CheckCircle2 v-else class="w-3.5 h-3.5" />
                      通过
                    </button>
                    <button class="btn-reject" @click="openCcRejectModal(item)">
                      <XCircle class="w-3.5 h-3.5" />
                      驳回
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 负责人变更驳回弹窗 -->
        <GlassModal v-model="ccRejectModal" title="驳回负责人变更" width="400px">
          <div class="reject-notice">
            <AlertTriangle class="w-4 h-4 shrink-0" />
            <span>驳回后申请者将收到通知，请填写具体原因。</span>
          </div>
          <label class="reject-label">驳回原因 <span class="text-danger">*</span></label>
          <textarea
            v-model="ccRejectReason"
            class="reject-textarea"
            placeholder="至少 2 个字"
            rows="3"
          ></textarea>
          <p v-if="ccRejectError" class="reject-error">{{ ccRejectError }}</p>
          <template #footer="{ close }">
            <button class="btn-cancel" @click="close">取消</button>
            <button
              class="btn-reject"
              :disabled="actionLoading"
              @click="confirmCcReject"
            >
              <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
              确认驳回
            </button>
          </template>
        </GlassModal>
      </template>

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

/* 头像 */
.card-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  margin-top: 2px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 22px;
  height: 22px;
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

.status-approved {
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
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

.meta-bio {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.change-field {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.meta-phone {
  cursor: pointer;
  border-radius: var(--radius-sm);
  padding: 1px 4px;
  transition: background 150ms;
}

.meta-phone:hover {
  background: var(--color-surface-alt);
}

.eye-icon {
  color: var(--color-text-disabled);
  transition: color 150ms;
}

.meta-phone:hover .eye-icon {
  color: var(--color-primary);
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
.detail-avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-avatar-placeholder {
  width: 26px;
  height: 26px;
  color: var(--color-text-disabled);
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border);
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
}

.detail-row--top {
  align-items: flex-start;
}

.detail-row svg {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.detail-label {
  color: var(--color-text-secondary);
  min-width: 64px;
  flex-shrink: 0;
}

.detail-bio-text {
  white-space: pre-wrap;
  line-height: 1.5;
}

.detail-row.meta-phone {
  cursor: pointer;
  border-radius: var(--radius-sm);
  padding: 2px 4px;
  margin: -2px -4px;
  transition: background 150ms;
}

.detail-row.meta-phone:hover {
  background: var(--color-surface-alt);
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
  height: 160px;
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
