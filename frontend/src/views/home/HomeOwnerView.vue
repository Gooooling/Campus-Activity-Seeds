<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileEdit,
  Send,
  TrendingUp,
  Users,
  ChevronRight,
} from 'lucide-vue-next'
import ActivityCard from '@/components/common/ActivityCard.vue'
import { useCountUp } from '@/composables/useCountUp'
import { useHomeStats, type HomeStatsOwner } from '@/composables/useHomeStats'
import type { ActivityListItem } from '@/types/activity'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const { data: stats, fetchStats } = useHomeStats()

const ownerData = computed(() => stats.value as HomeStatsOwner | null)

const totalUsers = useCountUp(computed(() => stats.value?.total_users ?? 0), 2000)
const totalActivities = useCountUp(computed(() => stats.value?.total_activities ?? 0), 2000)
const myActivityCount = useCountUp(computed(() => ownerData.value?.my_activity_count ?? 0), 1500)

const statusSummary = computed(() => ownerData.value?.status_summary ?? { active: 0, recruiting: 0, pending: 0, draft: 0, ended: 0 })
const pendingIssues = computed(() => ownerData.value?.pending_issues ?? [])
const recruitingActivities = computed<ActivityListItem[]>(() => ownerData.value?.recruiting_activities ?? [])

const statusColorMap: Record<string, string> = {
  active: 'var(--color-success)',
  pending: 'var(--color-accent)',
  recruiting: 'var(--color-primary)',
  draft: 'var(--color-text-disabled)',
  ended: 'var(--color-info)',
  rejected: 'var(--color-danger)',
}

const statusLabelMap: Record<string, string> = {
  active: '进行中',
  pending: '待审核',
  recruiting: '报名中',
  draft: '草稿',
  ended: '已结束',
  rejected: '已驳回',
}

function goToMyActivities() {
  router.push('/my-activities')
}

function goToEditActivity(id: number) {
  router.push(`/publish?edit=${id}`)
}

function goToPublish() {
  router.push('/publish')
}

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <div class="home-owner">
    <!-- Banner -->
    <section class="banner-section-sm">
      <div class="container">
        <div class="banner-card owner-banner">
          <Send class="w-8 h-8 text-white mb-2" />
          <h1 class="banner-title-sm">{{ authStore.user?.name ?? '朋友' }}，今天又要发布什么活动呀</h1>
          <p class="banner-subtitle-sm">这里可以管理你的活动，connect更多同学</p>
        </div>
      </div>
    </section>

    <!-- 平台数据 -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-bar">
          <div class="stat-item">
            <Users class="w-5 h-5 stat-icon" />
            <span class="stat-number">{{ totalUsers.count }}</span>
            <span class="stat-label">人已注册</span>
          </div>
          <div class="stat-divider" />
          <div class="stat-item">
            <TrendingUp class="w-5 h-5 stat-icon" />
            <span class="stat-number">{{ totalActivities.count }}</span>
            <span class="stat-label">个活动</span>
          </div>
          <div class="stat-divider" />
          <div class="stat-item">
            <Send class="w-5 h-5 stat-icon" />
            <span class="stat-number">{{ myActivityCount.count }}</span>
            <span class="stat-label">你一共发布了</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 双卡片区域 -->
    <section class="dual-cards-section">
      <div class="container">
        <div class="dual-cards">
          <!-- 待处理事项 -->
          <div class="info-card">
            <div class="info-card-header">
              <AlertTriangle class="w-5 h-5 text-danger" />
              <h3 class="info-card-title">待处理</h3>
            </div>
            <div class="info-card-body">
              <div v-if="pendingIssues.length === 0" class="empty-state">
                <CheckCircle2 class="w-8 h-8 text-success mb-2" />
                <p class="empty-text">暂无待处理事项</p>
              </div>
              <div
                v-for="issue in pendingIssues"
                :key="issue.activity_id"
                class="issue-item"
              >
                <div class="issue-header">
                  <AlertTriangle class="w-4 h-4 text-danger" />
                  <span class="issue-title">「{{ issue.title }}」被驳回</span>
                </div>
                <p class="issue-reason">原因：{{ issue.reject_reason }}</p>
                <button class="issue-action" @click="goToEditActivity(issue.activity_id)">
                  去修改 <ChevronRight class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          <!-- 我的活动状态统计 -->
          <div class="info-card">
            <div class="info-card-header">
              <FileEdit class="w-5 h-5 text-primary" />
              <h3 class="info-card-title">我的活动状态</h3>
            </div>
            <div class="status-list">
              <div
                v-for="(count, key) in statusSummary"
                :key="key"
                class="status-row"
              >
                <div class="status-dot" :style="{ background: statusColorMap[key] }" />
                <span class="status-label">{{ statusLabelMap[key] }}</span>
                <span class="status-count">{{ count }} 个</span>
              </div>
            </div>
            <button class="info-card-footer" @click="goToMyActivities">
              查看全部 <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 报名进行中的活动 -->
    <section v-if="recruitingActivities.length" class="hot-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">
            <Clock class="w-5 h-5 text-primary" />
            报名进行中的活动
          </h2>
        </div>
        <div class="activity-grid">
          <ActivityCard
            v-for="activity in recruitingActivities"
            :key="activity.id"
            :data="activity"
            @click="goToMyActivities"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.banner-section-sm {
  padding: 16px 0 8px;
}
.banner-card {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #3B82F6;
}
.owner-banner {
  border-left-color: #6366F1;
}
.banner-title-sm {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 4px;
}
.banner-subtitle-sm {
  font-size: 14px;
  color: #64748B;
}

.stats-section {
  padding: 16px 0;
}
.stats-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 14px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.stat-icon {
  color: #3B82F6;
}
.stat-number {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
}
.stat-label {
  font-size: 13px;
  color: #64748B;
}
.stat-divider {
  width: 1px;
  height: 28px;
  background: #E2E8F0;
}

.dual-cards-section {
  padding: 16px 0;
}
.dual-cards {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 768px) {
  .dual-cards {
    grid-template-columns: 1fr 1fr;
  }
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.info-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.info-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}
.info-card-body {
  margin-bottom: 12px;
}
.info-card-footer {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #3B82F6;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  color: #94A3B8;
}
.empty-text {
  font-size: 14px;
}

.issue-item {
  padding: 12px;
  background: #FEF2F2;
  border-radius: 8px;
  border-left: 3px solid var(--color-danger);
}
.issue-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.issue-title {
  font-size: 14px;
  font-weight: 500;
  color: #1E293B;
}
.issue-reason {
  font-size: 13px;
  color: #64748B;
  margin-bottom: 8px;
}
.issue-action {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #3B82F6;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-label {
  font-size: 14px;
  color: #1E293B;
  flex: 1;
}
.status-count {
  font-size: 14px;
  font-weight: 600;
  color: #64748B;
}

.hot-section {
  padding: 16px 0 48px;
}
.section-header {
  margin-bottom: 20px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
}

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
  }
}
</style>
