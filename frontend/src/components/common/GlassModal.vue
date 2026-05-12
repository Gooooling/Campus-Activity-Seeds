<script setup lang="ts">
import { X } from 'lucide-vue-next'

interface Props {
  modelValue: boolean
  title?: string
  showClose?: boolean
  width?: string
  closeOnOverlay?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showClose: true,
  width: '400px',
  closeOnOverlay: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

function close() {
  emit('update:modelValue', false)
  emit('close')
}

function onBackdropClick(e: MouseEvent) {
  if (props.closeOnOverlay && e.target === e.currentTarget) close()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-backdrop" @click="onBackdropClick">
        <div class="modal-glass" :style="{ maxWidth: width }">
          <div v-if="title || showClose" class="modal-header">
            <h3 v-if="title" class="modal-title">{{ title }}</h3>
            <button v-if="showClose" class="modal-close" @click="close">
              <X class="w-4 h-4" />
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" :close="close" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.modal-glass {
  width: 100%;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15), 0 4px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 0;
}
.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
}
.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748B;
  transition: all 150ms ease;
}
.modal-close:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1E293B;
}

.modal-body {
  padding: 16px 20px;
}
.modal-footer {
  padding: 0 20px 16px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 250ms ease;
}
.modal-enter-active .modal-glass,
.modal-leave-active .modal-glass {
  transition: transform 250ms ease, opacity 250ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-glass,
.modal-leave-to .modal-glass {
  transform: scale(0.95);
  opacity: 0;
}
</style>
