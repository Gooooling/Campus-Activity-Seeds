<script setup lang="ts">
import {
  BarChart3,
  LayoutDashboard,
  ClipboardCheck,
  Building2,
  CalendarDays,
  Users,
  ScrollText,
  Megaphone,
  Image,
  Settings,
  Bell,
  LogOut,
  House,
} from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}

const menuItems = [
  { label: '数据看板', path: '/admin', icon: LayoutDashboard },
  { label: '活动审核', path: '/admin/activity-audit', icon: ClipboardCheck },
  { label: '主体审核', path: '/admin/owner-audit', icon: Building2 },
  { label: '活动管理', path: '/admin/activities', icon: CalendarDays },
  { label: '用户管理', path: '/admin/users', icon: Users },
  { label: '操作日志', path: '/admin/logs', icon: ScrollText },
  { label: '公告管理', path: '/admin/announcements', icon: Megaphone },
  { label: '轮播图管理', path: '/admin/banners', icon: Image },
]
</script>

<template>
  <aside class="admin-sidebar">
    <div class="sidebar-brand">
      <BarChart3 class="w-5 h-5" />
      <span class="font-semibold">管理后台</span>
    </div>
    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="sidebar-link"
        :class="{ active: route.path === item.path }"
      >
        <component :is="item.icon" class="w-4.5 h-4.5" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
    <div class="sidebar-footer">
      <RouterLink to="/notifications" class="sidebar-link" :class="{ active: route.path === '/notifications' }">
        <Bell class="w-4.5 h-4.5" />
        <span>消息通知</span>
        <span v-if="notificationStore.unreadCount > 0" class="sidebar-badge">{{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}</span>
      </RouterLink>
      <RouterLink to="/" class="sidebar-link">
        <House class="w-4.5 h-4.5" />
        <span>返回前台</span>
      </RouterLink>
      <button class="sidebar-logout" @click="handleLogout">
        <LogOut class="w-4.5 h-4.5" />
        <span>退出登录</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.admin-sidebar {
  width: 224px;
  background: #FFFFFF;
  color: #1E293B;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: 100dvh;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 30;
  border-right: 1px solid #F1F5F9;
}

.sidebar-brand {
  padding: 20px 16px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #3B82F6;
  font-size: 15px;
}

.sidebar-nav {
  padding: 8px;
  flex: 1;
  overflow-y: auto;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #64748B;
  transition: all 150ms ease;
}

.sidebar-link:hover {
  background: #F8FAFC;
  color: #334155;
}

.sidebar-link.active {
  background: #EFF6FF;
  color: #3B82F6;
  font-weight: 500;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid #F1F5F9;
}

.sidebar-logout {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #64748B;
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  transition: all 150ms ease;
}

.sidebar-logout:hover {
  background: #FEF2F2;
  color: #EF4444;
}

.sidebar-badge {
  margin-left: auto;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: #EF4444;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
</style>
