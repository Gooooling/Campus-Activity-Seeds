<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft,
  Sparkles,
  User,
  AlertTriangle,
  CheckCircle2,
  Clock,
  MapPin,
  ChevronRight,
  Image as ImageIcon,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { ElMessage } from 'element-plus'
import type { CreditSummary, CreditAdvice, RecommendedActivity } from '@/types/activity'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const creditSummary = ref<CreditSummary | null>(null)
const creditAdvice = ref<CreditAdvice | null>(null)

const userName = computed(() => authStore.user?.name || '同学')
const collegeName = computed(() => authStore.user?.college_name || '')

async function fetchData() {
  if (!authStore.isLoggedIn) return
  loading.value = true
  try {
    const [data1, data2] = await Promise.all([
      request('/credits/summary'),
      request('/ai/credit-advice'),
    ])
    if (data1.code === 200) creditSummary.value = data1.data
    if (data2.code === 200) creditAdvice.value = data2.data
  } catch {
    error.value = '服务器错误请稍后重试'
  } finally {
    loading.value = false
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

const isAllMet = computed(() => {
  if (!creditSummary.value) return false
  const totalOk = creditSummary.value.total >= creditSummary.value.total_required
  const allTypesOk = creditSummary.value.details.every(d => d.current >= d.required)
  return totalOk && allTypesOk
})

function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.floor((+target - +today) / (1000 * 60 * 60 * 24))

  const MM = d.getMonth() + 1
  const dd = d.getDate()

  if (diffDays === 0) return `今天${MM}月${dd}日`
  if (diffDays === 1) return `明天${MM}月${dd}日`
  if (diffDays === 2) return `后天${MM}月${dd}日`
  return `${MM}月${dd}日`
}

function goActivity(id: number) {
  router.push(`/activities/${id}`)
}

onMounted(fetchData)
</script>

<template>
  <div class="analysis-page">
    <div class="analysis-inner">
      <!-- 返回按钮 -->
      <button class="back-link" @click="router.push('/')">
        <ChevronLeft class="w-4 h-4" />
        <span>返回首页</span>
      </button>

      <!-- 概览卡片 -->
      <div class="overview-card">
        <div class="overview-header">
          <Sparkles class="w-6 h-6 text-primary" />
          <h1 class="overview-title">AI 学分分析</h1>
        </div>
        <div class="overview-user">
          <div class="user-avatar-placeholder">
            <User class="w-5 h-5 text-primary" />
          </div>
          <div class="user-info">
            <span class="user-name">{{ userName }}</span>
            <span v-if="collegeName" class="user-college">{{ collegeName }}</span>
          </div>
        </div>
        <div class="overview-stats">
          <div class="stat-item">
            <span class="stat-label">入学以来累计</span>
            <span class="stat-value">
              {{ creditSummary?.total ?? 0 }} / {{ creditSummary?.total_required ?? 6.0 }} 分
            </span>
          </div>
          <div v-if="creditSummary && !isAllMet" class="stat-warning">
            <AlertTriangle class="w-3.5 h-3.5 text-accent" />
            <span class="text-accent text-xs">未达标：总分需 >= {{ creditSummary.total_required }} 且每类 >= {{ creditSummary.per_type_required }}</span>
          </div>
          <div v-else-if="creditSummary && isAllMet" class="stat-success">
            <CheckCircle2 class="w-3.5 h-3.5 text-success" />
            <span class="text-success text-xs">已达标，继续保持！</span>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-hint">加载中...</div>

      <template v-else-if="creditSummary">
        <div class="analysis-columns">
          <!-- 左栏：学分详细 -->
          <div class="column-left">
            <h2 class="column-title">各类学分详细分析</h2>
            <div class="credit-list">
              <div
                v-for="d in creditSummary.details"
                :key="d.type"
                class="credit-row"
              >
                <div class="credit-header">
                  <span class="credit-type">{{ d.type }}</span>
                  <span
                    class="credit-value"
                    :class="{ 'text-success': d.is_reached, 'text-accent': !d.is_reached }"
                  >
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
            </div>
          </div>

          <!-- 右栏：AI 建议 -->
          <div class="column-right">
            <h2 class="column-title">AI 建议</h2>
            <div class="advice-card">
              <!-- 全达标祝贺 -->
              <template v-if="isAllMet">
                <div class="congrats-section">
                  <CheckCircle2 class="w-10 h-10 text-success mb-2" />
                  <p class="congrats-text">恭喜！你已达到毕业学分要求 🎉</p>
                  <p class="congrats-sub">继续保持，别忘本年度也要攒够学分哦。</p>
                </div>
              </template>
              <template v-else>
                <p class="advice-intro">
                  你还需要 <strong>{{ creditAdvice?.total_gap ?? creditSummary.total_gap }}</strong> 分才能达到毕业要求。
                </p>

                <div v-if="creditAdvice?.priority_list?.length" class="priority-section">
                <p class="priority-title">优先参加以下类型活动（此处列出每类所需最低分）：</p>
                <div class="priority-list">
                  <div
                    v-for="(p, idx) in creditAdvice.priority_list"
                    :key="p.type"
                    class="priority-item"
                  >
                    <span class="priority-rank">{{ idx + 1 }}</span>
                    <span class="priority-type">{{ p.type }}</span>
                    <span class="priority-gap">还差 {{ p.gap }} 分</span>
                    <span v-if="idx === 0" class="priority-note">缺口最大</span>
                    <span v-else-if="idx === creditAdvice.priority_list.length - 1" class="priority-note">快达标了！</span>
                  </div>
                </div>
              </div>

              <div v-if="creditAdvice?.recommended_activities?.length" class="recommend-section">
                <p class="recommend-title">推荐活动：</p>
                <div class="recommend-list">
                  <div
                    v-for="act in creditAdvice.recommended_activities"
                    :key="act.id"
                    class="recommend-card"
                    @click="goActivity(act.id)"
                  >
                    <div class="recommend-cover">
                      <img
                        v-if="act.cover_image_url"
                        :src="act.cover_image_url"
                        :alt="act.title"
                        class="cover-img"
                      />
                      <div v-else class="cover-placeholder">
                        <ImageIcon class="w-6 h-6 text-text-disabled" />
                      </div>
                    </div>
                    <div class="recommend-info">
                      <h4 class="recommend-name">{{ act.title }}</h4>
                      <div class="recommend-tags">
                        <span class="recommend-tag">{{ act.credit_type }} +{{ act.credit_value ?? '-' }}分</span>
                      </div>
                      <div class="recommend-meta">
                        <span class="meta-item">
                          <Clock class="w-3 h-3" />
                          截止 {{ formatDateShort(act.registration_deadline) }}
                        </span>
                        <span class="meta-item">
                          <MapPin class="w-3 h-3" />
                          {{ act.location }}
                        </span>
                      </div>
                      <span class="recommend-action">
                        去看看
                        <ChevronRight class="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <p class="advice-footer">
                你已经达标了{{ creditSummary.details.filter(d => d.is_reached).length }}类学分，继续保持！
                同时别忘了本年度也要攒够学分哦。
              </p>
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.analysis-page {
  background: #F8FAFC;
  min-height: calc(100dvh - 64px);
  padding: 16px;
}

.analysis-inner {
  max-width: 64rem; /* max-w-5xl = 1024px */
  margin: 0 auto;
}

@media (min-width: 640px) {
  .analysis-page {
    padding: 24px;
  }
}

/* ── 返回按钮 ── */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  margin-bottom: 16px;
  transition: color 150ms ease;
}
.back-link:hover {
  color: #3B82F6;
}

