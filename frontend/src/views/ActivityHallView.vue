<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search,
  List,
  Calendar,
  ArrowUpDown,
  Filter,
  Inbox,
  X,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Clock,
} from 'lucide-vue-next'
import ActivityCard from '@/components/common/ActivityCard.vue'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { fetchPublicConfig } from '@/composables/useSystemConfig'
import type { ActivityListItem } from '@/types/activity'

const router = useRouter()
const authStore = useAuthStore()

// 视图模式
 type ViewMode = 'list' | 'calendar'
const viewMode = ref<ViewMode>('list')

// 搜索
const keyword = ref('')
const searchInput = ref('')

// 筛选条件
const creditType = ref('')
const activityType = ref('')
const deadlineFilter = ref('')

// 排序
const sortBy = ref<'deadline_asc' | 'deadline_desc' | 'created_desc'>('deadline_asc')

// 分页
const page = ref(1)
const pageSize = 12
const total = ref(0)
const activities = ref<ActivityListItem[]>([])
const loading = ref(false)
const hasMore = computed(() => activities.value.length < total.value)

// 移动端筛选弹窗
const showFilterModal = ref(false)

// 筛选选项
const configData = ref<{ credit_types: string[]; activity_types: string[] }>({
  credit_types: [],
  activity_types: [],
})
const deadlineFilters = [
  { value: '', label: '全部时间' },
  { value: 'today', label: '今天截止' },
  { value: 'week', label: '本周截止' },
  { value: 'later', label: '下周及以后' },
  { value: 'expired', label: '已过期' },
]

const sortOptions = [
  { value: 'deadline_asc' as const, label: '截止由近到远' },
  { value: 'deadline_desc' as const, label: '截止由远到近' },
  { value: 'created_desc' as const, label: '最新发布' },
]

// 是否正在筛选
const isFiltering = computed(() => creditType.value || activityType.value || deadlineFilter.value)

// 加载活动列表
async function loadActivities(reset = false) {
  if (loading.value) return
  loading.value = true

  if (reset) {
    page.value = 1
    activities.value = []
  }

  try {
    const params = new URLSearchParams()
    params.set('page', String(page.value))
    params.set('page_size', String(pageSize))
    params.set('sort_by', sortBy.value)
    if (creditType.value) params.set('credit_type', creditType.value)
    if (activityType.value) params.set('activity_type', activityType.value)
    if (deadlineFilter.value) params.set('deadline_filter', deadlineFilter.value)
    if (keyword.value) params.set('keyword', keyword.value)

    const data = await request(`/activities?${params.toString()}`)

    if (data.code === 200) {
      if (reset) {
        activities.value = data.data.items
      } else {
        activities.value.push(...data.data.items)
      }
      total.value = data.data.total
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 搜索（防抖）
let searchTimer: ReturnType<typeof setTimeout> | null = null
function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    keyword.value = searchInput.value
    loadActivities(true)
  }, 400)
}

function clearSearch() {
  searchInput.value = ''
  keyword.value = ''
  loadActivities(true)
}

// 筛选变更
function applyFilter() {
  showFilterModal.value = false
  loadActivities(true)
  if (viewMode.value === 'calendar') {
    loadCalendarActivities()
  }
}

function resetFilters() {
  creditType.value = ''
  activityType.value = ''
  deadlineFilter.value = ''
  sortBy.value = 'deadline_asc'
  loadActivities(true)
}

// 排序切换
function toggleSort() {
  const order: Array<'deadline_asc' | 'deadline_desc' | 'created_desc'> = ['deadline_asc', 'deadline_desc', 'created_desc']
  const idx = order.indexOf(sortBy.value)
  sortBy.value = order[(idx + 1) % order.length]
  loadActivities(true)
}

// 加载更多
function loadMore() {
  page.value++
  loadActivities()
}

