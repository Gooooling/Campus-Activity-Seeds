import { request } from '@/utils/request'

interface SystemConfig {
  credit_types: string[]
  activity_types: string[]
  owner_types: string[]
}

let fetchPromise: Promise<SystemConfig> | null = null

export async function fetchPublicConfig(): Promise<SystemConfig> {
  // 无缓存，每次直读（与设计文档一致：配置修改需即时生效）
  if (fetchPromise) return fetchPromise
  fetchPromise = (async () => {
    const res = await request('/system-config/public')
    fetchPromise = null
    if (res.code === 200 && res.data) {
      return res.data as SystemConfig
    }
    return { credit_types: [], activity_types: [], owner_types: [] }
  })()
  return fetchPromise
}
