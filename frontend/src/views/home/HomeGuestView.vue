<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Flame, Users, TrendingUp, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import ActivityCard from '@/components/common/ActivityCard.vue'
import GlassModal from '@/components/common/GlassModal.vue'
import { useCountUp } from '@/composables/useCountUp'
import { useHomeStats, type HomeStatsBase } from '@/composables/useHomeStats'
import type { ActivityListItem } from '@/types/activity'
import { request } from '@/utils/request'

const router = useRouter()

const { data: stats, loading: statsLoading, fetchStats } = useHomeStats()

const totalUsers = useCountUp(computed(() => stats.value?.total_users ?? 0), 2000)
const totalActivities = useCountUp(computed(() => stats.value?.total_activities ?? 0), 2000)

const hotActivities = computed<ActivityListItem[]>(() => {
  return (stats.value as HomeStatsBase)?.hot_activities ?? []
})

const showLoginModal = ref(false)
const pendingActivityId = ref<number | null>(null)

function handleActivityClick(id: number) {
  pendingActivityId.value = id
  showLoginModal.value = true
}

function goToLogin() {
  showLoginModal.value = false
  router.push(`/login?redirect=${encodeURIComponent(router.currentRoute.value.fullPath)}`)
}

// 轮播图
const currentSlide = ref(0)
const slides = ref<Array<{ title: string; subtitle: string | null; image_url: string }>>([])


let autoplayTimer: ReturnType<typeof setInterval> | null = null

function nextSlide() {
  if (slides.value.length === 0) return
  currentSlide.value = (currentSlide.value + 1) % slides.value.length
}

function prevSlide() {
  if (slides.value.length === 0) return
  currentSlide.value = (currentSlide.value - 1 + slides.value.length) % slides.value.length
}

function goToSlide(index: number) {
  currentSlide.value = index
}

function startAutoplay() {
  stopAutoplay()
  if (slides.value.length < 2) return
  autoplayTimer = setInterval(nextSlide, 3000)
}

