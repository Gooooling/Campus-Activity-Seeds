<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  User,
  Handshake,
  GraduationCap,
  Heart,
  CalendarDays,
  PenLine,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ChevronRight,
  QrCode,
  Lock,
  Eye,
  EyeOff,
  ChevronLeft,
  Image as ImageIcon,
  RefreshCw,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { useColleges } from '@/composables/useColleges'
import GlassModal from '@/components/common/GlassModal.vue'
import ParticipationCard from '@/components/common/ParticipationCard.vue'
import ActivityCard from '@/components/common/ActivityCard.vue'
import type {
  ParticipationItem,
  CreditSummary,
  StudentProfile,
  ActivityListItem,
} from '@/types/activity'

const router = useRouter()
const authStore = useAuthStore()

type TabKey = 'participations' | 'credits' | 'favorites' | 'calendar' | 'profile'

const activeTab = ref<TabKey>('participations')
const tabs: { key: TabKey; label: string; icon: typeof Handshake }[] = [
  { key: 'participations', label: '我的参与', icon: Handshake },
  { key: 'credits', label: '我的学分', icon: GraduationCap },
  { key: 'favorites', label: '我的收藏', icon: Heart },
  { key: 'calendar', label: '活动日历', icon: CalendarDays },
  { key: 'profile', label: '编辑资料', icon: PenLine },
]

// ── 用户信息 ──
const userProfile = ref<StudentProfile | null>(null)
const loading = ref(true)