// 点击活动卡片
function handleActivityClick(id: number) {
  router.push(`/activities/${id}`)
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

// 当前排序标签
const currentSortLabel = computed(() => {
  return sortOptions.find(o => o.value === sortBy.value)?.label || '排序'
})

// ── 日历视图逻辑 ──
const now = new Date()
const calendarYear = ref(now.getFullYear())
const calendarMonth = ref(now.getMonth()) // 0-indexed
const selectedDate = ref<string | null>(null) // 'YYYY-MM-DD'
const calendarActivities = ref<ActivityListItem[]>([])
const calendarLoading = ref(false)

// 星期标题（周一起始，符合中国习惯）
const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']

// 当月日历网格（6行 x 7列，填充前后空白）
const calendarDays = computed(() => {
  const year = calendarYear.value
  const month = calendarMonth.value
  const firstDay = new Date(year, month, 1)
  // 获取当月1号是周几（0=周日，1=周一...），转换为周一起始的偏移
  let startWeekday = firstDay.getDay() // 0=Sun
  startWeekday = startWeekday === 0 ? 6 : startWeekday - 1 // 转为周一=0...周日=6

  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const daysInPrevMonth = new Date(year, month, 0).getDate()

  const days: Array<{ date: number; monthOffset: -1 | 0 | 1; dateStr: string }> = []

  // 前月填充
  for (let i = startWeekday - 1; i >= 0; i--) {
    const d = daysInPrevMonth - i
    const m = month - 1
    const actualMonth = m < 0 ? 11 : m
    const actualYear = m < 0 ? year - 1 : year
    days.push({ date: d, monthOffset: -1, dateStr: formatDateStr(actualYear, actualMonth, d) })
  }

  // 当月日期
  for (let d = 1; d <= daysInMonth; d++) {
    days.push({ date: d, monthOffset: 0, dateStr: formatDateStr(year, month, d) })
  }

  // 后月填充（补齐到 42 格 = 6 行）
  const remaining = 42 - days.length
  for (let d = 1; d <= remaining; d++) {
    const m = month + 1
    const actualMonth = m > 11 ? 0 : m
    const actualYear = m > 11 ? year + 1 : year
    days.push({ date: d, monthOffset: 1, dateStr: formatDateStr(actualYear, actualMonth, d) })
  }

  return days
})

function formatDateStr(year: number, month: number, day: number): string {
  const m = String(month + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  return `${year}-${m}-${d}`
}

// 按日期分组活动（key: 'YYYY-MM-DD'）
const activitiesByDate = computed(() => {
  const map = new Map<string, ActivityListItem[]>()
  for (const act of calendarActivities.value) {
    const deadlineDate = act.registration_deadline.slice(0, 10) // 'YYYY-MM-DD'
    if (!map.has(deadlineDate)) {
      map.set(deadlineDate, [])
    }
    map.get(deadlineDate)!.push(act)
  }
  // 每个日期内的活动按截止时刻排序
  for (const [, list] of map) {
    list.sort((a, b) => new Date(a.registration_deadline).getTime() - new Date(b.registration_deadline).getTime())
  }
  return map
})

// 选中日期的活动列表
const selectedDateActivities = computed(() => {
  if (!selectedDate.value) return []
  return activitiesByDate.value.get(selectedDate.value) || []
})

// 月份标题
const calendarTitle = computed(() => {
  return `${calendarYear.value}年 ${calendarMonth.value + 1}月`
})

// 判断日期是否为今天
function isToday(dateStr: string): boolean {
  const today = new Date()
  const todayStr = formatDateStr(today.getFullYear(), today.getMonth(), today.getDate())
  return dateStr === todayStr
}

// 判断日期是否已过期（今天之前的日期）
function isDateExpired(dateStr: string): boolean {
  const today = new Date()
  const todayStr = formatDateStr(today.getFullYear(), today.getMonth(), today.getDate())
  return dateStr < todayStr
}

// 获取某日期的活动数量
function getDateActivityCount(dateStr: string): number {
  return activitiesByDate.value.get(dateStr)?.length || 0
}

// 获取某日期最早截止时刻（HH:MM）
function getEarliestDeadlineTime(dateStr: string): string {
  const acts = activitiesByDate.value.get(dateStr)
  if (!acts || acts.length === 0) return ''
  return formatDeadlineTime(acts[0].registration_deadline)
}

// 月份切换
function prevMonth() {
  if (calendarMonth.value === 0) {
    calendarMonth.value = 11
    calendarYear.value--
  } else {
    calendarMonth.value--
  }
  selectedDate.value = null
  loadCalendarActivities()
}

function nextMonth() {
  if (calendarMonth.value === 11) {
    calendarMonth.value = 0
    calendarYear.value++
  } else {
    calendarMonth.value++
  }
  selectedDate.value = null
  loadCalendarActivities()
}

// 点击日期
function selectDate(dateStr: string, monthOffset: number) {
  if (monthOffset === -1) { prevMonth(); return }
  if (monthOffset === 1) { nextMonth(); return }
  if (selectedDate.value === dateStr) {
    selectedDate.value = null
  } else {
    selectedDate.value = dateStr
    // 移动端点击日期后自动滚到详情区
    if (!isDesktop.value) {
      setTimeout(() => {
        calendarSideRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    }
  }
}

// 格式化截止时刻为 HH:mm
function formatDeadlineTime(deadline: string): string {
  const d = new Date(deadline)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 格式化选中日期标题
function formatSelectedDateTitle(dateStr: string): string {
  const parts = dateStr.split('-')
  return `${parseInt(parts[1])}月${parseInt(parts[2])}日截止报名的活动`
}

const calendarSideRef = ref<HTMLElement | null>(null)
const isDesktop = ref(window.innerWidth >= 768)

function onResize() { isDesktop.value = window.innerWidth >= 768 }

// 加载日历数据
async function loadCalendarActivities() {
  calendarLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('page', '1')
    params.set('page_size', '50')
    params.set('sort_by', 'deadline_asc')
    if (creditType.value) params.set('credit_type', creditType.value)
    if (activityType.value) params.set('activity_type', activityType.value)
    if (deadlineFilter.value) params.set('deadline_filter', deadlineFilter.value)
    if (keyword.value) params.set('keyword', keyword.value)

    const data = await request(`/activities?${params.toString()}`)

    if (data.code === 200) {
      calendarActivities.value = data.data.items
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    calendarLoading.value = false
  }
}

// 切换到日历视图时加载数据
watch(viewMode, (mode) => {
  if (mode === 'calendar' && calendarActivities.value.length === 0) {
    loadCalendarActivities()
  }
})

// 监听筛选条件变化（桌面端直接触发）
watch([creditType, activityType, deadlineFilter], () => {
  if (!showFilterModal.value) {
    loadActivities(true)
    if (viewMode.value === 'calendar') {
      loadCalendarActivities()
    }
  }
})

onMounted(async () => {
  const config = await fetchPublicConfig()
  configData.value = {
    credit_types: config.credit_types,
    activity_types: config.activity_types,
  }
  loadActivities(true)
  window.addEventListener('resize', onResize)
})
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<template>
  <div class="activity-hall">
    <!-- 顶部搜索区 -->
    <div class="hall-header">
      <div class="search-box">
        <Search class="search-icon" />
        <input
          v-model="searchInput"
          type="text"
          placeholder="搜索活动名称..."
          class="search-input"
          @input="handleSearchInput"
        />
        <button v-if="searchInput" class="search-clear" @click="clearSearch">
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 筛选+排序+视图切换栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <!-- 移动端：综合筛选按钮 -->
        <button class="filter-btn" :class="{ active: isFiltering }" @click="showFilterModal = true">
          <Filter class="w-4 h-4" />
          <span>筛选</span>
          <span v-if="isFiltering" class="filter-dot" />
        </button>

        <!-- 桌面端：单独筛选下拉 -->
        <div class="hidden md:flex md:items-center md:gap-2">
          <select v-model="creditType" class="filter-select">
            <option value="">学分类型</option>
            <option v-for="t in configData.credit_types" :key="t" :value="t">{{ t }}</option>
          </select>
          <select v-model="activityType" class="filter-select">
            <option value="">活动类型</option>
            <option v-for="t in configData.activity_types" :key="t" :value="t">{{ t }}</option>
          </select>
          <select v-model="deadlineFilter" class="filter-select">
            <option v-for="f in deadlineFilters" :key="f.value" :value="f.value">{{ f.label }}</option>
          </select>
        </div>
      </div>

      <div class="filter-right">
        <button class="sort-btn" @click="toggleSort">
          <ArrowUpDown class="w-4 h-4" />
          <span class="hidden sm:inline">{{ currentSortLabel }}</span>
        </button>

        <!-- 视图切换 -->
        <div class="view-toggle">
          <button
            class="view-btn"
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
          >
            <List class="w-4 h-4" />
          </button>
          <button
            class="view-btn"
            :class="{ active: viewMode === 'calendar' }"
            @click="viewMode = 'calendar'"
          >
            <Calendar class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-if="viewMode === 'list'" class="list-view">
      <!-- 空状态 -->
      <div v-if="!loading && activities.length === 0" class="empty-state">
        <Inbox class="w-12 h-12 text-text-disabled mb-4" />
        <p class="empty-title">暂无相关活动</p>
        <p class="empty-desc">试试调整筛选条件或搜索关键词</p>
        <button v-if="isFiltering || keyword" class="reset-btn" @click="resetFilters(); clearSearch()">
          重置筛选
        </button>
      </div>

      <!-- 活动卡片网格 -->
      <div v-else class="activity-grid">
        <ActivityCard
          v-for="activity in activities"
          :key="activity.id"
          :data="activity"
          show-favorite
          show-location
          @click="handleActivityClick"
          @favorite="handleFavorite"
        />
      </div>

      <!-- 加载更多 -->
      <div v-if="activities.length > 0" class="load-more">
        <button
          v-if="hasMore && !loading"
          class="load-more-btn"
          @click="loadMore"
        >
          加载更多
        </button>
        <div v-if="loading" class="loading-indicator">
          <Loader2 class="w-5 h-5 animate-spin text-primary" />
          <span>加载中...</span>
        </div>
        <p v-if="!hasMore && !loading" class="no-more">
          已加载全部 {{ total }} 个活动
        </p>
      </div>
    </div>

    <!-- 日历视图 -->
    <div v-else class="calendar-view">
      <!-- 加载状态 -->
      <div v-if="calendarLoading" class="calendar-loading">
        <Loader2 class="w-6 h-6 animate-spin text-primary" />
        <span>加载日历数据...</span>
      </div>

      <div class="calendar-layout">
        <!-- 左侧/上方：日历卡片 -->
        <div class="calendar-card">
          <div class="calendar-nav">
            <button class="calendar-nav-btn" @click="prevMonth" aria-label="上一月">
              <ChevronLeft class="w-5 h-5" />
            </button>
            <span class="calendar-title">{{ calendarTitle }}</span>
            <button class="calendar-nav-btn" @click="nextMonth" aria-label="下一月">
              <ChevronRight class="w-5 h-5" />
            </button>
          </div>

          <div class="calendar-weekdays">
            <div v-for="label in weekdayLabels" :key="label" class="calendar-weekday">
              {{ label }}
            </div>
          </div>

          <div class="calendar-grid">
            <button
              v-for="(day, idx) in calendarDays"
              :key="idx"
              class="calendar-day"
              :class="{
                'other-month': day.monthOffset !== 0,
                'is-today': isToday(day.dateStr),
                'is-selected': selectedDate === day.dateStr,
                'is-expired': day.monthOffset === 0 && isDateExpired(day.dateStr),
                'has-activities': day.monthOffset === 0 && getDateActivityCount(day.dateStr) > 0,
              }"
              @click="selectDate(day.dateStr, day.monthOffset)"
            >
              <span class="day-number">{{ day.date }}</span>
              <div v-if="day.monthOffset === 0 && getDateActivityCount(day.dateStr) > 0" class="day-dots">
                <span class="day-dot" />
                <span v-if="getDateActivityCount(day.dateStr) >= 2" class="day-dot" />
              </div>
            </button>
          </div>
        </div>

        <!-- 右侧/下方：选中日期的活动列表 -->
        <div ref="calendarSideRef" class="calendar-side">
          <div v-if="selectedDate" class="calendar-detail">
            <div class="detail-header">
              <Calendar class="w-4 h-4 text-primary" />
              <span class="detail-title">{{ formatSelectedDateTitle(selectedDate) }}</span>
              <span class="detail-count">{{ selectedDateActivities.length }}个活动</span>
            </div>

            <div v-if="selectedDateActivities.length === 0" class="detail-empty">
              该日期暂无截止活动
            </div>

            <div v-else class="detail-list">
              <button
                v-for="act in selectedDateActivities"
                :key="act.id"
                class="detail-item"
                @click="handleActivityClick(act.id)"
              >
                <div class="detail-cover">
                  <img
                    v-if="act.cover_image_url"
                    :src="act.cover_image_url"
                    :alt="act.title"
                    class="detail-cover-img"
                    loading="lazy"
                  />
                  <div v-else class="detail-cover-placeholder">
                    <Calendar class="w-5 h-5 text-text-disabled" />
                  </div>
                </div>

                <div class="detail-info">
                  <span class="detail-name">{{ act.title }}</span>
                  <div class="detail-meta">
                    <span class="detail-time">
                      <Clock class="w-3.5 h-3.5" />
                      {{ formatDeadlineTime(act.registration_deadline) }}前
                    </span>
                    <span class="detail-credit-tag">{{ act.credit_type }} {{ act.credit_value ?? '-' }}分</span>
                  </div>
                </div>

                <ChevronRight class="w-4 h-4 text-text-disabled shrink-0" />
              </button>
            </div>
          </div>

          <div v-else class="calendar-hint">
            <p>点击有活动标记的日期，查看当天截止的活动</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 移动端筛选弹窗 -->
    <div v-if="showFilterModal" class="filter-modal-overlay" @click="showFilterModal = false">
      <div class="filter-modal" @click.stop>
        <div class="filter-modal-header">
          <h3>筛选条件</h3>
          <button class="close-btn" @click="showFilterModal = false">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="filter-modal-body">
          <div class="filter-group">
            <label class="filter-group-label">学分类型</label>
            <div class="filter-options">
              <button
                class="filter-option"
                :class="{ active: creditType === '' }"
                @click="creditType = ''"
              >
                全部
              </button>
              <button
                v-for="t in configData.credit_types"
                :key="t"
                class="filter-option"
                :class="{ active: creditType === t }"
                @click="creditType = t"
              >
                {{ t }}
              </button>
            </div>
          </div>

          <div class="filter-group">
            <label class="filter-group-label">活动类型</label>
            <div class="filter-options">
              <button
                class="filter-option"
                :class="{ active: activityType === '' }"
                @click="activityType = ''"
              >
                全部
              </button>
              <button
                v-for="t in configData.activity_types"
                :key="t"
                class="filter-option"
                :class="{ active: activityType === t }"
                @click="activityType = t"
              >
                {{ t }}
              </button>
            </div>
          </div>

          <div class="filter-group">
            <label class="filter-group-label">截止时间</label>
            <div class="filter-options">
              <button
                v-for="f in deadlineFilters"
                :key="f.value"
                class="filter-option"
                :class="{ active: deadlineFilter === f.value }"
                @click="deadlineFilter = f.value"
              >
                {{ f.label }}
              </button>
            </div>
          </div>

          <div class="filter-group">
            <label class="filter-group-label">排序方式</label>
            <div class="filter-options">
              <button
                v-for="o in sortOptions"
                :key="o.value"
                class="filter-option"
                :class="{ active: sortBy === o.value }"
                @click="sortBy = o.value"
              >
                {{ o.label }}
              </button>
            </div>
          </div>
        </div>

        <div class="filter-modal-footer">
          <button class="btn-secondary" @click="resetFilters">重置</button>
          <button class="btn-primary" @click="applyFilter">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.activity-hall {
  min-height: calc(100dvh - 64px);
  padding: 16px;
  max-width: 1280px;
  margin: 0 auto;
}
@media (min-width: 768px) {
  .activity-hall {
    padding: 24px 32px;
  }
}

/* 搜索框 */
.hall-header {
  margin-bottom: 16px;
}
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: #94A3B8;
  pointer-events: none;
}
.search-input {
  width: 100%;
  height: 44px;
  padding: 0 40px 0 42px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 15px;
  color: #1E293B;
  transition: all 150ms ease;
}
.search-input::placeholder {
  color: #94A3B8;
}
.search-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}
.search-clear {
  position: absolute;
  right: 10px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  border-radius: 6px;
}
.search-clear:hover {
  background: #F1F5F9;
  color: #64748B;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.filter-left,
.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 14px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  color: #1E293B;
  transition: all 150ms ease;
  position: relative;
}
.filter-btn:hover {
  border-color: #3B82F6;
}
.filter-btn.active {
  border-color: #3B82F6;
  color: #3B82F6;
}
.filter-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 6px;
  height: 6px;
  background: var(--color-danger);
  border-radius: 50%;
}

.filter-select {
  height: 36px;
  padding: 0 28px 0 12px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  color: #1E293B;
  cursor: pointer;
  transition: all 150ms ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
}
.filter-select:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.sort-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 12px;
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  color: #64748B;
  transition: all 150ms ease;
}
.sort-btn:hover {
  border-color: #3B82F6;
  color: #3B82F6;
}

