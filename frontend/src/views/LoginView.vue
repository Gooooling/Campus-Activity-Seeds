<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { Landmark, Lock, User, AlertCircle } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const account = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  if (!account.value || !password.value) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  errorMsg.value = ''

  try {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        account: account.value,
        password: password.value,
      }),
    })

    if (data.code === 401 || data.code === 403) {
      errorMsg.value = data.message || '账号或密码错误'
      return
    }

    if (data.code === 200) {
      authStore.setUser(data.data.user)

      const redirect = route.query.redirect as string | undefined
      if (data.data.user.need_change_password) {
        router.push(redirect ? `/change-password?redirect=${encodeURIComponent(redirect)}` : '/change-password')
      } else if (data.data.user.role === 'admin' || data.data.user.role === 'super_admin') {
        router.push(redirect || '/admin')
      } else {
        router.push(redirect || '/')
      }
    } else {
      errorMsg.value = data.message || '账号或密码错误'
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 背景图 -->
    <div class="login-bg" />

    <!-- 毛玻璃登录卡片 -->
    <div class="login-card">
      <div class="login-header">
        <Landmark class="w-10 h-10 text-primary" />
        <h1 class="login-title">校园活动信息港</h1>
        <p class="login-subtitle">登录你的账号</p>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMsg" class="error-alert">
        <AlertCircle class="w-4 h-4" />
        <span>{{ errorMsg }}</span>
      </div>

      <!-- 表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="input-group">
          <User class="input-icon" />
          <input
            v-model="account"
            type="text"
            placeholder="学号/姓名"
            class="login-input"
            :disabled="loading"
          />
        </div>

        <div class="input-group">
          <Lock class="input-icon" />
          <input
            v-model="password"
            type="password"
            placeholder="密码"
            class="login-input"
            :disabled="loading"
          />
        </div>

        <button
          type="submit"
          class="login-btn"
          :disabled="loading"
        >
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>

      <div class="login-footer">
        <span class="text-text-secondary">还没有账号？</span>
        <RouterLink to="/register" class="link-primary">去注册 →</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  position: relative;
}

.login-bg {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #EFF6FF 0%, #F8FAFC 50%, #F1F5F9 100%);
  z-index: -1;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  padding: 40px 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-title {
  font-size: 22px;
  font-weight: 700;
  color: #1E293B;
  margin-top: 12px;
  margin-bottom: 4px;
}
.login-subtitle {
  font-size: 14px;
  color: #64748B;
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #FEF2F2;
  border-radius: 8px;
  color: var(--color-danger);
  font-size: 13px;
  margin-bottom: 16px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  position: relative;
}
.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #94A3B8;
}
.login-input {
  width: 100%;
  height: 48px;
  padding: 0 16px 0 44px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 15px;
  color: #1E293B;
  background: white;
  transition: all 150ms ease;
}
.login-input::placeholder {
  color: #94A3B8;
}
.login-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.login-btn {
  width: 100%;
  height: 48px;
  background: #3B82F6;
  color: white;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 150ms ease;
  margin-top: 8px;
}
.login-btn:hover {
  background: #2563EB;
}
.login-btn:active {
  transform: scale(0.98);
}
.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
}
.link-primary {
  color: #3B82F6;
  font-weight: 500;
  margin-left: 4px;
}
.link-primary:hover {
  color: #2563EB;
}
</style>
