<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { Lock, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirm = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

async function handleChangePassword() {
  errorMsg.value = ''
  successMsg.value = ''

  if (!newPassword.value || newPassword.value.length < 8) {
    errorMsg.value = '密码长度至少8位'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    const data = await request('/auth/force-change-password', {
      method: 'PUT',
      body: JSON.stringify({ new_password: newPassword.value, confirm_password: confirmPassword.value }),
    })

    if (data.code === 200) {
      successMsg.value = '密码设置成功，即将跳转登录页...'
      setTimeout(async () => {
        await authStore.logout()
        router.push('/login')
      }, 1500)
    } else {
      errorMsg.value = data.message || '修改密码失败'
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="change-password-page">
    <div class="change-password-card">
      <div class="card-header">
        <Lock class="w-10 h-10 text-primary" />
        <h1 class="card-title">设置新密码</h1>
        <p class="card-subtitle">首次登录需要修改初始密码</p>
      </div>

      <div v-if="errorMsg" class="error-alert">
        <AlertCircle class="w-4 h-4" />
        <span>{{ errorMsg }}</span>
      </div>

      <div v-if="successMsg" class="success-alert">
        <CheckCircle class="w-4 h-4" />
        <span>{{ successMsg }}</span>
      </div>

      <form class="password-form" @submit.prevent="handleChangePassword">
        <div class="input-group">
          <label class="input-label">新密码</label>
          <div class="input-wrapper">
            <input
              v-model="newPassword"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入新密码"
              class="form-input"
              :disabled="loading || !!successMsg"
            />
            <button type="button" class="toggle-btn" @click="showPassword = !showPassword">
              <Eye v-if="!showPassword" class="w-4 h-4" />
              <EyeOff v-else class="w-4 h-4" />
            </button>
          </div>
          <div class="password-hints">
            <span class="hint" :class="{ active: newPassword.value?.length >= 8 }">至少8位</span>
            <span class="hint" :class="{ active: /[A-Za-z]/.test(newPassword.value) }">包含字母</span>
            <span class="hint" :class="{ active: /[0-9]/.test(newPassword.value) }">包含数字</span>
          </div>
        </div>

        <div class="input-group">
          <label class="input-label">确认密码</label>
          <div class="input-wrapper">
            <input
              v-model="confirmPassword"
              :type="showConfirm ? 'text' : 'password'"
              placeholder="请再次输入新密码"
              class="form-input"
              :disabled="loading || !!successMsg"
            />
            <button type="button" class="toggle-btn" @click="showConfirm = !showConfirm">
              <Eye v-if="!showConfirm" class="w-4 h-4" />
              <EyeOff v-else class="w-4 h-4" />
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="submit-btn"
          :disabled="loading || !!successMsg"
        >
          {{ loading ? '提交中...' : '确认修改' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.change-password-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: linear-gradient(180deg, #EFF6FF 0%, #F8FAFC 50%, #F1F5F9 100%);
}

.change-password-card {
  width: 100%;
  max-width: 400px;
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  padding: 40px 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.card-title {
  font-size: 22px;
  font-weight: 700;
  color: #1E293B;
  margin-top: 12px;
  margin-bottom: 4px;
}

.card-subtitle {
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
  color: var(--color-danger, #EF4444);
  font-size: 13px;
  margin-bottom: 16px;
}

.success-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #F0FDF4;
  border-radius: 8px;
  color: #16A34A;
  font-size: 13px;
  margin-bottom: 16px;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input {
  width: 100%;
  height: 48px;
  padding: 0 44px 0 16px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 15px;
  color: #1E293B;
  background: white;
  transition: all 150ms ease;
}

.form-input::placeholder {
  color: #94A3B8;
}

.form-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}

.toggle-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: #94A3B8;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
}

.toggle-btn:hover {
  color: #64748B;
}

.submit-btn {
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

.submit-btn:hover {
  background: #2563EB;
}

.submit-btn:active {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.password-hints {
  display: flex;
  gap: 12px;
  margin-top: 6px;
}

.hint {
  font-size: 12px;
  color: #94A3B8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.hint::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #E2E8F0;
}

.hint.active {
  color: #059669;
}

.hint.active::before {
  background: #059669;
}
</style>
