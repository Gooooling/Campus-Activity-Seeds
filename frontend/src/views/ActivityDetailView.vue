<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { ElMessage } from 'element-plus'
import GlassModal from '@/components/common/GlassModal.vue'
import ActivityInfoCard from '@/components/common/ActivityInfoCard.vue'
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Star,
  ClipboardCheck,
  FileText,
  MessageSquare,
  Pencil,
  User,
  Award,
  ChevronDown,
  ImagePlus,
  Plus,
  QrCode,
  HelpCircle,
  Loader2,
} from 'lucide-vue-next'
import type { ActivityDetail, ActivityReview } from '@/types/activity'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activityId = Number(route.params.id)

// ── 数据 ──
const activity = ref<ActivityDetail | null>(null)
const loading = ref(true)

// 评价列表
const reviews = ref<ActivityReview[]>([])
const reviewTotal = ref(0)
const reviewPage = ref(1)
const reviewLoading = ref(false)
const reviewHasMore = ref(false)

// ── 轮播 ──
const activeSlide = ref(0)
let autoplayTimer: ReturnType<typeof setInterval> | null = null

function startAutoplay() {
  stopAutoplay()
  if (!activity.value || activity.value.images.length <= 1) return
  autoplayTimer = setInterval(() => {
    activeSlide.value = (activeSlide.value + 1) % activity.value!.images.length
  }, 4000)
}

