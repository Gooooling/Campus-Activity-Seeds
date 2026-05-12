<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import {
  Search,
  Plus,
  User,
  Building2,
  Shield,
  Eye,
  Ban,
  CheckCircle2,
  KeyRound,
  Inbox,
  Loader2,
  AlertTriangle,
  X,
  Copy,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useAdminUsers } from '@/composables/useAdminUsers'
import { useAuthStore } from '@/stores/auth'
import type { AdminUserItem } from '@/types/activity'

const authStore = useAuthStore()
const {
  items, loading, error, total, hasMore, actionLoading,
  keyword, roleFilter, statusFilter,
  fetchList, loadMore, createUser, toggleStatus, resetPassword, retry,
} = useAdminUsers()

const isSuperAdmin = computed(() => authStore.isSuperAdmin)

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

// 筛选
function onRoleChange(e: Event) {
  roleFilter.value = (e.target as HTMLSelectElement).value
  fetchList()
}

function onStatusChange(e: Event) {
  statusFilter.value = (e.target as HTMLSelectElement).value
  fetchList()
}

// 角色显示
const roleMap: Record<string, { label: string; cls: string }> = {
  student:        { label: '学生',   cls: 'role-student' },
  activity_owner: { label: '主体',   cls: 'role-owner' },
  admin:          { label: '管理员', cls: 'role-admin' },
  super_admin:    { label: '超管',   cls: 'role-super' },
}

// 状态显示
const userStatusMap: Record<string, { label: string; cls: string }> = {
  active:   { label: '正常', cls: 'ustatus-active' },
  disabled: { label: '禁用', cls: 'ustatus-disabled' },
}

// 创建账号弹窗
const createModal = ref(false)
const newRole = ref('student')
const newAccount = ref('')
const newName = ref('')
const createError = ref('')
const createdPassword = ref('')
const showCreatedResult = ref(false)

const roleOptions = computed(() => {
  const base = [
    { key: 'student', label: '学生' },
    { key: 'activity_owner', label: '活动主体' },
  ]
  if (isSuperAdmin.value) {
    base.push({ key: 'admin', label: '管理员' })
  }
  return base
})

function openCreateModal() {
  newRole.value = 'student'
  newAccount.value = ''
  newName.value = ''
  createError.value = ''
  createdPassword.value = ''
  showCreatedResult.value = false
  createModal.value = true
}

async function handleCreate() {
  if (!newAccount.value.trim() || !newName.value.trim()) {
    createError.value = '账号和姓名不能为空'
    return
  }
  const result = await createUser(newRole.value, newAccount.value.trim(), newName.value.trim())
  if (result.ok) {
    createdPassword.value = result.password || '（已生成）'
    showCreatedResult.value = true
    fetchList()
  } else {
    createError.value = result.msg || '创建失败'
  }
}

// 用户详情弹窗
const detailModal = ref(false)
const detailItem = ref<AdminUserItem | null>(null)

function openDetail(item: AdminUserItem) {
  detailItem.value = item
  detailModal.value = true
}

// 禁用/启用
async function handleToggleStatus(item: AdminUserItem) {
  const enable = item.status === 'disabled'
  const ok = await toggleStatus(item.user_id, enable)
  if (ok) {
    showToast(enable ? '已启用' : '已禁用')
    fetchList()
    if (detailItem.value?.user_id === item.user_id) {
      detailItem.value = { ...detailItem.value, status: enable ? 'active' : 'disabled' }
    }
  } else {
    showToast('操作失败')
  }
}

// 重置密码
const resetModal = ref(false)
const resetTarget = ref<AdminUserItem | null>(null)
const resetPasswordResult = ref('')

async function openResetModal(item: AdminUserItem) {
  resetTarget.value = item
  resetPasswordResult.value = ''
  resetModal.value = true
}

async function confirmReset() {
  if (!resetTarget.value) return
  const result = await resetPassword(resetTarget.value.user_id)
  if (result.ok) {
    resetPasswordResult.value = result.password || '（已生成）'
  } else {
    showToast(result.msg || '重置失败')
    resetModal.value = false
  }
}

// 复制密码
function copyPassword(pwd: string) {
  navigator.clipboard.writeText(pwd).then(() => {
    showToast('已复制到剪贴板')
  }).catch(() => {
    showToast('复制失败，请手动复制')
  })
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
  fetchList()
})
</script>

