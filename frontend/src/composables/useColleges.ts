import { ref } from 'vue'
import { request } from '@/utils/request'

export interface CollegeItem {
  id: number
  name: string
}

const colleges = ref<CollegeItem[]>([])
const loaded = ref(false)

export function useColleges() {
  async function fetchColleges() {
    if (loaded.value) return
    try {
      const data = await request<CollegeItem[]>('/users/colleges')
      if (data.code === 200) {
        colleges.value = data.data
        loaded.value = true
      }
    } catch {
      // 降级：使用空列表
    }
  }

  return { colleges, fetchColleges }
}