.view-toggle {
  display: flex;
  background: #F1F5F9;
  padding: 3px;
  border-radius: 8px;
  gap: 2px;
}
.view-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #64748B;
  transition: all 150ms ease;
}
.view-btn.active {
  background: white;
  color: #3B82F6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 活动网格 */
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
@media (min-width: 1024px) {
  .activity-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
}

/* 加载更多 */
.load-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 24px;
  margin-bottom: 32px;
  gap: 12px;
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
  padding: 64px 24px;
  text-align: center;
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
.reset-btn {
  padding: 8px 20px;
  background: #F1F5F9;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  transition: all 150ms ease;
}
.reset-btn:hover {
  background: #E2E8F0;
}

/* 日历视图 */
.calendar-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.calendar-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
@media (min-width: 768px) {
  .calendar-layout {
    flex-direction: row;
    align-items: flex-start;
  }
  .calendar-card {
    flex: 0 0 auto;
    width: 420px;
  }
  .calendar-side {
    flex: 1;
    min-width: 0;
  }
}

.calendar-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px 24px;
  font-size: 14px;
  color: #64748B;
}

.calendar-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  padding: 16px;
}

.calendar-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.calendar-nav-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #64748B;
  transition: all 150ms ease;
}
.calendar-nav-btn:hover {
  background: #F1F5F9;
  color: #1E293B;
}

