<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  Megaphone,
  Plus,
  Trash2,
  Inbox,
  Loader2,
  AlertTriangle,
  Send,
  X,
  Clock,
  MessageSquare,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useAnnouncements } from '@/composables/useAnnouncements'

const {
  items, loading, error, actionLoading,
  fetchList, create, remove,
} = useAnnouncements()

// 发布公告
const publishModal = ref(false)
const content = ref('')
const publishError = ref('')

function openPublishModal() {
  content.value = ''
  publishError.value = ''
  publishModal.value = true
}

async function handlePublish() {
  if (!content.value.trim()) {
    publishError.value = '公告内容不能为空'
    return
  }
  if (content.value.trim().length < 2) {
    publishError.value = '公告内容至少 2 个字'
    return
  }
  const ok = await create(content.value.trim())
  if (ok) {
    publishModal.value = false
    showToast('公告发布成功')
  } else {
    publishError.value = '发布失败，请稍后重试'
  }
}

// 删除公告
const deleteModal = ref(false)
const deleteTarget = ref<number | null>(null)

function openDeleteModal(id: number) {
  deleteTarget.value = id
  deleteModal.value = true
}

async function confirmDelete() {
  if (deleteTarget.value === null) return
  const ok = await remove(deleteTarget.value)
  if (ok) {
    showToast('公告已删除')
  } else {
    showToast('删除失败')
  }
  deleteModal.value = false
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

// 格式化日期
function formatDate(iso: string) {
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// 内容摘要（超过80字截断）
function excerpt(text: string, max = 80) {
  if (text.length <= max) return text
  return text.slice(0, max) + '...'
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="admin-layout">
    <AdminSidebar />

    <main class="admin-content">
      <h1 class="page-title">
        <Megaphone class="w-6 h-6" />
        公告管理
      </h1>
      <p class="page-subtitle">发布公告后全站登录用户将收到红点提醒</p>

      <!-- 发布区 -->
      <div class="publish-card">
        <div class="publish-header">
          <MessageSquare class="w-5 h-5 text-primary" />
          <span class="publish-title">发布公告</span>
        </div>
        <textarea
          v-model="content"
          class="publish-textarea"
          rows="4"
          placeholder="请输入公告内容..."
        />
        <div class="publish-footer">
          <span class="publish-hint">发布后全站推送，请谨慎措辞</span>
          <button
            class="btn-primary"
            :disabled="actionLoading || !content.trim()"
            @click="handlePublish"
          >
            <Send class="w-4 h-4" />
            发布
          </button>
        </div>
        <p v-if="publishError" class="form-error">{{ publishError }}</p>
      </div>

      <!-- 公告列表 -->
      <div class="list-header">
        <h2 class="list-title">公告列表</h2>
        <span v-if="items.length" class="list-count">共 {{ items.length }} 条</span>
      </div>

      <!-- 加载骨架 -->
      <template v-if="loading && !items.length">
        <div class="skeleton-list" />
      </template>

      <!-- 错误 -->
      <template v-else-if="error">
        <div class="error-card">
          <AlertTriangle class="w-8 h-8 text-danger" />
          <p class="text-text-primary font-medium">数据加载失败</p>
          <p class="text-text-secondary text-sm">{{ error }}</p>
          <button class="btn-primary mt-4" @click="fetchList">重新加载</button>
        </div>
      </template>

      <!-- 空状态 -->
      <template v-else-if="!items.length">
        <div class="empty-state">
          <Inbox class="w-12 h-12 text-text-disabled" />
          <p class="text-text-secondary">暂无公告</p>
        </div>
      </template>

      <!-- 列表 -->
      <template v-else>
        <div class="announcement-list">
          <div
            v-for="item in items"
            :key="item.id"
            class="announcement-item"
          >
            <div class="item-icon">
              <Megaphone class="w-4 h-4 text-primary" />
            </div>
            <div class="item-body">
              <p class="item-content">{{ item.content }}</p>
              <div class="item-meta">
                <Clock class="w-3 h-3" />
                <span>{{ formatDate(item.created_at) }}</span>
              </div>
            </div>
            <button
              class="btn-delete"
              :disabled="actionLoading"
              @click="openDeleteModal(item.id)"
            >
              <Trash2 class="w-4 h-4" />
              删除
            </button>
          </div>
        </div>
      </template>

      <!-- 发布确认弹窗（备用，实际直接发布） -->
      <GlassModal v-model="publishModal" title="发布公告" width="480px">
        <div class="form-group">
          <label class="form-label">公告内容</label>
          <textarea
            v-model="content"
            class="form-textarea"
            rows="5"
            placeholder="请输入公告内容..."
          />
        </div>
        <p v-if="publishError" class="form-error">{{ publishError }}</p>
        <template #footer="{ close }">
          <button class="btn-cancel" @click="close">取消</button>
          <button
            class="btn-primary"
            :disabled="actionLoading"
            @click="handlePublish"
          >
            <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
            确认发布
          </button>
        </template>
      </GlassModal>

      <!-- 删除确认弹窗 -->
      <GlassModal v-model="deleteModal" title="删除公告" width="360px">
        <div class="delete-confirm">
          <AlertTriangle class="w-10 h-10 text-danger" />
          <p class="font-medium text-text-primary">确定删除这条公告？</p>
          <p class="text-sm text-text-secondary">删除后无法恢复，用户消息中心中的该公告记录也将消失。</p>
        </div>
        <template #footer="{ close }">
          <button class="btn-cancel" @click="close">取消</button>
          <button
            class="btn-danger"
            :disabled="actionLoading"
            @click="confirmDelete"
          >
            <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
            确认删除
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

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 20px;
}

/* ── 发布卡片 ── */
.publish-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
  margin-bottom: 24px;
}

.publish-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.publish-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.publish-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
  background: var(--color-bg);
  resize: vertical;
  min-height: 96px;
  transition: border-color 150ms;
  font-family: inherit;
}

.publish-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.publish-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.publish-hint {
  font-size: 12px;
  color: var(--color-text-disabled);
}

/* ── 列表标题 ── */
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.list-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.list-count {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* ── 公告列表 ── */
.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 16px;
  transition: box-shadow 150ms;
}

.announcement-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.item-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.item-body {
  flex: 1;
  min-width: 0;
}

.item-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.btn-delete {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--color-danger);
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 150ms;
  flex-shrink: 0;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
}

.btn-delete:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── 弹窗表单 ── */
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

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
  background: var(--color-surface);
  resize: vertical;
  min-height: 100px;
  font-family: inherit;
  transition: border-color 150ms;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.form-error {
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 4px;
}

.delete-confirm {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  padding: 8px 0;
}

/* ── 通用按钮 ── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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

.btn-danger {
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

.btn-danger:hover { opacity: 0.9; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }

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

.skeleton-list {
  height: 200px;
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
  .skeleton-list { animation: none; }
  .toast-enter-active,
  .toast-leave-active { transition: none; }
}
</style>
