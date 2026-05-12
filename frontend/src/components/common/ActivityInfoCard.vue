<script setup lang="ts">
import {
  Tag,
  Zap,
  Calendar,
  MapPin,
  Clock,
  Users,
  Star,
  ClipboardCheck,
  CheckCircle2,
  ChevronRight,
  User,
} from 'lucide-vue-next'
import type { ActivityDetail } from '@/types/activity'

const props = defineProps<{
  activity: ActivityDetail
  isDeadlinePassed: boolean
  participateButtonState: 'participate' | 'participated' | 'deadline' | 'full' | 'hidden'
}>()

const emit = defineEmits<{
  toggleFavorite: []
  openParticipate: []
  goToOwner: []
}>()

function formatDateTimeRange(start: string, end: string): string {
  const s = new Date(start)
  const e = new Date(end)
  const sameDay = s.getFullYear() === e.getFullYear()
    && s.getMonth() === e.getMonth()
    && s.getDate() === e.getDate()
  const fmt = (d: Date) => `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
  if (sameDay) {
    return `${s.getFullYear()}年${s.getMonth() + 1}月${s.getDate()}日 ${fmt(s)} - ${fmt(e)}`
  }
  return `${s.getFullYear()}年${s.getMonth() + 1}月${s.getDate()}日 ${fmt(s)} - ${e.getFullYear()}年${e.getMonth() + 1}月${e.getDate()}日 ${fmt(e)}`
}

function formatDeadline(dateStr: string): string {
  const d = new Date(dateStr)
  const h = d.getHours()
  const period = h < 12 ? '上午' : h === 12 ? '中午' : '下午'
  const displayH = h > 12 ? h - 12 : h
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日${period}${displayH}:${min}截止`
}
</script>