<template>
  <div class="admin-layout">
    <AdminSidebar />

    <main class="admin-content">
      <h1 class="page-title">用户管理</h1>

      <!-- 工具栏 -->
      <div class="toolbar">
        <button class="btn-create" @click="openCreateModal">
          <Plus class="w-4 h-4" />
          创建账号
        </button>
        <div class="toolbar-filters">
          <div class="search-box">
            <Search class="search-icon" />
            <input
              v-model="searchInput"
              class="search-input"
              type="text"
              placeholder="搜索学号 / 姓名 / 账号"
            />
            <button v-if="searchInput" class="search-clear" @click="searchInput = ''">
              <X class="w-3.5 h-3.5" />
            </button>
          </div>
          <select class="filter-select" :value="roleFilter" @change="onRoleChange">
            <option value="all">全部角色</option>
            <option value="student">学生</option>
            <option value="activity_owner">活动主体</option>
            <option v-if="isSuperAdmin" value="admin">管理员</option>
            <option v-if="isSuperAdmin" value="super_admin">超管</option>
          </select>
          <select class="filter-select" :value="statusFilter" @change="onStatusChange">
            <option value="all">全部状态</option>
            <option value="active">正常</option>
            <option value="disabled">禁用</option>
          </select>
        </div>
      </div>

      <!-- 加载骨架 -->
      <template v-if="loading && !items.length">
        <div class="skeleton-table" />
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
          <p class="text-text-secondary">暂无匹配的用户</p>
        </div>
      </template>

      <!-- 用户表格 -->
      <template v-else>
        <div class="table-wrap">
          <table class="user-table">
            <thead>
              <tr>
                <th>姓名 / 主体</th>
                <th>账号</th>
                <th>角色</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.user_id">
                <td>
                  <div class="cell-name">
                    <div class="cell-avatar">
                      <img v-if="item.avatar_url" :src="item.avatar_url" alt="" class="cell-avatar-img" />
                      <User v-else class="cell-avatar-icon" />
                    </div>
                    <div>
                      <span class="name-text">{{ item.name }}</span>
                      <span class="name-college">{{ item.college_name }}</span>
                    </div>
                  </div>
                </td>
                <td><span class="cell-account">{{ item.account }}</span></td>
                <td>
                  <span class="role-tag" :class="roleMap[item.role]?.cls">
                    {{ roleMap[item.role]?.label }}
                  </span>
                </td>
                <td>
                  <span class="status-tag" :class="userStatusMap[item.status]?.cls">
                    {{ userStatusMap[item.status]?.label }}
                  </span>
                </td>
                <td>
                  <button class="btn-text" @click="openDetail(item)">
                    <Eye class="w-3.5 h-3.5" />
                    详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
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

      <!-- 创建账号弹窗 -->
      <GlassModal v-model="createModal" title="新建账号" width="400px">
        <div v-if="showCreatedResult" class="create-result">
          <CheckCircle2 class="w-10 h-10 text-success" />
          <p class="font-medium text-text-primary">账号创建成功</p>
          <p class="text-sm text-text-secondary">请将初始密码通知用户，首次登录需强制修改</p>
          <div class="password-box">
            <span class="password-text">{{ createdPassword }}</span>
            <button class="copy-btn" @click="copyPassword(createdPassword)">
              <Copy class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <template v-else>
          <div class="form-group">
            <label class="form-label">角色 <span class="text-danger">*</span></label>
            <select v-model="newRole" class="form-select">
              <option v-for="opt in roleOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">账号 / 学号 <span class="text-danger">*</span></label>
            <input v-model="newAccount" class="form-input" type="text" placeholder="请输入账号或学号" />
          </div>

          <div class="form-group">
            <label class="form-label">姓名 / 主体名 <span class="text-danger">*</span></label>
            <input v-model="newName" class="form-input" type="text" placeholder="请输入姓名或主体名称" />
          </div>

          <div class="form-hint">
            <KeyRound class="w-3.5 h-3.5" />
            初始密码系统自动生成，首次登录强制修改
          </div>

          <p v-if="createError" class="form-error">{{ createError }}</p>
        </template>

        <template #footer="{ close }">
          <button v-if="showCreatedResult" class="btn-primary" @click="close">知道了</button>
          <template v-else>
            <button class="btn-cancel" @click="close">取消</button>
            <button
              class="btn-primary"
              :disabled="actionLoading"
              @click="handleCreate"
            >
              <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
              创建
            </button>
          </template>
        </template>
      </GlassModal>

      <!-- 用户详情弹窗 -->
      <GlassModal v-model="detailModal" title="用户详情" width="400px">
        <template v-if="detailItem">
          <div class="detail-avatar-row">
            <div class="detail-avatar">
              <img v-if="detailItem.avatar_url" :src="detailItem.avatar_url" alt="" class="detail-avatar-img" />
              <User v-else class="detail-avatar-icon" />
            </div>
            <div>
              <h3 class="detail-name">{{ detailItem.name }}</h3>
              <span class="role-tag" :class="roleMap[detailItem.role]?.cls">
                {{ roleMap[detailItem.role]?.label }}
              </span>
            </div>
          </div>

          <div class="detail-info">
            <div class="detail-row">
              <User class="w-4 h-4" />
              <span class="detail-label">账号</span>
              <span>{{ detailItem.account }}</span>
            </div>
            <div class="detail-row">
              <Building2 class="w-4 h-4" />
              <span class="detail-label">学院</span>
              <span>{{ detailItem.college_name }}</span>
            </div>
            <div class="detail-row">
              <Shield class="w-4 h-4" />
              <span class="detail-label">状态</span>
              <span class="status-tag" :class="userStatusMap[detailItem.status]?.cls">
                {{ userStatusMap[detailItem.status]?.label }}
              </span>
            </div>
          </div>

          <div class="detail-actions">
            <button
              v-if="detailItem.status === 'active'"
              class="btn-disable"
              :disabled="actionLoading"
              @click="detailModal = false; handleToggleStatus(detailItem!)"
            >
              <Ban class="w-3.5 h-3.5" />
              禁用账号
            </button>
            <button
              v-else
              class="btn-enable"
              :disabled="actionLoading"
              @click="detailModal = false; handleToggleStatus(detailItem!)"
            >
              <CheckCircle2 class="w-3.5 h-3.5" />
              启用账号
            </button>
            <button
              class="btn-reset-pwd"
              :disabled="actionLoading"
              @click="detailModal = false; openResetModal(detailItem!)"
            >
              <KeyRound class="w-3.5 h-3.5" />
              重置密码
            </button>
          </div>
        </template>
      </GlassModal>

      <!-- 重置密码弹窗 -->
      <GlassModal v-model="resetModal" title="重置密码" width="400px">
        <div v-if="!resetPasswordResult">
          <p class="text-text-primary text-sm">
            确定要重置「{{ resetTarget?.name }}」的密码吗？
          </p>
          <p class="text-text-secondary text-sm mt-2">
            密码将重置为系统随机生成，用户下次登录需强制修改。
          </p>
        </div>
        <div v-else class="create-result">
          <CheckCircle2 class="w-10 h-10 text-success" />
          <p class="font-medium text-text-primary">密码重置成功</p>
          <p class="text-sm text-text-secondary">请将新密码通知用户</p>
          <div class="password-box">
            <span class="password-text">{{ resetPasswordResult }}</span>
            <button class="copy-btn" @click="copyPassword(resetPasswordResult)">
              <Copy class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <template #footer="{ close }">
          <template v-if="!resetPasswordResult">
            <button class="btn-cancel" @click="close">取消</button>
            <button
              class="btn-primary"
              :disabled="actionLoading"
              @click="confirmReset"
            >
              <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
              确认重置
            </button>
          </template>
          <button v-else class="btn-primary" @click="close">知道了</button>
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
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.toolbar-filters {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.btn-create {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 150ms;
}

.btn-create:hover { background: var(--color-primary-hover); }

.search-box {
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
  width: 220px;
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

.search-clear:hover { background: var(--color-surface-alt); }

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

/* ── 用户表格 ── */
.table-wrap {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.user-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-surface-alt);
  border-bottom: 1px solid var(--color-border);
}

.user-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
  vertical-align: middle;
}

