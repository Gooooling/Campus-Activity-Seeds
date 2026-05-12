<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import {
  Landmark,
  LayoutGrid,
  FileEdit,
  Send,
  Bell,
  UserCircle,
  LogOut,
  ChevronDown,
  Settings,
  Menu,
  X,
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const mobileMenuOpen = ref(false)
const avatarDropdownOpen = ref(false)
const isMobile = ref(window.innerWidth < 768)

const navItems = computed(() => {
  const items = [{ label: '首页', path: '/', icon: Landmark }]

  if (authStore.isLoggedIn) {
    items.push({ label: '活动大厅', path: '/activities', icon: LayoutGrid })
  }

  if (authStore.isOwner) {
    items.push(
      { label: '我的活动', path: '/my-activities', icon: FileEdit },
      { label: '发布活动', path: '/publish', icon: Send }
    )
  }

  return items
})

function handleResize() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    mobileMenuOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  if (authStore.isLoggedIn) {
    notificationStore.startPolling()
  }
})

watch(() => authStore.isLoggedIn, (loggedIn) => {
  if (loggedIn) {
    notificationStore.startPolling()
  } else {
    notificationStore.stopPolling()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  notificationStore.stopPolling()
})

async function handleLogout() {
  await authStore.logout()
  avatarDropdownOpen.value = false
  router.push('/')
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>

<template>
  <nav class="navbar-glass sticky top-0 z-50">
    <div class="container flex items-center justify-between h-16">
      <!-- Logo -->
      <RouterLink to="/" class="flex items-center gap-2 text-primary font-bold text-lg">
        <Landmark class="w-6 h-6" />
        <span class="hidden sm:inline">校园活动信息港</span>
        <span class="sm:hidden">校园活动信息港</span>
      </RouterLink>

      <!-- Desktop Nav -->
      <div class="hidden md:flex items-center gap-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: $route.path === item.path }"
        >
          <component :is="item.icon" class="w-4 h-4" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </div>

      <!-- Right Section -->
      <div class="flex items-center gap-3">
        <!-- Notifications -->
        <RouterLink v-if="authStore.isLoggedIn" to="/notifications" class="nav-icon-btn relative">
          <Bell class="w-5 h-5" />
          <span
            v-if="notificationStore.unreadCount > 0"
            class="absolute -top-1 -right-1 w-4 h-4 bg-danger text-white text-xs rounded-full flex items-center justify-center"
          >
            {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
          </span>
        </RouterLink>

        <!-- Auth Buttons (Guest) -->
        <template v-if="!authStore.isLoggedIn">
          <RouterLink to="/login" class="btn-text">登录</RouterLink>
          <RouterLink to="/register" class="btn-primary-sm">注册</RouterLink>
        </template>

        <!-- Avatar Dropdown (Logged In) -->
        <div v-else class="relative">
          <button
            class="flex items-center gap-1.5 p-1.5 rounded-full hover:bg-black/5 transition-colors"
            @click="avatarDropdownOpen = !avatarDropdownOpen"
          >
            <img
              v-if="authStore.user?.avatar_url"
              :src="authStore.user.avatar_url"
              alt=""
              class="w-8 h-8 rounded-full object-cover"
            />
            <div v-else class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
              <UserCircle class="w-5 h-5" />
            </div>
            <ChevronDown class="w-4 h-4 text-text-secondary" />
          </button>

          <!-- Dropdown Menu -->
          <div
            v-if="avatarDropdownOpen"
            class="absolute right-0 top-full mt-2 w-60 bg-white rounded-lg shadow-lg py-2 border border-border/60"
            @mouseleave="avatarDropdownOpen = false"
          >
            <!-- 用户信息（与菜单项共享同一 flex 对齐） -->
            <div class="dropdown-item user-info">
              <span class="dropdown-icon"></span>
              <div class="dropdown-label">
                <p class="drop-name">{{ authStore.user?.name || '用户' }}</p>
                <p class="drop-college">{{ authStore.user?.college_name || '' }}</p>
              </div>
            </div>
            <div class="mx-4 border-t border-border/60 mb-1" />
            <RouterLink
              v-if="authStore.isStudent"
              to="/profile"
              class="dropdown-item"
              @click="avatarDropdownOpen = false"
            >
              <span class="dropdown-icon"><UserCircle class="w-4 h-4" /></span>
              <span class="dropdown-label">个人中心</span>
            </RouterLink>
            <RouterLink
              v-if="authStore.isOwner"
              to="/owner-profile"
              class="dropdown-item"
              @click="avatarDropdownOpen = false"
            >
              <span class="dropdown-icon"><Settings class="w-4 h-4" /></span>
              <span class="dropdown-label">个人中心</span>
            </RouterLink>
            <RouterLink
              v-if="authStore.isAdmin"
              to="/admin"
              class="dropdown-item"
              @click="avatarDropdownOpen = false"
            >
              <span class="dropdown-icon"><Settings class="w-4 h-4" /></span>
              <span class="dropdown-label">管理后台</span>
            </RouterLink>
            <div class="mx-4 border-t border-border/60 my-1" />
            <button class="dropdown-item w-full text-danger" @click="handleLogout">
              <span class="dropdown-icon"><LogOut class="w-4 h-4" /></span>
              <span class="dropdown-label">退出登录</span>
            </button>
          </div>
        </div>

        <!-- Mobile Menu Toggle -->
        <button v-if="isMobile" class="nav-icon-btn" @click="toggleMobileMenu">
          <Menu v-if="!mobileMenuOpen" class="w-5 h-5" />
          <X v-else class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div v-if="mobileMenuOpen && isMobile" class="border-t border-border/50 bg-white/90 backdrop-blur-md">
      <div class="container py-3 flex flex-col gap-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="mobile-nav-link"
          :class="{ active: $route.path === item.path }"
          @click="closeMobileMenu"
        >
          <component :is="item.icon" class="w-5 h-5" />
          <span>{{ item.label }}</span>
        </RouterLink>
        <template v-if="!authStore.isLoggedIn">
          <RouterLink to="/login" class="mobile-nav-link" @click="closeMobileMenu">
            <LogOut class="w-5 h-5" /> 登录
          </RouterLink>
          <RouterLink to="/register" class="mobile-nav-link" @click="closeMobileMenu">
            <UserCircle class="w-5 h-5" /> 注册
          </RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar-glass {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  transition: all 150ms ease;
}
.nav-link:hover {
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.08);
}
.nav-link.active {
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.12);
}

.nav-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  color: #64748B;
  transition: all 150ms ease;
}
.nav-icon-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1E293B;
}

.btn-text {
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 150ms ease;
}
.btn-text:hover {
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.08);
}

.btn-primary-sm {
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: #3B82F6;
  padding: 6px 16px;
  border-radius: 8px;
  transition: all 150ms ease;
}
.btn-primary-sm:hover {
  background: #2563EB;
}
.btn-primary-sm:active {
  transform: scale(0.97);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 11px 16px;
  color: #334155;
  transition: background 150ms ease;
}
.dropdown-item:hover {
  background: #F1F5F9;
}
.dropdown-item.user-info {
  cursor: default;
}
.dropdown-item.user-info:hover {
  background: transparent;
}
.dropdown-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  flex-shrink: 0;
  color: #94a3b8;
}
.dropdown-label {
  line-height: 1.5;
  padding-left: 6px;
}
.drop-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
}
.drop-college {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  color: #64748B;
  transition: all 150ms ease;
}
.mobile-nav-link:hover,
.mobile-nav-link.active {
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.08);
}
</style>
