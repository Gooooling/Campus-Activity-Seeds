<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import HomeGuestView from './home/HomeGuestView.vue'
import HomeStudentView from './home/HomeStudentView.vue'
import HomeOwnerView from './home/HomeOwnerView.vue'

const authStore = useAuthStore()

const homeComponent = computed(() => {
  if (!authStore.isLoggedIn) return HomeGuestView
  if (authStore.isStudent) return HomeStudentView
  if (authStore.isOwner) return HomeOwnerView
  return HomeGuestView
})
</script>

<template>
  <component :is="homeComponent" />
</template>