function stopAutoplay() {
  if (autoplayTimer) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

async function fetchBanners() {
  try {
    const data = await request<Array<{ title: string; subtitle: string | null; image_url: string }>>('/home/banners')
    if (data.code === 200 && data.data && data.data.length > 0) {
      slides.value = data.data
      startAutoplay()
    }
  } catch {
    // 获取失败时保持空数组
  }
}

onMounted(() => {
  fetchBanners()
  fetchStats()
})

onUnmounted(() => {
  stopAutoplay()
})
</script>

<template>
  <div class="home-guest">
    <!-- 轮播 Banner -->
    <section class="banner-section">
      <div class="banner-slider">
        <!-- 有轮播图数据时 -->
        <template v-if="slides.length > 0">
          <div
            v-for="(slide, index) in slides"
            :key="index"
            class="banner-slide"
            :class="{ active: currentSlide === index }"
          >
            <!-- 毛玻璃模糊背景（左右两侧溢出填充） -->
            <div
              class="banner-blur-bg"
              :style="{ backgroundImage: `url(${slide.image_url})` }"
            />
            <!-- 居中清晰的图片 -->
            <img
              :src="slide.image_url"
              :alt="slide.title"
              class="banner-img"
            />
          </div>
        </template>

        <!-- 无轮播图数据时，显示默认欢迎图 -->
        <template v-else>
          <div class="banner-slide" style="background: linear-gradient(135deg, #1e3a5f, #2563eb);">
            <div class="flex flex-col items-center justify-center w-full h-full text-white">
              <h1 style="font-size: 28px; font-weight: 700; text-shadow: 0 2px 8px rgba(0,0,0,0.15);">发现你的校园精彩</h1>
              <p style="font-size: 15px; opacity: 0.9; margin-top: 8px;">探索第二课堂，记录每一次成长</p>
            </div>
          </div>
        </template>

        <!-- 左右箭头（仅在有多张轮播图时显示） -->
        <template v-if="slides.length > 1">
          <button class="banner-arrow banner-arrow-left" @click="prevSlide(); stopAutoplay()">
            <ChevronLeft class="w-6 h-6" />
          </button>
          <button class="banner-arrow banner-arrow-right" @click="nextSlide(); stopAutoplay()">
            <ChevronRight class="w-6 h-6" />
          </button>
        </template>

        <!-- 指示器（仅在有多张轮播图时显示） -->
        <div v-if="slides.length > 1" class="banner-indicators">
          <button
            v-for="(_, index) in slides"
            :key="index"
            class="indicator-dot"
            :class="{ active: currentSlide === index }"
            @click="goToSlide(index); stopAutoplay()"
          />
        </div>
      </div>
    </section>

    <!-- 平台数据 -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-bar">
          <div class="stat-item">
            <Users class="w-5 h-5 stat-icon" />
            <div class="stat-content">
              <span class="stat-number">{{ totalUsers.count }}</span>
              <span class="stat-label">人已注册</span>
            </div>
          </div>
          <div class="stat-divider" />
          <div class="stat-item">
            <TrendingUp class="w-5 h-5 stat-icon" />
            <div class="stat-content">
              <span class="stat-number">{{ totalActivities.count }}</span>
              <span class="stat-label">个活动</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 热门活动 -->
    <section class="hot-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">
            <Flame class="w-5 h-5 text-danger" />
            近期热门活动
          </h2>
        </div>
        <div v-if="hotActivities.length" class="activity-grid">
          <ActivityCard
            v-for="activity in hotActivities"
            :key="activity.id"
            :data="activity"
            @click="handleActivityClick"
          />
        </div>
        <div v-else-if="!statsLoading" class="empty-hint">
          <p>暂无热门活动</p>
        </div>
      </div>
    </section>

    <!-- 请先登录弹窗 -->
    <GlassModal v-model="showLoginModal" title="提示">
      <p class="text-text-secondary text-center py-4">
        请先登录后查看活动详情
      </p>
      <template #footer="{ close }">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" @click="goToLogin">去登录</button>
      </template>
    </GlassModal>
  </div>
</template>

<style scoped>
.banner-section {
  width: 100%;
  margin-bottom: 48px;
}
.banner-slider {
  position: relative;
  width: 100%;
  height: 360px;
  min-height: 260px;
  max-height: 440px;
  overflow: hidden;
}
.banner-slide {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  opacity: 0;
  visibility: hidden;
  transition: opacity 600ms ease, visibility 600ms ease;
}
.banner-slide.active {
  opacity: 1;
  visibility: visible;
}
.banner-blur-bg {
  position: absolute;
  top: -30px;
  left: -30px;
  right: -30px;
  bottom: -30px;
  background-size: cover;
  background-position: center;
  filter: blur(28px);
  transform: scale(1.1);
  opacity: 0.9;
}
.banner-img {
  position: relative;
  z-index: 1;
  height: 80%;
  max-width: 88%;
  width: auto;
  object-fit: contain;
  border-radius: 10px;
  box-shadow: 0 6px 28px rgba(0, 0, 0, 0.3);
}

/* 轮播箭头 */
.banner-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(4px);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease;
}
.banner-arrow:hover {
  background: rgba(255, 255, 255, 0.4);
}
.banner-arrow-left {
  left: 12px;
}
.banner-arrow-right {
  right: 12px;
}
@media (max-width: 639px) {
  .banner-arrow {
    width: 32px;
    height: 32px;
  }
  .banner-arrow-left {
    left: 8px;
  }
  .banner-arrow-right {
    right: 8px;
  }
}

/* 指示器 */
.banner-indicators {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 2;
}
.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.5);
  transition: all 300ms ease;
}
.indicator-dot.active {
  background: white;
  width: 24px;
}


.stats-section {
  padding: 24px 0;
}
.stats-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 32px;
  padding: 16px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stat-icon {
  color: #3B82F6;
}
.stat-content {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #1E293B;
  font-family: 'MiSans Latin', 'HarmonyOS Sans', monospace;
}
.stat-label {
  font-size: 14px;
  color: #64748B;
}
.stat-divider {
  width: 1px;
  height: 32px;
  background: #E2E8F0;
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

.empty-hint {
  text-align: center;
  padding: 40px 0;
  color: #94A3B8;
  font-size: 14px;
}

.btn-primary {
  padding: 8px 20px;
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
.btn-primary:active {
  transform: scale(0.97);
}

.btn-secondary {
  padding: 8px 20px;
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
</style>