<template>
  <div class="info-card">
    <h1 class="info-title">{{ activity.title }}</h1>

    <div class="info-badges">
      <span class="badge badge-type">
        <Tag class="w-3 h-3" />
        {{ activity.credit_type }}
      </span>
      <span class="badge badge-credit">
        <Zap class="w-3 h-3" />
        +{{ activity.credit_value ?? '-' }} 学分
      </span>
    </div>

    <div class="info-divider" />

    <button class="owner-row" @click="emit('goToOwner')">
      <img
        v-if="activity.owner.avatar_url"
        :src="activity.owner.avatar_url"
        :alt="activity.owner.name"
        class="owner-avatar"
      />
      <div v-else class="owner-avatar owner-avatar-placeholder">
        <User class="w-5 h-5" />
      </div>
      <span class="owner-name">{{ activity.owner.name }}</span>
      <ChevronRight class="w-4 h-4 text-slate-400 shrink-0" />
    </button>

    <div class="info-divider" />

    <div class="info-rows">
      <div class="info-row">
        <Calendar class="info-row-icon" />
        <span class="info-row-label">活动时间</span>
        <span class="info-row-value">{{ formatDateTimeRange(activity.start_time, activity.end_time) }}</span>
      </div>
      <div class="info-row">
        <MapPin class="info-row-icon" />
        <span class="info-row-label">地点</span>
        <span class="info-row-value">{{ activity.location }}</span>
      </div>
      <div class="info-row">
        <Clock class="info-row-icon" />
        <span class="info-row-label">报名截止</span>
        <span class="info-row-value">{{ formatDeadline(activity.registration_deadline) }}</span>
      </div>
      <div class="info-row">
        <Users class="info-row-icon" />
        <span class="info-row-label">参与人数</span>
        <span class="info-row-value">
          {{ activity.participant_count }} 人
          <template v-if="activity.max_participants > 0"> / 限报 {{ activity.max_participants }} 人</template>
          <span class="info-row-hint">（仅供参考）</span>
        </span>
      </div>
    </div>

    <div class="info-divider" />

    <div class="action-buttons">
      <button
        v-if="participateButtonState !== 'hidden'"
        class="action-btn action-fav"
        :class="{ 'action-fav-active': activity.is_favorited }"
        @click="emit('toggleFavorite')"
      >
        <Star class="w-4 h-4" :fill="activity.is_favorited ? 'currentColor' : 'none'" />
        <span>{{ activity.is_favorited ? '已收藏' : '收藏' }}</span>
      </button>

      <div class="action-participate-wrap" v-if="participateButtonState === 'participate' || participateButtonState === 'full'">
        <button
          class="action-btn action-participate"
          @click="emit('openParticipate')"
        >
          <ClipboardCheck class="w-4 h-4" />
          <span>我要参与（可获取进群方式）</span>
        </button>
        <span v-if="participateButtonState === 'full'" class="full-hint">名额紧张（仅供参考，请以实际为准）</span>
      </div>

      <button
        v-else-if="participateButtonState === 'participated'"
        class="action-btn action-participated"
        @click="emit('openParticipate')"
      >
        <CheckCircle2 class="w-4 h-4" />
        <span>已参与（查看进群方式）</span>
      </button>

      <button
        v-else-if="participateButtonState === 'deadline'"
        class="action-btn action-deadline"
        disabled
      >
        <span>{{ formatDeadline(activity.registration_deadline) }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.info-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  margin-bottom: 16px;
}
@media (min-width: 1024px) {
  .info-card {
    position: sticky;
    top: 80px;
    margin-bottom: 0;
  }
}
.info-title {
  font-size: 20px;
  font-weight: 700;
  color: #1E293B;
  line-height: 1.4;
}
@media (min-width: 1024px) {
  .info-title {
    font-size: 24px;
  }
}
.info-badges {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}
.badge-type {
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
}
.badge-credit {
  background: rgba(245, 158, 11, 0.1);
  color: #D97706;
}
.info-divider {
  height: 1px;
  background: #F1F5F9;
  margin: 14px 0;
}
.owner-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  text-align: left;
  transition: opacity 150ms ease;
}
.owner-row:hover {
  opacity: 0.8;
}
.owner-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
@media (min-width: 1024px) {
  .owner-avatar {
    width: 40px;
    height: 40px;
  }
}
.owner-avatar-placeholder {
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3B82F6;
}
.owner-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (min-width: 1024px) {
  .owner-name {
    font-size: 15px;
  }
}
.info-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.info-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.info-row-icon {
  width: 16px;
  height: 16px;
  color: #94A3B8;
  margin-top: 2px;
  flex-shrink: 0;
}
.info-row-label {
  font-size: 12px;
  color: #94A3B8;
  width: 56px;
  flex-shrink: 0;
}
@media (min-width: 1024px) {
  .info-row-label {
    width: 64px;
  }
}
.info-row-value {
  font-size: 14px;
  color: #1E293B;
  min-width: 0;
  word-break: break-all;
}
.info-row-hint {
  font-size: 12px;
  color: #94A3B8;
  margin-left: 4px;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 10px;
  transition: all 150ms ease;
  cursor: pointer;
}
.action-fav {
  flex: 1;
  padding: 10px 0;
  border: 1px solid #E2E8F0;
  color: #64748B;
  background: white;
}
.action-fav:hover {
  background: #F8FAFC;
}
.action-fav-active {
  color: #F59E0B;
  border-color: #FDE68A;
  background: #FFFBEB;
}
.action-fav-active:hover {
  background: #FEF3C7;
}
.action-participate-wrap {
  flex: 2;
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-participate {
  flex: 1;
  padding: 10px 0;
  background: #3B82F6;
  color: white;
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
}
.action-participate:hover {
  background: #2563EB;
}
.full-hint {
  font-size: 12px;
  font-weight: 500;
  color: #F97316;
  white-space: nowrap;
}
.action-participated {
  flex: 2;
  padding: 10px 0;
  background: #ECFDF5;
  color: #059669;
  border: 1px solid #A7F3D0;
}
.action-participated:hover {
  background: #D1FAE5;
}
.action-deadline {
  flex: 2;
  padding: 10px 0;
  background: #F1F5F9;
  color: #94A3B8;
  cursor: not-allowed;
}
</style>