.calendar-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 4px;
}

.calendar-weekday {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #94A3B8;
  padding: 8px 0;
  user-select: none;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.calendar-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2px;
  min-height: 40px;
  border-radius: 8px;
  transition: all 150ms ease;
  cursor: pointer;
  gap: 1px;
}
.calendar-day:hover:not(.other-month) {
  background: #F1F5F9;
}

.calendar-day.other-month {
  cursor: pointer;
}
.calendar-day.other-month .day-number {
  color: #CBD5E1;
}

.calendar-day.is-today .day-number {
  border: 2px solid #3B82F6;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.calendar-day.is-selected {
  background: #3B82F6;
}
.calendar-day.is-selected .day-number {
  color: white;
  font-weight: 600;
}
.calendar-day.is-selected.is-today .day-number {
  border-color: white;
}
.calendar-day.is-selected .day-dot {
  background: rgba(255, 255, 255, 0.7);
}

.calendar-day.is-expired .day-number {
  color: #94A3B8;
}
.calendar-day.is-expired {
  cursor: pointer;
}
.calendar-day.is-expired:hover {
  background: #F1F5F9;
}

.day-number {
  font-size: 15px;
  color: #1E293B;
  line-height: 1;
  user-select: none;
}

.day-dots {
  display: flex;
  gap: 3px;
  margin-top: 2px;
}

