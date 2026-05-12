<script setup lang="ts">
import {
  Clock,
  MapPin,
  Users,
  Star,
  Heart,
} from 'lucide-vue-next'
import type { ActivityListItem } from '@/types/activity'

const props = defineProps<{
  data: ActivityListItem
  showFavorite?: boolean
  showLocation?: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', id: number): void
  (e: 'favorite', id: number): void
}>()

function handleClick() {
  if (!props.disabled) emit('click', props.data.id)
}

function handleFavorite(e: Event) {
  e.stopPropagation()
  emit('favorite', props.data.id)
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = date.getTime() - now.getTime()
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays <= 0) return '已截止'
  if (diffDays === 1) return '明天截止'
  if (diffDays <= 3) return `${diffDays}天后截止`
  return `${date.getMonth() + 1}月${date.getDate()}日截止`
}
</script>

<template>
  <div
    class="activity-card"
    :class="{ disabled }"
    @click="handleClick"
  >
    <!-- 封面图 -->
    <div class="card-image-wrapper">
      <img
        v-if="data.cover_image_url"
        :src="data.cover_image_url"
        :alt="data.title"
        class="card-image"
        loading="lazy"
      />
      <div v-else class="card-image-placeholder">
        <Star class="w-8 h-8 text-text-disabled" />
      </div>



      <!-- 收藏按钮 -->
      <button
        v-if="showFavorite"
        class="favorite-btn"
        :class="{ active: data.is_favorited }"
        @click="handleFavorite"
      >
        <Heart class="w-4 h-4" :fill="data.is_favorited ? 'currentColor' : 'none'" />
      </button>
    </div>

    <!-- 信息区 -->
    <div class="card-body">
      <h3 class="card-title">{{ data.title }}</h3>

      <div class="card-meta">
        <span class="type-tag">{{ data.activity_type }}</span>
      </div>

      <div class="card-info">
        <span class="info-item">
          <Users class="w-3.5 h-3.5" />
          {{ data.participant_count }}人已参与
        </span>
        <span class="info-item" :class="{ 'text-danger': formatDate(data.registration_deadline) === '已截止' || formatDate(data.registration_deadline).includes('明天') }">
          <Clock class="w-3.5 h-3.5" />
          {{ formatDate(data.registration_deadline) }}
        </span>
      </div>

      <div v-if="showLocation && data.location" class="card-info">
        <span class="info-item">
          <MapPin class="w-3.5 h-3.5" />
          {{ data.location }}
        </span>
      </div>

      <div class="card-owner">
        {{ data.owner_name }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.activity-card {
  background: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  transition: transform 150ms ease, box-shadow 150ms ease;
  cursor: pointer;
}
.activity-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
}
.activity-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.activity-card.disabled:hover {
  transform: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.card-image-wrapper {
  position: relative;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #F1F5F9;
}
.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 300ms ease;
}
.activity-card:hover .card-image {
  transform: scale(1.03);
}
.card-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favorite-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  transition: all 150ms ease;
}
.favorite-btn:hover {
  background: white;
  color: #F59E0B;
}
.favorite-btn.active {
  color: #F59E0B;
}

.card-body {
  padding: 12px;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-meta {
  margin-bottom: 8px;
}
.type-tag {
  display: inline-block;
  font-size: 12px;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.card-info {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748B;
}
.info-item.text-danger {
  color: var(--color-danger);
}
.card-owner {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 4px;
}
</style>