async function fetchProfile() {
  if (!authStore.isLoggedIn) return
  loading.value = true
  try {
    const data = await request('/users/me')
    if (data.code === 200) {
      userProfile.value = data.data
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// ── 我的参与 ──
const participationFilter = ref<'all' | 'active' | 'ended'>('all')
const participations = ref<ParticipationItem[]>([])
const participationsLoading = ref(false)
const showQrcodeModal = ref(false)
const qrcodeItem = ref<ParticipationItem | null>(null)

async function fetchParticipations() {
  if (!authStore.isLoggedIn) return
  participationsLoading.value = true
  try {
    const status = participationFilter.value === 'all' ? 'all' : participationFilter.value
    const data = await request(`/participations/my?status=${status}`)
    if (data.code === 200) {
      participations.value = data.data.items ?? []
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    participationsLoading.value = false
  }
}

function onViewQrcode(item: ParticipationItem) {
  qrcodeItem.value = item
  showQrcodeModal.value = true
}

function onViewMemento(activityId: number) {
  router.push(`/participations/${activityId}/memento`)
}

function onParticipationClick(activityId: number) {
  router.push(`/activities/${activityId}`)
}

async function onCancelParticipation(item: ParticipationItem) {
  try {
    const data = await request(`/participations/${item.id}`, { method: 'DELETE' })
    if (data.code === 200) {
      ElMessage.success('已取消参与')
      await fetchParticipations()
    } else {
      ElMessage.error(data.message || '取消失败')
    }
  } catch {
    ElMessage.error('网络错误，请稍后重试')
  }
}

watch(participationFilter, () => fetchParticipations())

// ── 我的学分 ──
const creditSummary = ref<CreditSummary | null>(null)
const creditsLoading = ref(false)

async function fetchCredits() {
  if (!authStore.isLoggedIn) return
  creditsLoading.value = true
  try {
    const data = await request('/credits/summary')
    if (data.code === 200) {
      creditSummary.value = data.data
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    creditsLoading.value = false
  }
}

function getProgressPercent(current: number, required: number): number {
  if (required === 0) return 100
  return Math.min(Math.round((current / required) * 100), 100)
}

function getProgressWidth(current: number, required: number): number {
  if (required === 0) return 100
  return Math.min((current / required) * 100, 100)
}

// ── 我的收藏 ──
const favorites = ref<ActivityListItem[]>([])
const favoritesLoading = ref(false)

async function fetchFavorites() {
  if (!authStore.isLoggedIn) return
  favoritesLoading.value = true
  try {
    const data = await request('/favorites/my')
    if (data.code === 200) {
      favorites.value = data.data.items ?? []
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    favoritesLoading.value = false
  }
}

function isFavoriteExpired(item: ActivityListItem): boolean {
  return new Date(item.registration_deadline).getTime() < Date.now()
}

async function toggleFavorite(id: number) {
  if (!authStore.isLoggedIn) return
  try {
    const data = await request('/favorites', {
      method: 'POST',
      body: JSON.stringify({ activity_id: id }),
    })
    if (data.code === 200) {
      await fetchFavorites()
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

function goActivityDetail(id: number) {
  router.push(`/activities/${id}`)
}

// ── 我的活动日历 ──
const calendarYear = ref(new Date().getFullYear())
const calendarMonth = ref(new Date().getMonth())
const selectedDate = ref<number | null>(null)
const calendarParticipations = ref<ParticipationItem[]>([])

const calendarWeekDays = ['一', '二', '三', '四', '五', '六', '日']

const calendarDays = computed(() => {
  const y = calendarYear.value
  const m = calendarMonth.value
  const firstDay = new Date(y, m, 1)
  let startWeekday = firstDay.getDay()
  startWeekday = startWeekday === 0 ? 6 : startWeekday - 1

  const daysInMonth = new Date(y, m + 1, 0).getDate()
  const days: (number | null)[] = []
  for (let i = 0; i < startWeekday; i++) days.push(null)
  for (let d = 1; d <= daysInMonth; d++) days.push(d)
  return days
})

const activityDates = computed(() => {
  const dates = new Set<number>()
  for (const item of calendarParticipations.value) {
    const d = new Date(item.start_time)
    if (d.getFullYear() === calendarYear.value && d.getMonth() === calendarMonth.value) {
      dates.add(d.getDate())
    }
  }
  return dates
})

const selectedDateActivities = computed(() => {
  if (selectedDate.value === null) return []
  const y = calendarYear.value
  const m = calendarMonth.value
  const d = selectedDate.value
  return calendarParticipations.value.filter(item => {
    const date = new Date(item.start_time)
    return date.getFullYear() === y && date.getMonth() === m && date.getDate() === d
  })
})

function prevMonth() {
  if (calendarMonth.value === 0) {
    calendarMonth.value = 11
    calendarYear.value--
  } else {
    calendarMonth.value--
  }
  selectedDate.value = null
}

function nextMonth() {
  if (calendarMonth.value === 11) {
    calendarMonth.value = 0
    calendarYear.value++
  } else {
    calendarMonth.value++
  }
  selectedDate.value = null
}

function selectDate(day: number | null) {
  if (day === null || !activityDates.value.has(day)) return
  selectedDate.value = selectedDate.value === day ? null : day
}

async function fetchCalendarData() {
  if (!authStore.isLoggedIn) return
  try {
    const data = await request('/participations/my?status=all')
    if (data.code === 200) {
      calendarParticipations.value = data.data.items ?? []
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

function formatCalendarTime(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
}

function formatCalendarEndTime(item: ParticipationItem): string {
  const s = new Date(item.start_time)
  return `${s.getHours()}:${s.getMinutes().toString().padStart(2, '0')}`
}

// ── 编辑资料 ──
const profileForm = ref({
  name: '',
  college_id: null as number | null,
  phone: '',
  email: '',
})
const { colleges, fetchColleges } = useColleges()
const showPasswordForm = ref(false)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const profileMsg = ref({ type: '' as 'success' | 'error', text: '' })
const passwordMsg = ref({ type: '' as 'success' | 'error', text: '' })
const profileSaving = ref(false)
const passwordSaving = ref(false)
const showOldPwd = ref(false)
const showNewPwd = ref(false)
const showConfirmPwd = ref(false)

function initProfileForm() {
  if (userProfile.value) {
    profileForm.value.name = userProfile.value.name
    profileForm.value.college_id = userProfile.value.college_id
    profileForm.value.phone = userProfile.value.phone || ''
    profileForm.value.email = userProfile.value.email || ''
  }
}

async function saveProfile() {
  if (!authStore.isLoggedIn) return
  profileSaving.value = true
  profileMsg.value = { type: '', text: '' }
  try {
    const data = await request('/users/me', {
      method: 'PUT',
      body: JSON.stringify(profileForm.value),
    })
    if (data.code === 200) {
      profileMsg.value = { type: 'success', text: '保存成功' }
      await fetchProfile()
    } else {
      profileMsg.value = { type: 'error', text: data.message || '保存失败' }
    }
  } catch {
    profileMsg.value = { type: 'error', text: '网络错误' }
  } finally {
    profileSaving.value = false
  }
}

async function changePassword() {
  if (!authStore.isLoggedIn) return
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordMsg.value = { type: 'error', text: '两次密码输入不一致' }
    return
  }
  if (passwordForm.value.new_password.length < 8) {
    passwordMsg.value = { type: 'error', text: '新密码至少8位' }
    return
  }
  passwordSaving.value = true
  passwordMsg.value = { type: '', text: '' }
  try {
    const data = await request('/auth/password', {
      method: 'PUT',
      body: JSON.stringify(passwordForm.value),
    })
    if (data.code === 200) {
      passwordMsg.value = { type: 'success', text: '密码修改成功' }
      showPasswordForm.value = false
      passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    } else {
      passwordMsg.value = { type: 'error', text: data.message || '修改失败' }
    }
  } catch {
    passwordMsg.value = { type: 'error', text: '网络错误' }
  } finally {
    passwordSaving.value = false
  }
}

// ── 标签页切换加载 ──
const loadedTabs = ref(new Set<TabKey>())

watch(activeTab, (tab) => {
  if (loadedTabs.value.has(tab)) return
  loadedTabs.value.add(tab)
  if (tab === 'participations') fetchParticipations()
  else if (tab === 'credits') fetchCredits()
  else if (tab === 'favorites') fetchFavorites()
  else if (tab === 'calendar') fetchCalendarData()
  else if (tab === 'profile') initProfileForm()
})

// ── 刷新当前标签页 ──
function refreshCurrentTab() {
  const tab = activeTab.value
  loadedTabs.value.delete(tab)
  if (tab === 'participations') fetchParticipations()
  else if (tab === 'credits') fetchCredits()
  else if (tab === 'favorites') fetchFavorites()
  else if (tab === 'calendar') fetchCalendarData()
  else if (tab === 'profile') initProfileForm()
  loadedTabs.value.add(tab)
}

// ── 下拉刷新（移动端 touch 事件） ──
const pullDistance = ref(0)
const isPulling = ref(false)
let touchStartY = 0

function handleTouchStart(e: TouchEvent) {
  const scrollEl = document.querySelector('.tab-content') as HTMLElement | null
  if (scrollEl && scrollEl.scrollTop > 0) return
  touchStartY = e.touches[0].clientY
  isPulling.value = true
}

function handleTouchMove(e: TouchEvent) {
  if (!isPulling.value) return
  const deltaY = e.touches[0].clientY - touchStartY
  if (deltaY > 0) {
    pullDistance.value = Math.min(deltaY * 0.5, 80)
  }
}

function handleTouchEnd() {
  if (pullDistance.value >= 60) {
    refreshCurrentTab()
  }
  isPulling.value = false
  pullDistance.value = 0
}

onMounted(async () => {
  fetchColleges()
  await fetchProfile()
  loadedTabs.value.add('participations')
  fetchParticipations()
})
</script>

<template>
  <div class="profile-page">
    <!-- 用户信息卡片 -->
    <div class="user-card">
      <div class="user-avatar-wrap">
        <img
          v-if="userProfile?.avatar_url"
          :src="userProfile.avatar_url"
          alt=""
          class="user-avatar-img"
        />
        <div v-else class="user-avatar-placeholder">
          <User class="w-6 h-6" />
        </div>
      </div>
      <div class="user-info">
        <h2 class="user-name">{{ userProfile?.name || '加载中...' }}</h2>
        <span class="user-meta">{{ userProfile?.account }}</span>
        <span class="user-meta">{{ userProfile?.college_name }}</span>
      </div>
    </div>

    <!-- 标签导航 -->
    <div class="tab-nav">
      <div class="tab-scroll">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" class="w-4 h-4" />
          <span>{{ tab.label }}</span>
        </button>
        <button class="tab-refresh-btn" title="刷新" @click="refreshCurrentTab">
          <RefreshCw class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 标签页内容 -->
    <div
      class="tab-content"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <!-- 下拉刷新指示器（移动端） -->
      <div v-if="pullDistance > 0" class="pull-indicator" :style="{ height: pullDistance + 'px' }">
        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': pullDistance >= 60 }" />
        <span>{{ pullDistance >= 60 ? '释放刷新' : '下拉刷新' }}</span>
      </div>
      <!-- 我的参与 -->
      <div v-if="activeTab === 'participations'" class="tab-panel">
        <div class="filter-bar">
          <button
            v-for="f in (['all', 'active', 'ended'] as const)"
            :key="f"
            class="filter-pill"
            :class="{ active: participationFilter === f }"
            @click="participationFilter = f"
          >
            {{ f === 'all' ? '全部' : f === 'active' ? '进行中' : '已结束' }}
          </button>
        </div>

        <div v-if="participationsLoading" class="loading-hint">加载中...</div>
        <div v-else-if="participations.length === 0" class="empty-hint">
          <Handshake class="w-10 h-10 text-text-disabled mb-2" />
          <p>暂无参与记录</p>
        </div>
        <div v-else class="participation-list">
          <ParticipationCard
            v-for="item in participations"
            :key="item.id"
            :item="item"
            @click="onParticipationClick"
            @view-qrcode="onViewQrcode"
            @view-memento="onViewMemento"
            @cancel="onCancelParticipation"
          />
        </div>
      </div>

      <!-- 我的学分 -->
      <div v-if="activeTab === 'credits'" class="tab-panel">
        <div v-if="creditsLoading" class="loading-hint">加载中...</div>
        <div v-else-if="!creditSummary" class="empty-hint">
          <GraduationCap class="w-10 h-10 text-text-disabled mb-2" />
          <p>暂无学分数据</p>
        </div>
        <template v-else>
          <div class="credit-list">
            <div v-for="d in creditSummary.details" :key="d.type" class="credit-row">
              <div class="credit-header">
                <span class="credit-type">{{ d.type }}</span>
                <span class="credit-value" :class="{ 'text-success': d.is_reached, 'text-accent': !d.is_reached }">
                  {{ d.current }} / {{ d.required }}
                </span>
              </div>
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :class="d.is_reached ? 'bg-success' : 'bg-accent'"
                  :style="{ width: getProgressWidth(d.current, d.required) + '%' }"
                />
              </div>
              <div class="credit-status">
                <template v-if="d.is_reached">
                  <CheckCircle2 class="w-3.5 h-3.5 text-success" />
                  <span class="text-success text-xs">{{ d.current }}分</span>
                </template>
                <template v-else>
                  <AlertTriangle class="w-3.5 h-3.5 text-accent" />
                  <span class="text-accent text-xs">还差 {{ d.gap }}</span>
                </template>
                <span class="credit-percent text-xs text-text-disabled ml-auto">
                  {{ getProgressPercent(d.current, d.required) }}%
                </span>
              </div>
            </div>
          </div>

          <div class="credit-divider" />

          <div class="credit-summary-block">
            <div class="summary-row">
              <span class="summary-label">本年度累计</span>
              <span class="summary-value">{{ creditSummary.yearly_total }} 分</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">入学以来累计</span>
              <span class="summary-value">
                {{ creditSummary.total }} / {{ creditSummary.total_required }}
              </span>
            </div>
            <div v-if="!creditSummary.is_total_reached" class="summary-warning">
              <AlertTriangle class="w-3.5 h-3.5 text-accent" />
              <span class="text-accent text-xs">未达标：总分需 >= {{ creditSummary.total_required }} 且每类 >= {{ creditSummary.per_type_required }}</span>
            </div>
            <div v-else class="summary-success">
              <CheckCircle2 class="w-3.5 h-3.5 text-success" />
              <span class="text-success text-xs">已达标，继续保持！</span>
            </div>
          </div>

          <div class="ai-advice-card">
            <Sparkles class="w-4 h-4 text-primary shrink-0" />
            <div class="ai-advice-content">
              <p class="ai-advice-text">
                还差 {{ creditSummary.total_gap }} 分，优先参加
                {{ creditSummary.details.filter(d => !d.is_reached).map(d => d.type).join('、') }}类活动
              </p>
              <RouterLink to="/credit-analysis" class="ai-advice-link">
                查看推荐活动
                <ChevronRight class="w-3.5 h-3.5" />
              </RouterLink>
            </div>
          </div>
        </template>
      </div>

      <!-- 我的收藏 -->
      <div v-if="activeTab === 'favorites'" class="tab-panel">
        <div v-if="favoritesLoading" class="loading-hint">加载中...</div>
        <div v-else-if="favorites.length === 0" class="empty-hint">
          <Heart class="w-10 h-10 text-text-disabled mb-2" />
          <p>暂无收藏</p>
        </div>
        <div v-else class="favorites-grid">
          <div
            v-for="item in favorites"
            :key="item.id"
            class="favorite-wrapper"
            :class="{ 'is-expired': isFavoriteExpired(item) }"
          >
            <ActivityCard
              :data="item"
              :show-favorite="true"
              :disabled="isFavoriteExpired(item)"
              @click="goActivityDetail"
              @favorite="toggleFavorite"
            />
            <div v-if="isFavoriteExpired(item)" class="expired-overlay">
              <span class="expired-badge">已结束</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 我的活动日历 -->
      <div v-if="activeTab === 'calendar'" class="tab-panel">
        <div class="cal-layout">
        <div class="calendar-card">
          <div class="calendar-header">
            <button class="calendar-nav-btn" @click="prevMonth">
              <ChevronLeft class="w-4 h-4" />
            </button>
            <span class="calendar-title">{{ calendarYear }}年{{ calendarMonth + 1 }}月</span>
            <button class="calendar-nav-btn" @click="nextMonth">
              <ChevronLeft class="w-4 h-4 rotate-180" />
            </button>
          </div>

          <div class="calendar-grid">
            <div v-for="day in calendarWeekDays" :key="day" class="calendar-weekday">
              {{ day }}
            </div>
            <div
              v-for="(day, idx) in calendarDays"
              :key="idx"
              class="calendar-day"
              :class="{
                'has-activity': day !== null && activityDates.has(day),
                'is-selected': day !== null && selectedDate === day,
                'is-empty': day === null,
              }"
              @click="selectDate(day)"
            >
              <span v-if="day !== null" class="day-num">{{ day }}</span>
            </div>
          </div>
        </div>
        <!-- 右侧/下方：选中日期的活动列表 -->
        <div class="cal-side">
          <div v-if="selectedDate !== null && selectedDateActivities.length > 0" class="date-activities">
            <h4 class="date-title">
              {{ calendarMonth + 1 }}月{{ selectedDate }}日
            </h4>
            <div class="date-activity-list">
              <div
                v-for="item in selectedDateActivities"
                :key="item.id"
                class="date-activity-item"
                @click="goActivityDetail(item.activity_id)"
              >
                <div class="date-activity-dot" />
                <div class="date-activity-info">
                  <p class="date-activity-name">{{ item.title }}</p>
                  <p class="date-activity-time">
                    <span class="date-activity-label">时间</span>
                    {{ formatCalendarTime(item.start_time) }}-{{ formatCalendarEndTime(item) }}
                  </p>
                  <p class="date-activity-loc">
                    <span class="date-activity-label">地点</span>
                    {{ item.location }}
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="date-activities">
            <h4 class="date-title" style="color:#94A3B8; font-weight:400;">点击有蓝色圆圈的日期查看当天活动</h4>
          </div>
        </div>
      </div>
      </div>

      <!-- 编辑资料 -->
      <div v-if="activeTab === 'profile'" class="tab-panel">
        <div class="profile-form-card">
          <div class="form-grid">
            <div class="form-row">
              <label class="form-label">学号</label>
              <input
                :value="userProfile?.account"
                class="form-input form-input-readonly"
                readonly
                tabindex="-1"
              />
            </div>
            <div class="form-row">
              <label class="form-label">姓名</label>
              <input v-model="profileForm.name" type="text" class="form-input" />
            </div>
            <div class="form-row">
              <label class="form-label">学院</label>
              <select v-model="profileForm.college_id" class="form-input">
                <option :value="null">请选择学院</option>
                <option v-for="c in colleges.filter(x => x.id !== 0)" :key="c.id" :value="c.id">
                  {{ c.name }}
                </option>
              </select>
            </div>
            <div class="form-row">
              <label class="form-label">手机号</label>
              <input v-model="profileForm.phone" type="tel" class="form-input" />
            </div>
            <div class="form-row">
              <label class="form-label">邮箱</label>
              <input v-model="profileForm.email" type="email" class="form-input" />
            </div>
          </div>

          <div v-if="profileMsg.text" class="form-msg" :class="profileMsg.type">
            {{ profileMsg.text }}
          </div>

          <div class="password-section">
            <button class="password-toggle" @click="showPasswordForm = !showPasswordForm">
              <Lock class="w-4 h-4" />
              <span>修改密码</span>
              <ChevronRight class="w-4 h-4 transition-transform" :class="{ 'rotate-90': showPasswordForm }" />
            </button>

            <Transition name="slide">
              <div v-if="showPasswordForm" class="password-form">
                <div class="form-row">
                  <label class="form-label">当前密码</label>
                  <div class="input-with-toggle">
                    <input
                      v-model="passwordForm.old_password"
                      :type="showOldPwd ? 'text' : 'password'"
                      class="form-input"
                    />
                    <button class="toggle-vis" @click="showOldPwd = !showOldPwd">
                      <Eye v-if="!showOldPwd" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div class="form-row">
                  <label class="form-label">新密码</label>
                  <div class="input-with-toggle">
                    <input
                      v-model="passwordForm.new_password"
                      :type="showNewPwd ? 'text' : 'password'"
                      class="form-input"
                    />
                    <button class="toggle-vis" @click="showNewPwd = !showNewPwd">
                      <Eye v-if="!showNewPwd" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div class="form-row">
                  <label class="form-label">确认新密码</label>
                  <div class="input-with-toggle">
                    <input
                      v-model="passwordForm.confirm_password"
                      :type="showConfirmPwd ? 'text' : 'password'"
                      class="form-input"
                    />
                    <button class="toggle-vis" @click="showConfirmPwd = !showConfirmPwd">
                      <Eye v-if="!showConfirmPwd" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div v-if="passwordMsg.text" class="form-msg" :class="passwordMsg.type">
                  {{ passwordMsg.text }}
                </div>
                <button
                  class="btn-secondary"
                  :disabled="passwordSaving"
                  @click="changePassword"
                >
                  {{ passwordSaving ? '修改中...' : '确认修改密码' }}
                </button>
              </div>
            </Transition>
          </div>

          <button
            class="btn-primary"
            :disabled="profileSaving"
            @click="saveProfile"
          >
            {{ profileSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 进群二维码弹窗 -->
    <GlassModal v-model="showQrcodeModal" title="进群二维码" width="320px">
      <div v-if="qrcodeItem" class="qrcode-modal-content">
        <QrCode class="w-10 h-10 text-primary mb-3" />
        <img
          v-if="qrcodeItem.qrcode_url"
          :src="qrcodeItem.qrcode_url"
          alt="群二维码"
          class="qrcode-img"
        />
        <p class="qrcode-hint">请使用微信扫码加入活动群</p>
        <p class="qrcode-activity-name">{{ qrcodeItem.title }}</p>
      </div>
    </GlassModal>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 56rem;
  margin: 0 auto;
  padding: 24px 16px 32px;
}

/* ── 用户卡片 ── */
.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  margin-bottom: 16px;
}
.user-avatar-wrap {
  flex-shrink: 0;
}
.user-avatar-img {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}
.user-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3B82F6;
}
.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
  line-height: 1.3;
}
.user-meta {
  font-size: 13px;
  color: #64748B;
}

@media (min-width: 768px) {
  .user-avatar-img,
  .user-avatar-placeholder {
    width: 56px;
    height: 56px;
  }
  .user-name {
    font-size: 20px;
  }
}

/* ── 标签导航 ── */
.tab-nav {
  margin-bottom: 16px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.tab-nav::-webkit-scrollbar {
  display: none;
}
.tab-scroll {
  display: flex;
  gap: 4px;
  padding-bottom: 4px;
  min-width: max-content;
  border-bottom: 1px solid #E2E8F0;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  white-space: nowrap;
  border-radius: 8px 8px 0 0;
  transition: all 150ms ease;
  position: relative;
}
.tab-btn::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: transparent;
  border-radius: 2px 2px 0 0;
  transition: background 150ms ease;
}
.tab-btn:hover {
  color: #1E293B;
  background: rgba(59, 130, 246, 0.05);
}
.tab-btn.active {
  color: #3B82F6;
}
.tab-btn.active::after {
  background: #3B82F6;
}

@media (min-width: 768px) {
  .tab-btn {
    padding: 10px 18px;
    font-size: 14px;
  }
}

/* ── 标签内容 ── */
.tab-content {
  min-height: 300px;
}
.tab-panel {
  animation: fadeIn 200ms ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── 筛选 ── */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.filter-pill {
  padding: 7px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  background: #F1F5F9;
  transition: all 150ms ease;
}
.filter-pill:hover {
  background: #E2E8F0;
}
.filter-pill.active {
  background: #3B82F6;
  color: white;
}

/* ── 通用状态 ── */
.loading-hint {
  text-align: center;
  padding: 40px 0;
  color: #94A3B8;
  font-size: 14px;
}
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0;
  color: #94A3B8;
  font-size: 14px;
}

/* ── 参与列表 ── */
.participation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── 学分列表 ── */
.credit-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.credit-row {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.credit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.credit-type {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
}
.credit-value {
  font-size: 14px;
  font-weight: 500;
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
}
.progress-track {
  height: 6px;
  background: #F1F5F9;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}
.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 500ms ease;
}
.credit-status {
  display: flex;
  align-items: center;
  gap: 4px;
}
.credit-percent {
  margin-left: auto;
}

/* 桌面端学分表格布局 */
@media (min-width: 768px) {
  .credit-list {
    gap: 0;
    background: #FFFFFF;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    overflow: hidden;
  }
  .credit-row {
    border-radius: 0;
    box-shadow: none;
    padding: 12px 20px;
    display: grid;
    grid-template-columns: 140px 100px 1fr 80px;
    align-items: center;
    gap: 12px;
  }
  .credit-row:not(:last-child) {
    border-bottom: 1px solid #F1F5F9;
  }
  .credit-header {
    margin-bottom: 0;
  }
  .progress-track {
    margin-bottom: 0;
  }
  .credit-status {
    justify-content: flex-end;
  }
  .credit-percent {
    margin-left: 0;
  }
}

.credit-divider {
  height: 1px;
  background: #E2E8F0;
  margin: 20px 0;
}

.credit-summary-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #F8FAFC;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.summary-label {
  font-size: 14px;
  font-weight: 500;
  color: #1E293B;
}
.summary-value {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
}
.summary-warning {
  display: flex;
  align-items: center;
  gap: 4px;
}
.summary-success {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ai-advice-card {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: rgba(59, 130, 246, 0.08);
  border-radius: 10px;
  padding: 14px 16px;
}
.ai-advice-text {
  font-size: 13px;
  color: #3B82F6;
  line-height: 1.5;
}
.ai-advice-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 600;
  color: #3B82F6;
  margin-top: 4px;
}
.ai-advice-link:hover {
  color: #2563EB;
}

/* ── 收藏网格 ── */
.favorites-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
.favorite-wrapper {
  position: relative;
}
.favorite-wrapper.is-expired {
  opacity: 0.6;
  filter: grayscale(40%);
}
.expired-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
}
.expired-badge {
  background: rgba(100, 116, 139, 0.85);
  color: white;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
}
@media (min-width: 768px) {
  .favorites-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (min-width: 1024px) {
  .favorites-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* ── 日历 ── */
.cal-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
@media (min-width: 768px) {
  .cal-layout {
    flex-direction: row;
    align-items: flex-start;
  }
  .calendar-card {
    flex: 0 0 auto;
    width: 360px;
  }
  .cal-side {
    flex: 1;
    min-width: 0;
  }
}
.calendar-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
}
.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.calendar-nav-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748B;
  transition: all 150ms ease;
}
.calendar-nav-btn:hover {
  background: #F1F5F9;
  color: #1E293B;
}
.calendar-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.calendar-weekday {
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  color: #94A3B8;
  padding: 4px 0 6px;
}
.calendar-day {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  height: 36px;
  border-radius: 6px;
  cursor: default;
  transition: all 150ms ease;
}
.calendar-day.is-empty {
  cursor: default;
}
.day-num {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #1E293B;
  border-radius: 50%;
  transition: all 150ms ease;
}
.calendar-day.has-activity {
  cursor: pointer;
}
.calendar-day.has-activity .day-num {
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
  font-weight: 600;
}
.calendar-day.has-activity:hover .day-num {
  background: rgba(59, 130, 246, 0.2);
}
.calendar-day.is-selected .day-num {
  background: #3B82F6;
  color: white;
}
.calendar-day:not(.has-activity):not(.is-empty) .day-num {
  color: #CBD5E1;
}

@media (min-width: 768px) {
  .calendar-day {
    height: 40px;
  }
  .day-num {
    width: 30px;
    height: 30px;
    font-size: 14px;
  }
}

/* ── 日期活动列表 ── */
.date-activities {
  margin-top: 4px;
}
.date-title {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 10px;
}
.date-activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.date-activity-item {
  display: flex;
  gap: 12px;
  background: #FFFFFF;
  border-radius: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 150ms ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.date-activity-item:hover {
  background: #F8FAFC;
}
.date-activity-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #3B82F6;
  margin-top: 6px;
  flex-shrink: 0;
}
.date-activity-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.date-activity-label {
  display: inline-block;
  font-size: 12px;
  color: #64748B;
  background: #F1F5F9;
  border-radius: 4px;
  padding: 1px 6px;
  font-weight: 500;
  width: fit-content;
}
.date-activity-time {
  font-size: 14px;
  color: #64748B;
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
}
.date-activity-name {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}
.date-activity-loc {
  font-size: 13px;
  color: #64748B;
}

/* ── 编辑资料表单 ── */
.profile-form-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
@media (min-width: 768px) {
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #1E293B;
}
.form-input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  color: #1E293B;
  background: white;
  transition: all 150ms ease;
}
.form-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}
.form-input-readonly {
  background: #F8FAFC;
  color: #94A3B8;
  border-style: dashed;
  cursor: not-allowed;
}
.input-with-toggle {
  position: relative;
}
.input-with-toggle .form-input {
  padding-right: 40px;
}
.toggle-vis {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: #94A3B8;
  padding: 4px;
}
.toggle-vis:hover {
  color: #64748B;
}

.form-msg {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-top: 4px;
}
.form-msg.success {
  background: #ECFDF5;
  color: var(--color-success);
}
.form-msg.error {
  background: #FEF2F2;
  color: var(--color-danger);
}

.password-section {
  margin: 20px 0;
  padding-top: 20px;
  border-top: 1px solid #E2E8F0;
}
.password-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #3B82F6;
  transition: opacity 150ms ease;
}
.password-toggle:hover {
  opacity: 0.8;
}
.password-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #F1F5F9;
}

.btn-primary {
  width: 100%;
  height: 44px;
  background: #3B82F6;
  color: white;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 150ms ease;
  margin-top: 20px;
}
.btn-primary:hover {
  background: #2563EB;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
@media (min-width: 768px) {
  .btn-primary {
    max-width: 320px;
  }
}

.btn-secondary {
  height: 38px;
  background: #F1F5F9;
  color: #1E293B;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 150ms ease;
}
.btn-secondary:hover {
  background: #E2E8F0;
}
.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── 动画 ── */
.slide-enter-active,
.slide-leave-active {
  transition: all 200ms ease;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}
.slide-enter-to,
.slide-leave-from {
  max-height: 400px;
}

/* ── 二维码弹窗 ── */
.qrcode-modal-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 0;
}
.qrcode-img {
  width: 200px;
  height: 200px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}
.qrcode-hint {
  font-size: 14px;
  color: #1E293B;
  margin-top: 14px;
}
.qrcode-activity-name {
  font-size: 13px;
  color: #64748B;
  margin-top: 4px;
}

/* ── 刷新按钮 ── */
.tab-refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-left: 4px;
  border-radius: 8px;
  color: #64748B;
  transition: all 150ms ease;
  flex-shrink: 0;
  align-self: center;
}
.tab-refresh-btn:hover {
  background: rgba(59, 130, 246, 0.08);
  color: #3B82F6;
}

/* ── 下拉刷新指示器 ── */
.pull-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: #94A3B8;
  overflow: hidden;
  transition: height 100ms ease;
}
</style>
