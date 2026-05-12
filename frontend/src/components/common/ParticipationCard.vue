<script setup lang="ts">
import {
  Image,
  Calendar,
  MapPin,
  Building2,
  Clock,
  QrCode,
  Award,
  X,
} from 'lucide-vue-next'
import type { ParticipationItem } from '@/types/activity'

const props = defineProps<{
  item: ParticipationItem
}>()

const emit = defineEmits<{
  (e: 'click', id: number): void
  (e: 'viewQrcode', item: ParticipationItem): void
  (e: 'viewMemento', activityId: number): void
  (e: 'cancel', item: ParticipationItem): void
}>()

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function formatTime(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`
}

function handleClick() {
  emit('click', props.item.activity_id)
}

function stopProp(e: MouseEvent) {
  e.stopPropagation()
}
</script>

<template>
  <div class="participation-card" @click="handleClick">
    <!-- 左侧图片 28% -->
    <div class="card-cover">
      <img
        v-if="item.cover_image_url"
        :src="item.cover_image_url"
        :alt="item.title"
        class="cover-img"
        loading="lazy"
      />
      <div v-else class="cover-placeholder">
        <Image class="w-8 h-8 text-text-disabled" />
      </div>
    </div>

    <!-- 右侧内容 -->
    <div class="card-content">
      <h3 class="card-title">{{ item.title }}</h3>

      <div class="card-badges">
        <span class="badge-type">{{ item.credit_type }}</span>
        <span class="badge-credit">+{{ item.credit_value ?? '-' }}分</span>
      </div>

      <div class="card-meta">
        <span class="meta-item">
          <Calendar class="w-3.5 h-3.5" />
          {{ formatDate(item.start_time) }} {{ formatTime(item.start_time) }}
        </span>
        <span class="meta-item">
          <MapPin class="w-3.5 h-3.5" />
          {{ item.location }}
        </span>
        <span class="meta-item">
          <Building2 class="w-3.5 h-3.5" />
          {{ item.owner_name }}
        </span>
      </div>

      <!-- 底部操作栏 -->
      <div class="card-footer">
        <div class="footer-status">
          <span v-if="item.status === 'active'" class="status-active">
            <Clock class="w-3.5 h-3.5" />
            已参与 {{ formatDate(item.registration_time) }}
          </span>
          <span v-else class="status-ended">已结束</span>
        </div>
        <div class="footer-actions" @click="stopProp">
          <button
            v-if="item.status === 'active' && item.qrcode_url"
            class="action-btn btn-qrcode"
            @click="emit('viewQrcode', item)"
          >
            <QrCode class="w-3.5 h-3.5" />
            进群
          </button>
          <button
            v-if="item.can_cancel"
            class="action-btn btn-cancel"
            @click="emit('cancel', item)"
          >
            <X class="w-3.5 h-3.5" />
            取消
          </button>
          <button
            v-if="item.status === 'ended' && item.can_view_memento"
            class="action-btn btn-memento"
            @click="emit('viewMemento', item.activity_id)"
          >
            <Award class="w-3.5 h-3.5" />
            参与纪念
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.participation-card {
  display: flex;
  background: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: box-shadow 150ms ease;
}
.participation-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* ── 左侧图片 ── */
.card-cover {
  width: 28%;
  flex-shrink: 0;
  min-height: 100px;
  overflow: hidden;
  background: #F1F5F9;
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

/* ── 右侧内容 ── */
.card-content {
  flex: 1;
  min-width: 0;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-badges {
  display: flex;
  gap: 6px;
}
.badge-type {
  display: inline-block;
  font-size: 11px;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.badge-credit {
  display: inline-block;
  font-size: 11px;
  color: #D97706;
  background: rgba(245, 158, 11, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.card-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── 底部操作栏 ── */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid #F1F5F9;
}
.footer-status {
  flex-shrink: 0;
}
.status-active {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #94A3B8;
}
.status-ended {
  font-size: 11px;
  color: #94A3B8;
}
.footer-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  transition: all 150ms ease;
  cursor: pointer;
  flex-shrink: 0;
}
.btn-qrcode {
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
}
.btn-qrcode:hover {
  background: rgba(59, 130, 246, 0.2);
}
.btn-memento {
  background: rgba(245, 158, 11, 0.1);
  color: #D97706;
}
.btn-memento:hover {
  background: rgba(245, 158, 11, 0.2);
}
.btn-cancel {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
}
.btn-cancel:hover {
  background: rgba(239, 68, 68, 0.2);
}

@media (min-width: 768px) {
  .card-cover {
    width: 28%;
  }
  .card-content {
    padding: 18px 24px;
  }
  .card-title {
    font-size: 16px;
  }
  .meta-item {
    font-size: 13px;
  }
}
</style>
