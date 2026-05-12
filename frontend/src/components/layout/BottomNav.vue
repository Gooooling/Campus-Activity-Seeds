<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Landmark, LayoutGrid, Bell, UserCircle, CalendarDays } from 'lucide-vue-next'

const route = useRoute()
const authStore = useAuthStore()

const navItems = computed(() => {
  if (authStore.isStudent) {
    return [
      { label: '首页', path: '/', icon: Landmark },
      { label: '活动大厅', path: '/activities', icon: LayoutGrid },
      { label: '消息', path: '/notifications', icon: Bell },
      { label: '我的', path: '/profile', icon: UserCircle },
    ]
  }
  if (authStore.isOwner) {
    return [
      { label: '首页', path: '/', icon: Landmark },
      { label: '活动大厅', path: '/activities', icon: LayoutGrid },
      { label: '我的活动', path: '/my-activities', icon: CalendarDays },
      { label: '我的', path: '/owner-profile', icon: UserCircle },
    ]
  }
  return []
})

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <nav class="bottom-nav">
    <RouterLink
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      class="bottom-nav-item"
      :class="{ active: isActive(item.path) }"
    >
      <component :is="item.icon" class="w-5 h-5" />
      <span class="bottom-nav-label">{{ item.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 40;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: 56px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  padding-bottom: env(safe-area-inset-bottom);
}

@media (min-width: 768px) {
  .bottom-nav {
    display: none !important;
  }
}

.bottom-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex: 1;
  height: 100%;
  color: #94A3B8;
  transition: color 150ms ease;
}

.bottom-nav-item.active {
  color: #3B82F6;
}

.bottom-nav-label {
  font-size: 11px;
  font-weight: 500;
}
</style>