function stopAutoplay() {
  if (autoplayTimer) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

function prevSlide() {
  stopAutoplay()
  if (!activity.value) return
  activeSlide.value = (activeSlide.value - 1 + activity.value.images.length) % activity.value.images.length
}

function nextSlide() {
  stopAutoplay()
  if (!activity.value) return
  activeSlide.value = (activeSlide.value + 1) % activity.value.images.length
}

function goToSlide(index: number) {
  stopAutoplay()
  activeSlide.value = index
}

// ── 弹窗 ──
const showParticipateModal = ref(false)
const participateStep = ref<'confirm' | 'qrcode'>('confirm')
const participateLoading = ref(false)
const qrcodeUrl = ref('')

const showReviewModal = ref(false)
const reviewRating = ref(0)
const reviewContent = ref('')
const reviewSubmitting = ref(false)

// ── 日期格式化 ──
function formatReviewDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

// ── 计算属性 ──
const isDeadlinePassed = computed(() => {
  if (!activity.value) return false
  return new Date(activity.value.registration_deadline) < new Date()
})

const isEnded = computed(() => activity.value?.status === 'ended')

const isStudent = computed(() => authStore.isStudent)

const participateButtonState = computed<'participate' | 'participated' | 'deadline' | 'full' | 'hidden'>(() => {
  if (!isStudent.value || !activity.value) return 'hidden'
  if (activity.value.is_participated) return 'participated'
  if (isDeadlinePassed.value) return 'deadline'
  if (activity.value.max_participants > 0 && activity.value.participant_count >= activity.value.max_participants) return 'full'
  return 'participate'
})

// ── API ──
async function fetchActivity() {
  loading.value = true
  try {
    const data = await request(`/activities/${activityId}`)
    if (data.code === 200) {
      activity.value = data.data
      startAutoplay()
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function fetchReviews(reset = false) {
  if (reviewLoading.value) return
  reviewLoading.value = true
  if (reset) reviewPage.value = 1

  try {
    const params = new URLSearchParams()
    params.set('page', String(reviewPage.value))
    params.set('page_size', '10')
    const data = await request(`/activities/${activityId}/reviews?${params.toString()}`)
    if (data.code === 200) {
      if (reset) {
        reviews.value = data.data.items
      } else {
        reviews.value.push(...data.data.items)
      }
      reviewTotal.value = data.data.total
      reviewHasMore.value = reviews.value.length < data.data.total
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    reviewLoading.value = false
  }
}

function loadMoreReviews() {
  reviewPage.value++
  fetchReviews()
}

async function toggleFavorite() {
  if (!activity.value || !isStudent.value) return
  try {
    const data = await request('/favorites', {
      method: 'POST',
      body: JSON.stringify({ activity_id: activityId }),
    })
    if (data.code === 200) {
      activity.value.is_favorited = data.data.is_favorited
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

async function handleParticipate() {
  if (!activity.value) return
  participateLoading.value = true
  try {
    const data = await request('/participations', {
      method: 'POST',
      body: JSON.stringify({ activity_id: activityId }),
    })
    if (data.code === 200) {
      activity.value.is_participated = true
      qrcodeUrl.value = data.data.qrcode_url
      participateStep.value = 'qrcode'
    } else {
      ElMessage.error(data.message || '参与失败，请稍后重试')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '网络错误，请稍后重试')
  } finally {
    participateLoading.value = false
  }
}

function openParticipateModal() {
  if (activity.value?.is_participated) {
    fetchQrcode()
    participateStep.value = 'qrcode'
    showParticipateModal.value = true
  } else {
    participateStep.value = 'confirm'
    showParticipateModal.value = true
  }
}

async function fetchQrcode() {
  try {
    const data = await request(`/activities/${activityId}/qrcode`)
    if (data.code === 200) {
      qrcodeUrl.value = data.data.qrcode_url
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  }
}

function closeParticipateModal() {
  showParticipateModal.value = false
  participateStep.value = 'confirm'
}

async function submitReview() {
  if (reviewRating.value === 0 || reviewSubmitting.value) return
  reviewSubmitting.value = true
  try {
    const data = await request(`/activities/${activityId}/reviews`, {
      method: 'POST',
      body: JSON.stringify({
        rating: reviewRating.value,
        content: reviewContent.value.trim(),
      }),
    })
    if (data.code === 200) {
      showReviewModal.value = false
      reviewRating.value = 0
      reviewContent.value = ''
      fetchReviews(true)
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    reviewSubmitting.value = false
  }
}

function openReviewModal() {
  reviewRating.value = 0
  reviewContent.value = ''
  showReviewModal.value = true
}

function goBack() {
  router.back()
}

async function handlePhotoUpload(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length || !activity.value) return
  const file = input.files[0]
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过10MB')
    return
  }
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('type', 'activity_image')
    const data = await request('/upload', { method: 'POST', body: form })
    if (data.code === 200) {
      await request(`/activities/${activityId}`, {
        method: 'PUT',
        body: JSON.stringify({ images: [data.data.filename] }),
      })
      fetchActivity()
      ElMessage.success('照片上传成功')
    } else {
      ElMessage.error(data.message || '上传失败')
    }
  } catch {
    ElMessage.error('上传失败，请稍后重试')
  } finally {
    input.value = ''
  }
}

function goToOwner() {
  if (activity.value) {
    router.push(`/owners/${activity.value.owner.id}`)
  }
}

// ── 生命周期 ──
onMounted(() => {
  fetchActivity()
  fetchReviews(true)
})

onUnmounted(() => {
  stopAutoplay()
})
</script>

<template>
  <div class="detail-page">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
      <p class="loading-text">加载中...</p>
    </div>

    <template v-else-if="activity">
      <!-- 返回按钮 -->
      <button class="back-btn" @click="goBack">
        <ArrowLeft class="w-4 h-4" />
        <span>返回活动大厅</span>
      </button>

      <!-- 图片轮播 -->
      <div class="carousel">
        <img
          v-for="(img, idx) in activity.images"
          :key="img.id"
          :src="img.url"
          :alt="activity.title"
          class="carousel-img"
          :class="{ active: idx === activeSlide }"
        />
        <div v-if="activity.images.length === 0" class="carousel-placeholder">
          <ImagePlus class="w-12 h-12 text-text-disabled" />
        </div>

        <button
          v-if="activity.images.length > 1"
          class="carousel-arrow carousel-arrow-left"
          @click="prevSlide"
        >
          <ChevronLeft class="w-5 h-5" />
        </button>

        <button
          v-if="activity.images.length > 1"
          class="carousel-arrow carousel-arrow-right"
          @click="nextSlide"
        >
          <ChevronRight class="w-5 h-5" />
        </button>

        <div v-if="activity.images.length > 1" class="carousel-dots">
          <button
            v-for="(_, idx) in activity.images"
            :key="idx"
            class="carousel-dot"
            :class="{ active: idx === activeSlide }"
            @click="goToSlide(idx)"
          />
        </div>
      </div>

      <!-- 主体内容区 -->
      <div class="content-layout">
        <!-- 移动端：信息卡片 -->
        <div class="lg:hidden">
          <ActivityInfoCard
            :activity="activity"
            :is-deadline-passed="isDeadlinePassed"
            :participate-button-state="participateButtonState"
            @toggle-favorite="toggleFavorite"
            @open-participate="openParticipateModal"
            @go-to-owner="goToOwner"
          />
        </div>

        <!-- 左栏：活动详情 + 评价 -->
        <div class="content-left">
          <section class="detail-card">
            <div class="section-header">
              <FileText class="w-5 h-5 text-primary" />
              <h2 class="section-title">活动详情</h2>
            </div>
            <div class="detail-text">{{ activity.description }}</div>
          </section>

          <section class="detail-card">
            <div class="section-header">
              <MessageSquare class="w-5 h-5 text-primary" />
              <h2 class="section-title">活动评价（{{ reviewTotal }}）</h2>
              <div class="flex-1" />
              <button
                v-if="activity.allow_review"
                class="review-write-btn"
                @click="openReviewModal"
              >
                <Pencil class="w-3.5 h-3.5" />
                <span>写评价</span>
              </button>
            </div>

            <div v-if="reviews.length > 0" class="review-list">
              <div v-for="review in reviews" :key="review.id" class="review-item">
                <div class="review-avatar">
                  <User class="w-4 h-4" />
                </div>
                <div class="review-body">
                  <div class="review-meta">
                    <span class="review-name">{{ review.reviewer_name }}</span>
                    <div class="review-stars">
                      <Star
                        v-for="i in 5"
                        :key="i"
                        class="review-star"
                        :class="i <= review.rating ? 'filled' : 'empty'"
                      />
                    </div>
                  </div>
                  <p class="review-content">{{ review.content }}</p>
                  <p class="review-date">{{ formatReviewDate(review.created_at) }}</p>
                </div>
              </div>
            </div>

            <div v-else class="review-empty">
              <p>暂无评价</p>
            </div>

            <div v-if="reviewHasMore" class="review-more">
              <button class="review-more-btn" @click="loadMoreReviews">
                <ChevronDown class="w-4 h-4" />
                <span>查看更多评价</span>
              </button>
            </div>
            <div v-if="reviewLoading" class="review-loading">
              <Loader2 class="w-4 h-4 animate-spin text-primary" />
              <span>加载中...</span>
            </div>
          </section>

          <!-- 参与纪念卡片入口 -->
          <div v-if="isEnded && activity.is_participated" class="memento-banner">
            <Award class="w-5 h-5 text-amber-500 shrink-0" />
            <p class="memento-text">
              你已参与本次活动，点击查看你的
              <router-link
                :to="`/participations/${activityId}/memento`"
                class="memento-link"
              >
                参与纪念卡片
                <ChevronRight class="w-3 h-3 inline" />
              </router-link>
            </p>
          </div>

          <!-- 追加现场照片 -->
          <section v-if="activity.allow_edit" class="detail-card">
            <div class="section-header">
              <ImagePlus class="w-5 h-5 text-primary" />
              <h2 class="section-title">追加现场照片</h2>
            </div>
            <div class="photo-grid">
              <div
                v-for="img in activity.images"
                :key="img.id"
                class="photo-thumb"
              >
                <img :src="img.url" :alt="activity.title" class="photo-img" />
              </div>
              <label class="photo-upload">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/gif,image/webp,image/bmp"
                  class="hidden"
                  @change="handlePhotoUpload"
                />
                <Plus class="w-6 h-6 text-text-disabled" />
              </label>
            </div>
          </section>
        </div>

        <!-- 桌面端：右侧粘性信息卡 -->
        <div class="hidden lg:block content-right">
          <ActivityInfoCard
            :activity="activity"
            :is-deadline-passed="isDeadlinePassed"
            :participate-button-state="participateButtonState"
            @toggle-favorite="toggleFavorite"
            @open-participate="openParticipateModal"
            @go-to-owner="goToOwner"
          />
        </div>
      </div>
    </template>

    <!-- 加载失败 -->
    <div v-else class="loading-state">
      <p class="loading-text">加载失败，请稍后重试</p>
    </div>

    <!-- 参与确认 / 二维码弹窗 -->
    <GlassModal v-model="showParticipateModal" :show-close="false" width="360px">
      <template v-if="participateStep === 'confirm'">
        <div class="modal-center">
          <HelpCircle class="w-10 h-10 text-primary mx-auto mb-3" />
          <h3 class="modal-heading">确认参与</h3>
          <p class="modal-desc">确认后将显示活动群二维码，方便你加入活动群聊。</p>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="closeParticipateModal">取消</button>
          <button
            class="btn-primary"
            :disabled="participateLoading"
            @click="handleParticipate"
          >
            <Loader2 v-if="participateLoading" class="w-4 h-4 animate-spin" />
            <ClipboardCheck v-else class="w-4 h-4" />
            <span>确认参与</span>
          </button>
        </div>
      </template>

      <template v-else>
        <div class="modal-center">
          <QrCode class="w-10 h-10 text-primary mx-auto mb-3" />
          <h3 class="modal-heading">活动群二维码</h3>
          <div v-if="qrcodeUrl" class="qrcode-wrapper">
            <img :src="qrcodeUrl" alt="群二维码" class="qrcode-img" />
          </div>
          <div v-else class="qrcode-empty-state">
            <QrCode class="w-12 h-12 text-text-disabled mb-2" />
            <p>活动方未上传群二维码</p>
          </div>
          <p class="modal-desc">请使用微信扫码加入活动群</p>
        </div>
        <div class="modal-actions">
          <button class="btn-primary w-full" @click="closeParticipateModal">知道了</button>
        </div>
      </template>
    </GlassModal>

    <!-- 写评价弹窗 -->
    <GlassModal v-model="showReviewModal" title="写评价" width="400px">
      <div class="review-form">
        <p class="review-form-label">活动评分</p>
        <div class="rating-stars">
          <button
            v-for="i in 5"
            :key="i"
            class="rating-star-btn"
            @click="reviewRating = i"
          >
            <Star
              class="w-8 h-8"
              :class="i <= reviewRating ? 'text-amber-400 fill-amber-400' : 'text-slate-200'"
            />
          </button>
        </div>

        <p class="review-form-label mt-4">评价内容</p>
        <textarea
          v-model="reviewContent"
          class="review-textarea"
          placeholder="分享你的参与感受..."
          maxlength="200"
          rows="4"
        />
        <p class="review-char-count">{{ reviewContent.length }}/200</p>
      </div>
      <template #footer="{ close }">
        <button class="btn-secondary" @click="close">取消</button>
        <button
          class="btn-primary"
          :disabled="reviewRating === 0 || reviewSubmitting"
          @click="submitReview"
        >
          <Loader2 v-if="reviewSubmitting" class="w-4 h-4 animate-spin" />
          <span>提交评价</span>
        </button>
      </template>
    </GlassModal>
  </div>
</template>

<style scoped>
/* ── 页面容器 ── */
.detail-page {
  min-height: calc(100dvh - 64px);
  padding: 16px;
  max-width: 1152px;
  margin: 0 auto;
}
@media (min-width: 1024px) {
  .detail-page {
    padding: 24px 32px 48px;
  }
}

/* ── 加载状态 ── */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 24px;
  gap: 12px;
}
.loading-text {
  font-size: 14px;
  color: #94A3B8;
}

/* ── 返回按钮 ── */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #64748B;
  padding: 4px 0;
  margin-bottom: 12px;
  transition: color 150ms ease;
}
.back-btn:hover {
  color: #3B82F6;
}

/* ── 轮播 ── */
.carousel {
  position: relative;
  aspect-ratio: 16 / 9;
  max-height: 320px;
  border-radius: 12px;
  overflow: hidden;
  background: #F1F5F9;
}
@media (min-width: 1024px) {
  .carousel {
    max-height: 480px;
    border-radius: 16px;
  }
}
.carousel-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  inset: 0;
  opacity: 0;
  visibility: hidden;
  transition: opacity 400ms ease, visibility 400ms ease;
}
.carousel-img.active {
  opacity: 1;
  visibility: visible;
}
.carousel-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 200ms ease;
}
.carousel:hover .carousel-arrow {
  opacity: 1;
}
@media (max-width: 1023px) {
  .carousel-arrow {
    opacity: 1;
  }
}
.carousel-arrow-left {
  left: 8px;
}
.carousel-arrow-right {
  right: 8px;
}
@media (min-width: 1024px) {
  .carousel-arrow {
    width: 40px;
    height: 40px;
  }
  .carousel-arrow-left {
    left: 16px;
  }
  .carousel-arrow-right {
    right: 16px;
  }
}
.carousel-dots {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
}
@media (min-width: 1024px) {
  .carousel-dots {
    bottom: 16px;
    gap: 8px;
  }
}
.carousel-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  transition: all 300ms ease;
}
.carousel-dot.active {
  width: 24px;
  border-radius: 3px;
  background: white;
}

/* ── 内容布局 ── */
.content-layout {
  margin-top: 16px;
}
@media (min-width: 1024px) {
  .content-layout {
    display: flex;
    gap: 24px;
    margin-top: 24px;
  }
}
.content-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
@media (min-width: 1024px) {
  .content-left {
    width: 60%;
  }
}
.content-right {
  width: 40%;
}

/* ── 详情卡片通用 ── */
.detail-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
}
.detail-text {
  font-size: 14px;
  color: #475569;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ── 评价 ── */
.review-write-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
  font-size: 13px;
  font-weight: 500;
  border-radius: 20px;
  transition: background 150ms ease;
  white-space: nowrap;
}
.review-write-btn:hover {
  background: rgba(59, 130, 246, 0.2);
}
.review-list {
  display: flex;
  flex-direction: column;
}
.review-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #F1F5F9;
}
.review-item:last-child {
  border-bottom: none;
}
.review-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3B82F6;
  flex-shrink: 0;
}
.review-body {
  flex: 1;
  min-width: 0;
}
.review-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.review-name {
  font-size: 14px;
  font-weight: 500;
  color: #1E293B;
}
.review-stars {
  display: flex;
  gap: 2px;
}
.review-star {
  width: 14px;
  height: 14px;
}
.review-star.filled {
  fill: #F59E0B;
  color: #F59E0B;
}
.review-star.empty {
  color: #E2E8F0;
}
.review-content {
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
  word-break: break-word;
}
.review-date {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 4px;
}
.review-empty {
  text-align: center;
  padding: 24px 0;
  color: #94A3B8;
  font-size: 14px;
}
.review-more {
  display: flex;
  justify-content: center;
  padding-top: 12px;
}
.review-more-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #3B82F6;
  padding: 6px 16px;
  border-radius: 8px;
  transition: background 150ms ease;
}
.review-more-btn:hover {
  background: rgba(59, 130, 246, 0.06);
}
.review-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 0;
  font-size: 13px;
  color: #94A3B8;
}

