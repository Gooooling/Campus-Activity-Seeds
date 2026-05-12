<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import {
  Search,
  ScrollText,
  Inbox,
  Loader2,
  AlertTriangle,
  X,
  Filter,
  Globe,
  User,
  Clock,
  Tag,
  FileText,
} from 'lucide-vue-next'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'
import { useLogs } from '@/composables/useLogs'

const {
  items, loading, error, total, hasMore,
  operatorFilter, actionTypeFilter, dateFrom, dateTo, actionTypes,
  fetchList, loadMore, retry, resetFilters,
} = useLogs()

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout>
const searchInput = ref('')
watch(searchInput, (val) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    operatorFilter.value = val
    fetchList()
  }, 400)
})

function onActionTypeChange(e: Event) {
  actionTypeFilter.value = (e.target as HTMLSelectElement).value
  fetchList()
}

function onDateFromChange(e: Event) {
  dateFrom.value = (e.target as HTMLInputElement).value
  fetchList()
}

function onDateToChange(e: Event) {
  dateTo.value = (e.target as HTMLInputElement).value
  fetchList()
}

// 格式化日期时间
function formatDateTime(iso: string) {
  const d = new Date(iso)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}

// 操作类型中文映射
const operationLabelMap: Record<string, string> = {
  create_user: '创建账号',
  reset_password: '重置密码',
  approve_activity: '通过活动',
  reject_activity: '驳回活动',
  delete_activity: '删除活动',
  approve_owner: '通过主体',
  reject_owner: '驳回主体',
  approve_contact_change: '通过负责人变更',
  reject_contact_change: '驳回负责人变更',
  post_announcement: '发布公告',
  create_announcement: '发布公告',
  delete_announcement: '删除公告',
  toggle_user_status: '禁用/启用用户',
  login: '登录',
  participate: '参与活动',
  favorite: '收藏',
  create_activity: '发布活动',
  update_activity: '编辑活动',
  update_profile: '修改资料',
  create_banner: '创建轮播图',
  update_banner: '更新轮播图',
  delete_banner: '删除轮播图',
}

// 操作类型颜色映射（用英文key）
const actionColorMap: Record<string, string> = {
  create_user: 'bg-accent/10 text-accent',
  reset_password: 'bg-accent/10 text-accent',
  approve_activity: 'bg-success/10 text-success',
  reject_activity: 'bg-danger/10 text-danger',
  delete_activity: 'bg-danger/10 text-danger',
  approve_owner: 'bg-success/10 text-success',
  reject_owner: 'bg-danger/10 text-danger',
  post_announcement: 'bg-primary/10 text-primary',
  delete_announcement: 'bg-danger/10 text-danger',
  toggle_user_status: 'bg-info/10 text-info',
  login: 'bg-surface-alt text-text-secondary',
  participate: 'bg-success/10 text-success',
  favorite: 'bg-primary/10 text-primary',
  create_activity: 'bg-secondary/10 text-secondary',
  update_activity: 'bg-info/10 text-info',
  update_profile: 'bg-surface-alt text-text-secondary',
  create_banner: 'bg-primary/10 text-primary',
  update_banner: 'bg-info/10 text-info',
  delete_banner: 'bg-danger/10 text-danger',
}

function getOperationLabel(op: string) {
  return operationLabelMap[op] || op
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
        <ScrollText class="w-6 h-6" />
        操作日志
      </h1>
      <p class="page-subtitle">只读审计日志，记录系统所有操作行为</p>

      <!-- 筛选栏 -->
      <div class="toolbar">
        <div class="toolbar-filters">
          <div class="search-box">
            <User class="search-icon" />
            <input
              v-model="searchInput"
              class="search-input"
              type="text"
              placeholder="搜索操作人"
            />
            <button v-if="searchInput" class="search-clear" @click="searchInput = ''">
              <X class="w-3.5 h-3.5" />
            </button>
          </div>
          <select class="filter-select" :value="actionTypeFilter" @change="onActionTypeChange">
            <option v-for="opt in actionTypes" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <div class="date-range">
            <input
              class="date-input"
              type="date"
              :value="dateFrom"
              @change="onDateFromChange"
            />
            <span class="date-sep">至</span>
            <input
              class="date-input"
              type="date"
              :value="dateTo"
              @change="onDateToChange"
            />
          </div>
          <button class="btn-reset" @click="resetFilters">
            <Filter class="w-3.5 h-3.5" />
            重置
          </button>
        </div>
        <span class="total-hint" v-if="total > 0">共 {{ total }} 条记录</span>
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
          <p class="text-text-secondary">暂无操作日志</p>
        </div>
      </template>

      <!-- 日志表格 -->
      <template v-else>
        <div class="table-wrap">
          <table class="log-table">
            <thead>
              <tr>
                <th class="th-time">时间</th>
                <th>操作人</th>
                <th>操作类型</th>
                <th>目标对象</th>
                <th class="th-detail">详情</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <td class="cell-time">{{ formatDateTime(item.created_at) }}</td>
                <td>
                  <span class="cell-operator">{{ item.user_name }}</span>
                </td>
                <td>
                  <span class="action-tag" :class="actionColorMap[item.operation] || 'bg-surface-alt text-text-secondary'">
                    {{ getOperationLabel(item.operation) }}
                  </span>
                </td>
                <td>
                  <span class="cell-target-type">{{ item.target_type }}</span>
                  <span class="cell-target-id">#{{ item.target_id }}</span>
                </td>
                <td class="cell-detail">{{ item.detail || '-' }}</td>
                <td class="cell-ip">{{ item.ip_address }}</td>
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

/* ── 筛选栏 ── */
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
  width: 180px;
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

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  transition: border-color 150ms;
}

.date-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.date-sep {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.btn-reset {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 150ms;
}

.btn-reset:hover { background: var(--color-surface-alt); }

.total-hint {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* ── 日志表格 ── */
.table-wrap {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  table-layout: auto;
}

.log-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-surface-alt);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.log-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
  vertical-align: middle;
}

.log-table tr:last-child td {
  border-bottom: none;
}

.log-table tr:hover td {
  background: rgba(59, 130, 246, 0.02);
}

.th-time { width: 120px; }
.th-detail { min-width: 180px; }

.cell-time {
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.cell-operator {
  font-weight: 500;
  color: var(--color-text-primary);
}

.action-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.cell-target-type {
  font-weight: 500;
  color: var(--color-text-primary);
}

.cell-target-id {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-left: 4px;
}

.cell-detail {
  font-size: 13px;
  color: var(--color-text-secondary);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-ip {
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
  font-size: 12px;
  color: var(--color-text-disabled);
  white-space: nowrap;
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

/* ── 通用按钮 ── */
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

/* ── 减少动效 ── */
@media (prefers-reduced-motion: reduce) {
  .skeleton-table { animation: none; }
}
</style>