/* ── 概览卡片 ── */
.overview-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}
.overview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.overview-title {
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
}
.overview-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.user-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}
.user-college {
  font-size: 13px;
  color: #64748B;
}
.overview-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stat-label {
  font-size: 14px;
  color: #64748B;
}
.stat-value {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
}
.stat-warning,
.stat-success {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ── 双栏布局 ── */
.analysis-columns {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

@media (min-width: 1024px) {
  .analysis-columns {
    flex-direction: row;
    gap: 24px; /* gap-6 */
  }
  .column-left,
  .column-right {
    flex: 1;
    width: 50%;
  }
}

.column-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 14px;
}

/* ── 学分列表 ── */
.credit-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  transition: width 800ms ease;
}
.credit-status {
  display: flex;
  align-items: center;
  gap: 4px;
}
.credit-percent {
  margin-left: auto;
}

.credit-divider {
  height: 1px;
  background: #E2E8F0;
  margin: 16px 0;
}
.credit-summary-block {
  background: #F8FAFC;
  border-radius: 10px;
  padding: 12px 16px;
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

/* ── AI 建议 ── */
.advice-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.advice-intro {
  font-size: 14px;
  color: #1E293B;
  line-height: 1.6;
  margin-bottom: 16px;
}
.advice-intro strong {
  color: #F59E0B;
  font-weight: 600;
}

.priority-section {
  margin-bottom: 16px;
}
.priority-title {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 10px;
}
.priority-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.priority-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}
.priority-rank {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.priority-type {
  font-weight: 500;
  color: #1E293B;
}
.priority-gap {
  color: #64748B;
  font-size: 13px;
}
.priority-note {
  font-size: 12px;
  color: #F59E0B;
  margin-left: auto;
}

.recommend-section {
  margin-bottom: 16px;
}
.recommend-title {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 10px;
}
.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.recommend-card {
  display: flex;
  gap: 12px;
  background: #F8FAFC;
  border-radius: 10px;
  padding: 12px;
  cursor: pointer;
  transition: background 150ms ease;
}
.recommend-card:hover {
  background: #F1F5F9;
}
.recommend-cover {
  width: 72px;
  height: 72px;
  border-radius: 8px;
  overflow: hidden;
  background: #E2E8F0;
  flex-shrink: 0;
}
.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.recommend-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.recommend-name {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.recommend-tags {
  display: flex;
  gap: 6px;
}
.recommend-tag {
  font-size: 12px;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.recommend-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: #64748B;
}
.recommend-action {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  font-weight: 500;
  color: #3B82F6;
  margin-top: 2px;
  transition: opacity 150ms ease;
}
.recommend-action:hover {
  opacity: 0.8;
}

.advice-footer {
  font-size: 13px;
  color: #64748B;
  line-height: 1.5;
  padding-top: 12px;
  border-top: 1px solid #F1F5F9;
}

/* ── 通用状态 ── */
.loading-hint {
  text-align: center;
  padding: 40px 0;
  color: #94A3B8;
  font-size: 14px;
}

/* 颜色工具类 */
.text-success {
  color: var(--color-success);
}
.text-accent {
  color: #F59E0B;
}
.text-primary {
  color: #3B82F6;
}
.text-text-disabled {
  color: #94A3B8;
}
.bg-success {
  background: var(--color-success);
}
.bg-accent {
  background: #F59E0B;
}

/* ── 全达标祝贺 ── */
.congrats-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 0;
}
.congrats-text {
  font-size: 18px;
  font-weight: 700;
  color: #059669;
  margin-bottom: 4px;
}
.congrats-sub {
  font-size: 14px;
  color: #64748B;
}
</style>
