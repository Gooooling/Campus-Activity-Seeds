<script setup lang="ts">
import { Landmark } from 'lucide-vue-next'
</script>

<template>
  <footer class="bg-white border-t border-border py-8 mt-auto">
    <div class="container">
      <div class="flex flex-col items-center gap-3 text-center">
        <div class="flex items-center gap-2 text-text-primary font-semibold">
          <Landmark class="w-5 h-5 text-primary" />
          <span>**大学 · 校园活动信息港</span>
        </div>
        <p class="text-text-secondary text-sm">
          探索你的课外生活，记录每一次精彩
        </p>
        <p class="text-text-disabled text-xs">
          © 2026 **大学 
        </p>
      </div>
    </div>
  </footer>
</template>
