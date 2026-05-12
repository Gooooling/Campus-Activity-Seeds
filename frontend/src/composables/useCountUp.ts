import { ref, onMounted, onUnmounted, watch, toValue, type MaybeRefOrGetter } from 'vue'

export function useCountUp(target: MaybeRefOrGetter<number>, duration = 2000) {
  const count = ref(0)
  let animationFrame: number | null = null
  let startTime: number | null = null

  function animate(timestamp: number, targetVal: number) {
    if (!startTime) startTime = timestamp
    const progress = Math.min((timestamp - startTime) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    count.value = Math.round(eased * targetVal)
    if (progress < 1) {
      animationFrame = requestAnimationFrame((ts) => animate(ts, targetVal))
    }
  }

  function start(targetVal: number) {
    stop()
    startTime = null
    count.value = 0
    if (targetVal === 0) {
      count.value = 0
      return
    }
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      count.value = targetVal
    } else {
      animationFrame = requestAnimationFrame((ts) => animate(ts, targetVal))
    }
  }

  function stop() {
    if (animationFrame !== null) {
      cancelAnimationFrame(animationFrame)
      animationFrame = null
    }
  }

  // 监听目标值变化，数据到达后触发动画
  watch(() => toValue(target), (newVal) => {
    start(newVal)
  }, { immediate: false })

  onMounted(() => {
    const val = toValue(target)
    if (val > 0) {
      start(val)
    }
  })

  onUnmounted(() => {
    stop()
  })

  return { count }
}