/* ── 纪念卡片入口 ── */
.memento-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
  background: linear-gradient(to right, #FFFBEB, #FFF7ED);
  border: 1px solid #FDE68A;
}
.memento-text {
  font-size: 14px;
  color: #475569;
}
.memento-link {
  color: #3B82F6;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  text-decoration: none;
}
.memento-link:hover {
  text-decoration: underline;
}

/* ── 追加照片 ── */
.photo-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.photo-thumb {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
}
.photo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.photo-upload {
  aspect-ratio: 1;
  border-radius: 8px;
  border: 2px dashed #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms ease;
}
.photo-upload:hover {
  border-color: #3B82F6;
  background: rgba(59, 130, 246, 0.04);
}

/* ── 弹窗内容 ── */
.modal-center {
  text-align: center;
  padding: 8px 0;
}
.modal-heading {
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 8px;
}
.modal-desc {
  font-size: 14px;
  color: #64748B;
  line-height: 1.6;
}
.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
.qrcode-wrapper {
  margin: 16px auto;
  width: 176px;
  height: 176px;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
  padding: 8px;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.qrcode-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.qrcode-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 16px auto;
  width: 176px;
  height: 176px;
  border-radius: 8px;
  border: 1px dashed #E2E8F0;
  background: #F8FAFC;
  color: #94A3B8;
  font-size: 13px;
}

/* ── 评价表单 ── */
.review-form {
  padding: 4px 0;
}
.review-form-label {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}
.rating-stars {
  display: flex;
  gap: 4px;
  justify-content: center;
}
.rating-star-btn {
  padding: 4px;
  transition: transform 150ms ease;
}
.rating-star-btn:hover {
  transform: scale(1.15);
}
.review-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
  color: #1E293B;
  resize: none;
  transition: all 150ms ease;
  font-family: inherit;
  line-height: 1.6;
}
.review-textarea::placeholder {
  color: #94A3B8;
}
.review-textarea:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.review-char-count {
  font-size: 12px;
  color: #94A3B8;
  text-align: right;
  margin-top: 4px;
}

/* ── 通用按钮 ── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  background: #3B82F6;
  color: white;
  font-size: 14px;
  font-weight: 500;
  border-radius: 10px;
  transition: all 150ms ease;
}
.btn-primary:hover {
  background: #2563EB;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary.w-full {
  width: 100%;
}
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 20px;
  background: #F1F5F9;
  color: #475569;
  font-size: 14px;
  font-weight: 500;
  border-radius: 10px;
  transition: all 150ms ease;
}
.btn-secondary:hover {
  background: #E2E8F0;
}

/* ── 动画 ── */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
