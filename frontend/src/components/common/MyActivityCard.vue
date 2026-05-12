<script setup lang="ts">
import {
  Pencil,
  Trash2,
  Camera,
  AlertTriangle,
  FileEdit,
  Clock,
  CheckCircle2,
  CheckCheck,
  XCircle,
} from 'lucide-vue-next'
import ActivityCard from '@/components/common/ActivityCard.vue'
import type { MyActivityItem } from '@/types/activity'

const props = defineProps<{
  data: MyActivityItem
}>()

const emit = defineEmits<{
  (e: 'click', id: number): void
  (e: 'edit', id: number): void
  (e: 'delete', id: number): void
  (e: 'addPhotos', id: number): void
}>()

type ActivityStatus = 'draft' | 'pending' | 'active' | 'ended' | 'rejected'

const statusConfig: Record<ActivityStatus, { label: string; bgClass: string; textClass: string; icon: typeof FileEdit }> = {
  draft: { label: '草稿', bgClass: 'status-bg-draft', textClass: 'status-text-draft', icon: FileEdit },
  pending: { label: '待审核', bgClass: 'status-bg-pending', textClass: 'status-text-pending', icon: Clock },
  active: { label: '报名中', bgClass: 'status-bg-active', textClass: 'status-text-active', icon: CheckCircle2 },
  ended: { label: '已结束', bgClass: 'status-bg-ended', textClass: 'status-text-ended', icon: CheckCheck },
  rejected: { label: '已驳回', bgClass: 'status-bg-rejected', textClass: 'status-text-rejected', icon: XCircle },
}

function getStatusConfig(status: string) {
  return statusConfig[status as ActivityStatus] ?? statusConfig.draft
}

const canEdit = ['draft', 'pending', 'active', 'rejected'].includes(props.data.status)
const canDelete = ['draft', 'pending', 'active', 'rejected'].includes(props.data.status)
const canAddPhotos = props.data.status === 'ended'
const isDeleteDisabled = props.data.status === 'ended'
</script>

<template>
  <div class="my-activity-card">
    <!-- 状态标签（叠加在 ActivityCard 封面图右上角） -->
    <div class="card-wrapper">
      <div class="status-badge" :class="[getStatusConfig(data.status).bgClass, getStatusConfig(data.status).textClass]">
        <component :is="getStatusConfig(data.status).icon" class="w-3 h-3" />
        {{ getStatusConfig(data.status).label }}
      </div>
      <ActivityCard
        :data="data"
        :show-favorite="false"
        :show-location="false"
        @click="emit('click', $event)"
      />
    </div>

    <!-- 驳回原因 -->
    <div v-if="data.status === 'rejected' && data.reject_reason" class="reject-reason">
      <AlertTriangle class="w-4 h-4 shrink-0" />
      <span>驳回原因：{{ data.reject_reason }}</span>
    </div>

    <!-- 操作按钮行 -->
    <div class="action-bar">
      <button
        v-if="canEdit"
        class="action-btn action-edit"
        @click.stop="emit('edit', data.id)"
      >
        <Pencil class="w-3.5 h-3.5" />
        {{ data.status === 'rejected' ? '去修改' : '编辑' }}
      </button>

      <button
        v-if="canAddPhotos"
        class="action-btn action-photos"
        @click.stop="emit('addPhotos', data.id)"
      >
        <Camera class="w-3.5 h-3.5" />
        追加照片
      </button>

      <button
        v-if="canDelete || isDeleteDisabled"
        class="action-btn action-delete"
        :class="{ disabled: isDeleteDisabled }"
        :disabled="isDeleteDisabled"
        :title="isDeleteDisabled ? '已结束活动不可删除，请联系管理员' : ''"
        @click.stop="!isDeleteDisabled && emit('delete', data.id)"
      >
        <Trash2 class="w-3.5 h-3.5" />
        删除
      </button>
    </div>
  </div>
</template>

<style scoped>
.my-activity-card {
  background: #FFFFFF;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.card-wrapper {
  position: relative;
}

/* 隐藏 ActivityCard 自身的 hover 效果，由外层统一管理 */
.card-wrapper :deep(.activity-card) {
  box-shadow: none;
  border-radius: 0;
}
.card-wrapper :deep(.activity-card:hover) {
  transform: none;
  box-shadow: none;
}

.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.status-bg-draft { background: rgba(241, 245, 249, 0.92); }
.status-text-draft { color: #475569; }

.status-bg-pending { background: rgba(255, 251, 235, 0.92); }
.status-text-pending { color: #B45309; }

.status-bg-active { background: rgba(236, 253, 245, 0.92); }
.status-text-active { color: #047857; }

.status-bg-ended { background: rgba(238, 242, 255, 0.92); }
.status-text-ended { color: #4338CA; }

.status-bg-rejected { background: rgba(254, 242, 242, 0.92); }
.status-text-rejected { color: #B91C1C; }

.reject-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 12px;
  padding: 10px 12px;
  background: #FFFBEB;
  border-radius: 8px;
  font-size: 13px;
  color: #92400E;
  line-height: 1.5;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid #F1F5F9;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  transition: all 150ms ease;
}

.action-edit {
  background: rgba(59, 130, 246, 0.08);
  color: #3B82F6;
}
.action-edit:hover {
  background: rgba(59, 130, 246, 0.15);
}

.action-photos {
  background: rgba(59, 130, 246, 0.08);
  color: #3B82F6;
}
.action-photos:hover {
  background: rgba(59, 130, 246, 0.15);
}

.action-delete {
  background: rgba(239, 68, 68, 0.06);
  color: var(--color-danger);
}
.action-delete:hover {
  background: rgba(239, 68, 68, 0.12);
}
.action-delete.disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.action-delete.disabled:hover {
  background: rgba(239, 68, 68, 0.06);
}
</style>
