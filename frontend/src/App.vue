<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Navbar from '@/components/layout/Navbar.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import BottomNav from '@/components/layout/BottomNav.vue'

const route = useRoute()
const authStore = useAuthStore()

const isAdminRoute = computed(() => route.path.startsWith('/admin'))
const showBottomNav = computed(() => authStore.isLoggedIn && !isAdminRoute.value)
</script>

<template>
  <div id="app-root" :class="{ 'has-bottom-nav-root': showBottomNav }">
    <Navbar v-if="!isAdminRoute" />
    <main :class="['main-content', { 'admin-content': isAdminRoute, 'has-bottom-nav': showBottomNav }]">
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
    <AppFooter v-if="!isAdminRoute" />
    <BottomNav v-if="showBottomNav" />
  </div>
</template>

<style scoped>
#app-root {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: #F8FAFC;
  font-family: 'HarmonyOS Sans', 'MiSans Latin', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.main-content {
  flex: 1;
}
.admin-content {
  padding: 0;
  margin-left: 224px;
}
.has-bottom-nav {
  padding-bottom: 56px;
}
.has-bottom-nav-root {
  padding-bottom: 56px;
}
@media (min-width: 768px) {
  .has-bottom-nav {
    padding-bottom: 0;
  }
  .has-bottom-nav-root {
    padding-bottom: 0;
  }
}

/* 页面切换淡入淡出动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 110ms ease;
}
.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