.day-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #3B82F6;
  transition: background 150ms ease;
}


/* 日历详情：选中日期的活动列表 */
.calendar-detail {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  border-bottom: 1px solid #F1F5F9;
}

.detail-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}

.detail-count {
  font-size: 12px;
  color: #94A3B8;
  margin-left: auto;
}

.detail-empty {
  padding: 32px 20px;
  text-align: center;
  font-size: 14px;
  color: #94A3B8;
}

.detail-list {
  display: flex;
  flex-direction: column;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  text-align: left;
  transition: background 150ms ease;
  border-bottom: 1px solid #F1F5F9;
}
.detail-item:last-child {
  border-bottom: none;
}
.detail-item:hover {
  background: #F8FAFC;
}

.detail-cover {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #F1F5F9;
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
}

.detail-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-name {
  font-size: 14px;
  font-weight: 500;
  color: #1E293B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748B;
}

.detail-credit-tag {
  font-size: 11px;
  font-weight: 500;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  padding: 1px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.calendar-hint {
  text-align: center;
  padding: 24px 16px;
  font-size: 14px;
  color: #94A3B8;
}

/* 日历视图响应式 */
@media (min-width: 768px) {
  .calendar-card {
    padding: 20px;
  }
  .calendar-day {
    min-height: 46px;
  }
  .day-number {
    font-size: 15px;
  }
  .detail-item {
    padding: 14px 20px;
  }
}

/* 筛选弹窗 */
.filter-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.filter-modal {
  width: 100%;
  max-width: 380px;
  background: white;
  border-radius: 14px;
  max-height: 75dvh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  animation: fadeIn 200ms ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}

.filter-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #F1F5F9;
}
.filter-modal-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}
.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  border-radius: 8px;
}
.close-btn:hover {
  background: #F1F5F9;
}

