<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="container py-20 text-center">
    <h1 class="text-6xl font-bold text-primary mb-4">404</h1>
    <p class="text-text-secondary mb-8">页面找不到了</p>
    <button class="btn-primary" @click="router.push('/')">返回首页</button>
  </div>
</template>