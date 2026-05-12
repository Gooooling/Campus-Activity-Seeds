/**
 * 统一请求封装
 * - 自动携带 Cookie（httpOnly）进行认证
 * - 区分登录请求 vs 业务请求
 * - 401/403 分流处理
 */
import router from '@/router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const BASE_URL = '/api'

/** 连续 403 计数器 */
let _consecutive403Count = 0
const _403_KICK_THRESHOLD = 3

/** 后端统一响应结构 */
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message?: string
}

/** 判断是否为认证相关请求（不应被拦截器统一处理） */
function isAuthRequest(url: string): boolean {
  return url === '/auth/login' || url === '/auth/register/student' || url === '/auth/register/owner'
}

/** 判断当前是否在登录/注册页 */
function isOnLoginPage(): boolean {
  return router.currentRoute.value.path === '/login' || router.currentRoute.value.path === '/register'
}

/** 判断当前是否在公开页面（无需登录） */
function isOnPublicPage(): boolean {
  return !!router.currentRoute.value.meta.public
}

/**
 * 统一 fetch 请求函数
 */
export async function request<T>(
  url: string,
  options?: RequestInit,
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string> ?? {}),
  }
  if (options?.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json; charset=utf-8'
  }

  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  // 401 处理
  if (res.status === 401) {
    if (isAuthRequest(url)) {
      let msg = '账号或密码错误'
      try {
        const json = await res.json()
        msg = json.detail || json.message || msg
      } catch { /* 解析失败用默认消息 */ }
      return { code: 401, data: null as unknown as T, message: msg }
    }

    // 公开页面（如主页）的 401：静默返回，不弹提示不跳转
    if (isOnPublicPage()) {
      return { code: 401, data: null as unknown as T, message: '未登录' }
    }

    const authStore = useAuthStore()
    ElMessage.warning('登录已过期，请重新登录')
    await authStore.logout()
    if (router.currentRoute.value.path !== '/login') {
      router.push('/login')
    }
    return { code: 401, data: null as unknown as T, message: '登录已过期，请重新登录' }
  }

  // 403 处理
  if (res.status === 403) {
    let serverMessage = '无权访问'
    try {
      const json = await res.json()
      serverMessage = json.detail || json.message || '无权访问'
    } catch { /* 解析失败用默认消息 */ }

    if (isAuthRequest(url) || isOnLoginPage()) {
      return { code: 403, data: null as unknown as T, message: serverMessage }
    }

    _consecutive403Count++
    if (_consecutive403Count >= _403_KICK_THRESHOLD) {
      _consecutive403Count = 0
      const authStore = useAuthStore()
      await authStore.logout()
      ElMessage.error('您已触发异常，请重新登录')
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
    } else {
      ElMessage.error(serverMessage)
    }
    return { code: 403, data: null as unknown as T, message: serverMessage }
  }

  // 非 403 时重置计数器
  _consecutive403Count = 0

  // 解析 JSON
  const json = await res.json()
  return json as ApiResponse<T>
}