.filter-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-group-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 6px;
}
.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.filter-option {
  padding: 6px 14px;
  background: #F1F5F9;
  border-radius: 8px;
  font-size: 13px;
  color: #64748B;
  transition: all 150ms ease;
}
.filter-option.active {
  background: #3B82F6;
  color: white;
}

.filter-modal-footer {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #F1F5F9;
}
.filter-modal-footer .btn-secondary,
.filter-modal-footer .btn-primary {
  flex: 1;
  height: 38px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 150ms ease;
}
.filter-modal-footer .btn-secondary {
  background: #F1F5F9;
  color: #64748B;
}
.filter-modal-footer .btn-secondary:hover {
  background: #E2E8F0;
}
.filter-modal-footer .btn-primary {
  background: #3B82F6;
  color: white;
}
.filter-modal-footer .btn-primary:hover {
  background: #2563EB;
}

/* 通用按钮 */
.btn-primary {
  padding: 10px 20px;
  background: #3B82F6;
  color: white;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 150ms ease;
}
.btn-primary:hover {
  background: #2563EB;
}
.btn-secondary {
  padding: 10px 20px;
  background: #F1F5F9;
  color: #64748B;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 150ms ease;
}
.btn-secondary:hover {
  background: #E2E8F0;
}

/* 动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>