.user-table tr:last-child td {
  border-bottom: none;
}

.user-table tr:hover td {
  background: rgba(59, 130, 246, 0.02);
}

/* 单元格样式 */
.cell-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cell-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cell-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cell-avatar-icon {
  width: 16px;
  height: 16px;
  color: var(--color-text-disabled);
}

.name-text {
  display: block;
  font-weight: 500;
  color: var(--color-text-primary);
}

.name-college {
  display: block;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.cell-account {
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 角色标签 */
.role-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-student { background: rgba(59, 130, 246, 0.1); color: #1D4ED8; }
.role-owner   { background: rgba(14, 165, 233, 0.1); color: #0369A1; }
.role-admin   { background: rgba(245, 158, 11, 0.1); color: #B45309; }
.role-super   { background: rgba(239, 68, 68, 0.1);  color: #B91C1C; }

/* 状态标签 */
.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.ustatus-active   { background: rgba(16, 185, 129, 0.1); color: #047857; }
.ustatus-disabled { background: rgba(239, 68, 68, 0.1);  color: #B91C1C; }

/* 操作按钮 */
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

.btn-text:hover { background: var(--color-primary-light); }

/* ── 创建弹窗 ── */
.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  transition: border-color 150ms;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.form-select {
  width: 100%;
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

.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.form-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.form-error {
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 4px;
}

/* 创建结果 */
.create-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  padding: 12px 0;
}

.password-box {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 14px;
  background: var(--color-surface-alt);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--color-border);
}

.password-text {
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 1px;
}

.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 150ms;
}

.copy-btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

/* ── 详情弹窗 ── */
.detail-avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-avatar {
  width: 48px;
  height: 48px;
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

.detail-avatar-icon {
  width: 22px;
  height: 22px;
  color: var(--color-text-disabled);
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
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
  min-width: 48px;
}

.detail-actions {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.btn-disable {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  background: var(--color-danger);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 150ms;
}

.btn-disable:hover { opacity: 0.9; }
.btn-disable:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-enable {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  background: var(--color-success);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: opacity 150ms;
}

.btn-enable:hover { opacity: 0.9; }
.btn-enable:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-reset-pwd {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
  background: none;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 150ms;
}

.btn-reset-pwd:hover { background: var(--color-primary-light); }
.btn-reset-pwd:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── 通用按钮 ── */
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

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 150ms;
}

.btn-primary:hover { background: var(--color-primary-hover); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

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

.skeleton-table {
  height: 300px;
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
  .skeleton-table { animation: none; }
  .toast-enter-active,
  .toast-leave-active { transition: none; }
}
</style>
