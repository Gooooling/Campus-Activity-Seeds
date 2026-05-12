<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Award, Calendar, MapPin, Clock, Loader2 } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activityId = Number(route.params.id)

interface MementoData {
  title: string
  cover_image_url: string | null
  start_time: string
  end_time: string | null
  owner_name: string
  credit_type: string
  credit_value: number | null
}

const memento = ref<MementoData | null>(null)
const loading = ref(true)
const errorMsg = ref('')

async function fetchMemento() {
  loading.value = true
  errorMsg.value = ''
  try {
    const data = await request(`/participations/${activityId}/memento`)
    if (data.code === 200) {
      memento.value = data.data
    } else {
      errorMsg.value = data.message || '获取纪念卡片失败'
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
}

function goBack() {
  router.back()
}

onMounted(() => {
  fetchMemento()
})
</script>

<template>
  <div class="memento-page">
    <div v-if="loading" class="loading-state">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
      <p class="loading-text">加载中...</p>
    </div>

    <div v-else-if="errorMsg" class="error-state">
      <p class="error-text">{{ errorMsg }}</p>
      <button class="back-btn-inline" @click="goBack">返回</button>
    </div>

    <template v-else-if="memento">
      <button class="back-btn" @click="goBack">
        <ArrowLeft class="w-4 h-4" />
        <span>返回</span>
      </button>

      <div class="memento-card">
        <div class="card-cover">
          <img
            v-if="memento.cover_image_url"
            :src="memento.cover_image_url"
            :alt="memento.title"
            class="cover-img"
          />
          <div v-else class="cover-placeholder">
            <Award class="w-16 h-16 text-amber-300" />
          </div>
        </div>

        <div class="card-body">
          <div class="card-badge">
            <Award class="w-4 h-4" />
            <span>参与纪念</span>
          </div>

          <h1 class="card-title">{{ memento.title }}</h1>

          <div class="card-info">
            <div class="info-item">
              <Calendar class="w-4 h-4" />
              <span>{{ formatDate(memento.start_time) }} {{ formatTime(memento.start_time) }}</span>
              <template v-if="memento.end_time">
                <span>—</span>
                <span>{{ formatDate(memento.end_time) }} {{ formatTime(memento.end_time) }}</span>
              </template>
            </div>
            <div class="info-item">
              <Clock class="w-4 h-4" />
              <span>{{ memento.owner_name }}</span>
            </div>
          </div>

          <div class="credit-badge">
            <span class="credit-type">{{ memento.credit_type }}</span>
            <span class="credit-value">+{{ memento.credit_value ?? '-' }} 学分</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.memento-page {
  min-height: calc(100dvh - 64px);
  padding: 16px;
  max-width: 600px;
  margin: 0 auto;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 24px;
  gap: 12px;
}

.loading-text,
.error-text {
  font-size: 14px;
  color: #94A3B8;
}

.back-btn-inline {
  margin-top: 12px;
  padding: 8px 20px;
  background: #3B82F6;
  color: white;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #64748B;
  padding: 4px 0;
  margin-bottom: 16px;
  transition: color 150ms ease;
}

.back-btn:hover {
  color: #3B82F6;
}

.memento-card {
  border-radius: 16px;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-cover {
  aspect-ratio: 16 / 9;
  max-height: 240px;
  overflow: hidden;
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A855F7 100%);
  position: relative;
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

.card-body {
  padding: 24px;
}

.card-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #FFFBEB, #FEF3C7);
  border: 1px solid #FDE68A;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: #D97706;
  margin-bottom: 12px;
}

.card-title {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 16px;
  line-height: 1.4;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748B;
  flex-wrap: wrap;
}

.credit-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #F1F5F9;
}

.credit-type {
  display: inline-block;
  font-size: 13px;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.credit-value {
  display: inline-block;
  font-size: 13px;
  color: #D97706;
  background: rgba(245, 158, 11, 0.1);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
