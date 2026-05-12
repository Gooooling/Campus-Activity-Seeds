<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Calendar,
  Sparkles,
  Star,
  ChevronRight,
  Users,
  TrendingUp,
} from 'lucide-vue-next'
import ActivityCard from '@/components/common/ActivityCard.vue'
import { useCountUp } from '@/composables/useCountUp'
import { useHomeStats, type HomeStatsStudent } from '@/composables/useHomeStats'
import type { ActivityListItem } from '@/types/activity'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const { data: stats, loading: statsLoading, fetchStats } = useHomeStats()

const studentData = computed(() => stats.value as HomeStatsStudent | null)

const totalUsers = useCountUp(computed(() => stats.value?.total_users ?? 0), 2000)
const totalActivities = useCountUp(computed(() => stats.value?.total_activities ?? 0), 2000)
const myParticipationCount = useCountUp(computed(() => studentData.value?.my_participation_count ?? 0), 1500)

const upcomingActivities = computed(() => studentData.value?.upcoming_activities ?? [])
const expiringFavorites = computed<ActivityListItem[]>(() => studentData.value?.expiring_favorites ?? [])

const creditAdvice = computed(() => {
  const preview = studentData.value?.credit_advice_preview ?? ''
  const match = preview.match(/还差\s*([\d.]+)\s*(.+?)分/)
  if (!match) {
    return { gap: 0, type: '', isAllMet: true }
  }
  return { gap: parseFloat(match[1]), type: match[2], isAllMet: false }
})

function formatActivityTime(timeStr: string): string {
  const date = new Date(timeStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function goToActivityDetail(id: number) {
  router.push(`/activities/${id}`)
}

function goToCreditAnalysis() {
  router.push('/credit-analysis')
}

function goToActivityHall() {
  router.push('/activities')
}

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <div class="home-student">
    <!-- Banner -->
    <section class="banner-section-sm">
      <div class="container">
        <div class="banner-card">
          <Sparkles class="w-8 h-8 text-primary mb-2" />
          <h1 class="banner-title-sm">{{ authStore.user?.name ?? '同学' }}，欢迎你回来！</h1>
          <p class="banner-subtitle-sm">发现精彩活动，记录你的成长足迹</p>
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
            <Star class="w-5 h-5 stat-icon" />
            <span class="stat-number">{{ myParticipationCount.count }}</span>
            <span class="stat-label">你参与了</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 双卡片区域 -->
    <section class="dual-cards-section">
      <div class="container">
        <div class="dual-cards">
          <!-- 最近要参加 -->
          <div class="info-card">
            <div class="info-card-header">
              <Calendar class="w-5 h-5 text-primary" />
              <h3 class="info-card-title">最近要参加</h3>
            </div>
            <div class="info-card-body">
              <div
                v-for="item in upcomingActivities"
                :key="item.id"
                class="upcoming-item"
                @click="goToActivityDetail(item.id)"
              >
                <span class="upcoming-date">{{ formatActivityTime(item.start_time) }}</span>
                <span class="upcoming-name">{{ item.title }}</span>
              </div>
              <div v-if="!upcomingActivities.length" class="empty-hint-inline">暂无即将参加的活动</div>
            </div>
            <button class="info-card-footer" @click="goToActivityHall">
              查看全部 <ChevronRight class="w-4 h-4" />
            </button>
          </div>

          <!-- AI 学分建议 -->
          <div class="info-card accent-card" @click="goToCreditAnalysis">
            <div class="info-card-header">
              <Sparkles class="w-5 h-5 text-accent" />
              <h3 class="info-card-title">AI 学分建议</h3>
            </div>
            <div class="info-card-body">
              <template v-if="creditAdvice.isAllMet">
                <p class="advice-text">恭喜！你已达到毕业学分要求 🎉</p>
              </template>
              <template v-else-if="studentData?.credit_advice_preview">
                <p class="advice-text">
                  还差 <span class="advice-highlight">{{ creditAdvice.gap }}</span> {{ creditAdvice.type }}分
                </p>
                <p class="advice-sub">{{ studentData.credit_advice_preview }}</p>
              </template>
              <p v-else-if="!statsLoading" class="advice-text">暂无学分建议</p>
            </div>
            <div class="info-card-footer">
              去看看 <ChevronRight class="w-4 h-4" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 即将截止的收藏 -->
    <section class="hot-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">
            <Star class="w-5 h-5 text-accent" />
            我收藏的即将截止的活动
          </h2>
        </div>
        <div v-if="expiringFavorites.length" class="activity-grid">
          <ActivityCard
            v-for="activity in expiringFavorites"
            :key="activity.id"
            :data="activity"
            show-favorite
            @click="goToActivityDetail"
          />
        </div>
        <div v-else class="empty-hint-inline">还没有收藏的活动，去逛逛吧</div>
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
  transition: all 150ms ease;
  cursor: pointer;
}
.info-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.accent-card {
  background: white;
  border-left: 4px solid #F59E0B;
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

.upcoming-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #F1F5F9;
  cursor: pointer;
  transition: all 150ms ease;
}
.upcoming-item:last-child {
  border-bottom: none;
}
.upcoming-item:hover {
  color: #3B82F6;
}
.upcoming-date {
  font-size: 13px;
  font-weight: 600;
  color: #3B82F6;
  min-width: 60px;
}
.upcoming-name {
  font-size: 14px;
  color: #1E293B;
}

.empty-hint-inline {
  text-align: center;
  padding: 16px 0;
  color: #94A3B8;
  font-size: 13px;
}

.advice-text {
  font-size: 16px;
  color: #1E293B;
  margin-bottom: 4px;
}
.advice-highlight {
  font-size: 24px;
  font-weight: 700;
  color: #F59E0B;
}
.advice-sub {
  font-size: 13px;
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
