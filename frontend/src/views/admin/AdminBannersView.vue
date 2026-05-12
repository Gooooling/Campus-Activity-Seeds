<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import {
  Image,
  Plus,
  Trash2,
  Inbox,
  Loader2,
  AlertTriangle,
  Pencil,
  Upload,
  X,
  GripVertical,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { request } from '@/utils/request'

interface AdminBannerItem {
  id: number
  title: string
  subtitle: string
  image_url: string
  sort_order: number
  is_active: boolean
  created_at: string
}

// ── 列表数据 ──
const items = ref<AdminBannerItem[]>([])
const loading = ref(false)
const error = ref('')
const actionLoading = ref(false)

const sortedItems = computed(() =>
  [...items.value].sort((a, b) => a.sort_order - b.sort_order),
)

async function fetchList() {
  loading.value = true
  error.value = ''
  try {
    const res = await request<AdminBannerItem[]>('/admin/banners')
    if (res.code === 200 || res.code === 0) {
      items.value = res.data ?? []
    } else {
      error.value = res.message || '加载失败'
    }
  } catch (e: any) {
    error.value = e.message || '网络异常'
  } finally {
    loading.value = false
  }
}

// ── 新增/编辑表单 ──
const formModal = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const form = ref({
  title: '',
  subtitle: '',
  image_url: '',
  sort_order: 0,
  is_active: true,
})
const formError = ref('')
const uploading = ref(false)

function openAddModal() {
  isEdit.value = false
  editId.value = null
  form.value = { title: '', subtitle: '', image_url: '', sort_order: items.value.length, is_active: true }
  formError.value = ''
  formModal.value = true
}

function openEditModal(item: AdminBannerItem) {
  isEdit.value = true
  editId.value = item.id
  form.value = {
    title: item.title,
    subtitle: item.subtitle,
    image_url: item.image_url,
    sort_order: item.sort_order,
    is_active: item.is_active,
  }
  formError.value = ''
  formModal.value = true
}

async function handleSubmit() {
  if (!form.value.title.trim()) {
    formError.value = '标题不能为空'
    return
  }
  if (!form.value.image_url) {
    formError.value = '请上传轮播图图片'
    return
  }

  actionLoading.value = true
  formError.value = ''
  try {
    const body: Record<string, any> = {
      title: form.value.title.trim(),
      image_url: form.value.image_url,
      sort_order: form.value.sort_order,
      is_active: form.value.is_active,
    }
    if (form.value.subtitle.trim()) {
      body.subtitle = form.value.subtitle.trim()
    }

    let res
    if (isEdit.value && editId.value !== null) {
      res = await request(`/admin/banners/${editId.value}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      })
    } else {
      res = await request('/admin/banners', {
        method: 'POST',
        body: JSON.stringify(body),
      })
    }

    if (res.code === 200 || res.code === 0) {
      formModal.value = false
      showToast(isEdit.value ? '轮播图已更新' : '轮播图已添加')
      await fetchList()
    } else {
      formError.value = res.message || '操作失败'
    }
  } catch (e: any) {
    formError.value = e.message || '网络异常'
  } finally {
    actionLoading.value = false
  }
}

// ── 图片上传 ──
const fileInput = ref<HTMLInputElement | null>(null)

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    formError.value = '请选择图片文件'
    target.value = ''
    return
  }

  uploading.value = true
  formError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('type', 'activity_image')
    const res = await request<{ url: string }>('/upload', {
      method: 'POST',
      body: fd,
    })
    if ((res.code === 200 || res.code === 0) && res.data?.url) {
      form.value.image_url = res.data.url
    } else {
      formError.value = res.message || '图片上传失败'
    }
  } catch (e: any) {
    formError.value = e.message || '图片上传异常'
  } finally {
    uploading.value = false
    target.value = ''
  }
}

function removeImage() {
  form.value.image_url = ''
}

// ── 启用/禁用切换 ──
async function toggleActive(item: AdminBannerItem) {
  actionLoading.value = true
  try {
    const res = await request(`/admin/banners/${item.id}`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: !item.is_active }),
    })
    if (res.code === 200 || res.code === 0) {
      showToast(item.is_active ? '已禁用' : '已启用')
      await fetchList()
    } else {
      showToast(res.message || '操作失败')
    }
  } catch (e: any) {
    showToast(e.message || '网络异常')
  } finally {
    actionLoading.value = false
  }
}

// ── 删除 ──
const deleteModal = ref(false)
const deleteTarget = ref<AdminBannerItem | null>(null)

function openDeleteModal(item: AdminBannerItem) {
  deleteTarget.value = item
  deleteModal.value = true
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  actionLoading.value = true
  try {
    const res = await request(`/admin/banners/${deleteTarget.value.id}`, {
      method: 'DELETE',
    })
    if (res.code === 200 || res.code === 0) {
      showToast('轮播图已删除')
    } else {
      showToast(res.message || '删除失败')
    }
  } catch (e: any) {
    showToast(e.message || '网络异常')
  } finally {
    actionLoading.value = false
    deleteModal.value = false
  }
}

// ── Toast ──
const toastVisible = ref(false)
const toastMsg = ref('')
let toastTimer: ReturnType<typeof setTimeout>

function showToast(msg: string) {
  toastMsg.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2000)
}

// ── 格式化日期 ──
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
      <div class="page-header">
        <div>
          <h1 class="page-title">
            <Image class="w-6 h-6" />
            轮播图管理
          </h1>
          <p class="page-subtitle">管理首页轮播图，支持排序、启用/禁用</p>
        </div>
        <button class="btn-primary" @click="openAddModal">
          <Plus class="w-4 h-4" />
          新增轮播图
        </button>
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
          <p class="text-text-secondary">暂无轮播图</p>
          <button class="btn-primary mt-2" @click="openAddModal">
            <Plus class="w-4 h-4" />
            添加第一张轮播图
          </button>
        </div>
      </template>

      <!-- 列表 -->
      <template v-else>
        <div class="banner-list">
          <div
            v-for="item in sortedItems"
            :key="item.id"
            class="banner-item"
            :class="{ inactive: !item.is_active }"
          >
            <!-- 缩略图 -->
            <div class="banner-thumb">
              <img v-if="item.image_url" :src="item.image_url" :alt="item.title" />
              <Image v-else class="w-6 h-6 text-text-disabled" />
            </div>

            <!-- 信息 -->
            <div class="banner-body">
              <div class="banner-title-row">
                <span class="banner-title">{{ item.title }}</span>
                <span class="badge" :class="item.is_active ? 'badge-active' : 'badge-inactive'">
                  {{ item.is_active ? '启用' : '禁用' }}
                </span>
              </div>
              <p v-if="item.subtitle" class="banner-subtitle">{{ item.subtitle }}</p>
              <div class="banner-meta">
                <GripVertical class="w-3 h-3" />
                <span>排序: {{ item.sort_order }}</span>
                <span class="meta-sep">|</span>
                <span>{{ formatDate(item.created_at) }}</span>
              </div>
            </div>

            <!-- 操作 -->
            <div class="banner-actions">
              <label class="toggle-wrap" :title="item.is_active ? '点击禁用' : '点击启用'">
                <input
                  type="checkbox"
                  class="toggle-input"
                  :checked="item.is_active"
                  :disabled="actionLoading"
                  @change="toggleActive(item)"
                />
                <span class="toggle-slider" />
              </label>
              <button
                class="btn-icon"
                title="编辑"
                :disabled="actionLoading"
                @click="openEditModal(item)"
              >
                <Pencil class="w-4 h-4" />
              </button>
              <button
                class="btn-icon btn-icon-danger"
                title="删除"
                :disabled="actionLoading"
                @click="openDeleteModal(item)"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </template>

      <!-- 新增/编辑弹窗 -->
      <GlassModal v-model="formModal" :title="isEdit ? '编辑轮播图' : '新增轮播图'" width="520px" :close-on-overlay="false">
        <div class="form-group">
          <label class="form-label">标题 <span class="text-danger">*</span></label>
          <input
            v-model="form.title"
            class="form-input"
            type="text"
            placeholder="请输入轮播图标题"
            maxlength="50"
          />
        </div>
        <div class="form-group">
          <label class="form-label">副标题</label>
          <input
            v-model="form.subtitle"
            class="form-input"
            type="text"
            placeholder="可选，显示在标题下方"
            maxlength="100"
          />
        </div>
        <div class="form-group">
          <label class="form-label">轮播图图片 <span class="text-danger">*</span></label>
          <div class="upload-area">
            <div v-if="form.image_url" class="upload-preview">
              <img :src="form.image_url" alt="预览" />
              <button class="upload-remove" @click="removeImage">
                <X class="w-3.5 h-3.5" />
              </button>
            </div>
            <button v-else class="upload-btn" :disabled="uploading" @click="triggerUpload">
              <Loader2 v-if="uploading" class="w-5 h-5 animate-spin text-primary" />
              <Upload v-else class="w-5 h-5 text-text-secondary" />
              <span class="upload-text">{{ uploading ? '上传中...' : '点击上传图片' }}</span>
            </button>
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden-input"
              @change="handleFileChange"
            />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group flex-1">
            <label class="form-label">排序</label>
            <input
              v-model.number="form.sort_order"
              class="form-input"
              type="number"
              min="0"
              placeholder="数字越小越靠前"
            />
          </div>
          <div class="form-group">
            <label class="form-label">状态</label>
            <label class="toggle-wrap">
              <input v-model="form.is_active" type="checkbox" class="toggle-input" />
              <span class="toggle-slider" />
              <span class="toggle-label">{{ form.is_active ? '启用' : '禁用' }}</span>
            </label>
          </div>
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <template #footer="{ close }">
          <button class="btn-cancel" @click="close">取消</button>
          <button
            class="btn-primary"
            :disabled="actionLoading || uploading"
            @click="handleSubmit"
          >
            <Loader2 v-if="actionLoading" class="w-3.5 h-3.5 animate-spin" />
            {{ isEdit ? '保存修改' : '确认添加' }}
          </button>
        </template>
      </GlassModal>

      <!-- 删除确认弹窗 -->
      <GlassModal v-model="deleteModal" title="删除轮播图" width="360px">
        <div class="delete-confirm">
          <AlertTriangle class="w-10 h-10 text-danger" />
          <p class="font-medium text-text-primary">确定删除轮播图「{{ deleteTarget?.title }}」？</p>
          <p class="text-sm text-text-secondary">删除后无法恢复，首页将不再展示该轮播图。</p>
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

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
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
}

/* ── 轮播图列表 ── */
.banner-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.banner-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 16px;
  transition: box-shadow 150ms, opacity 150ms;
}

.banner-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.banner-item.inactive {
  opacity: 0.6;
}

.banner-thumb {
  width: 120px;
  height: 68px;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.banner-body {
  flex: 1;
  min-width: 0;
}

.banner-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.banner-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.banner-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.banner-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-disabled);
}

.meta-sep {
  opacity: 0.4;
}

/* ── 状态标签 ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.badge-active {
  background: rgba(34, 197, 94, 0.12);
  color: #16a34a;
}

.badge-inactive {
  background: rgba(148, 163, 184, 0.12);
  color: #94a3b8;
}

/* ── 操作按钮 ── */
.banner-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 150ms;
}

.btn-icon:hover {
  background: var(--color-bg);
  border-color: var(--color-border);
}

.btn-icon-danger:hover {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
}

.btn-icon:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ── Toggle 开关 ── */
.toggle-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.toggle-input {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 36px;
  height: 20px;
  background: var(--color-border);
  border-radius: 999px;
  transition: background 200ms;
  flex-shrink: 0;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  transition: transform 200ms;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.toggle-input:checked + .toggle-slider {
  background: var(--color-primary);
}

.toggle-input:checked + .toggle-slider::after {
  transform: translateX(16px);
}

.toggle-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

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

.text-danger {
  color: var(--color-danger);
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  transition: border-color 150ms;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.form-error {
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 4px;
}

/* ── 图片上传 ── */
.upload-area {
  width: 100%;
}

.upload-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 140px;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  cursor: pointer;
  transition: border-color 150ms, background 150ms;
}

.upload-btn:hover {
  border-color: var(--color-primary);
  background: rgba(59, 130, 246, 0.04);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.upload-preview {
  position: relative;
  width: 100%;
  max-height: 180px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.upload-preview img {
  width: 100%;
  height: auto;
  max-height: 180px;
  object-fit: contain;
  display: block;
  background: var(--color-bg);
}

.upload-remove {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: background 150ms;
}

.upload-remove:hover {
  background: rgba(239, 68, 68, 0.8);
}

.hidden-input {
  display: none;
}

/* ── 删除确认 ── */
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
