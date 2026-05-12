<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { request } from '@/utils/request'
import { useColleges } from '@/composables/useColleges'
import { fetchPublicConfig } from '@/composables/useSystemConfig'
import { Landmark, User, Lock, Building2, Phone, Mail, AlertCircle, CheckCircle2 } from 'lucide-vue-next'

type RegisterType = 'student' | 'owner'

const router = useRouter()
const activeTab = ref<RegisterType>('student')

// 学生表单
const studentForm = ref({
  student_id: '',
  name: '',
  password: '',
  confirm_password: '',
  college_id: null as number | null,
  phone: '',
  email: '',
})

// 活动主体表单
const ownerForm = ref({
  account: '',
  password: '',
  confirm_password: '',
  owner_name: '',
  owner_type: '',
  college_id: null as number | null,
  contact_name: '',
  contact_student_id: '',
  contact_phone: '',
  advisor_name: '',
  advisor_contact: '',
  bio: '',
})

const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const { colleges, fetchColleges } = useColleges()

const ownerTypes = ref<string[]>([])

const isStudentFormValid = computed(() => {
  const f = studentForm.value
  return f.student_id && f.name && f.password && f.confirm_password && f.college_id !== null
    && f.password === f.confirm_password && /^\d{11}$/.test(f.student_id)
    && f.password.length >= 8 && f.password.length <= 20
})

const isOwnerFormValid = computed(() => {
  const f = ownerForm.value
  return f.account && f.password && f.confirm_password && f.owner_name && f.owner_type
    && f.college_id !== null && f.contact_name && f.contact_student_id && f.contact_phone
    && f.password === f.confirm_password && f.password.length >= 8 && f.password.length <= 20
})

async function handleStudentRegister() {
  if (!isStudentFormValid.value) {
    errorMsg.value = '请填写完整信息并确保密码一致'
    return
  }
  loading.value = true
  errorMsg.value = ''

  try {
    const data = await request('/auth/register/student', {
      method: 'POST',
      body: JSON.stringify({
        ...studentForm.value,
        phone: studentForm.value.phone || null,
        email: studentForm.value.email || null,
      }),
    })

    if (data.code === 200) {
      successMsg.value = '注册成功！'
      setTimeout(() => router.push('/login'), 1500)
    } else {
      errorMsg.value = data.message || '注册失败'
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function handleOwnerRegister() {
  if (!isOwnerFormValid.value) {
    errorMsg.value = '请填写完整信息并确保密码一致'
    return
  }
  loading.value = true
  errorMsg.value = ''

  try {
    const data = await request('/auth/register/owner', {
      method: 'POST',
      body: JSON.stringify({
        ...ownerForm.value,
        advisor_name: ownerForm.value.advisor_name || null,
        advisor_contact: ownerForm.value.advisor_contact || null,
        bio: ownerForm.value.bio || null,
      }),
    })

    if (data.code === 200) {
      successMsg.value = '已提交审核，审核通过后即可登录'
      // 主办方注册不自动跳转，保持当前页面提示用户等待审核
    } else {
      errorMsg.value = data.message || '提交失败'
    }
  } catch {
    errorMsg.value = '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(fetchColleges)
onMounted(async () => {
  const config = await fetchPublicConfig()
  ownerTypes.value = config.owner_types
})
</script>

<template>
  <div class="register-page">
    <div class="register-bg" />

    <div class="register-card">
      <div class="register-header">
        <Landmark class="w-10 h-10 text-primary" />
        <h1 class="register-title">校园活动信息港</h1>
        <p class="register-subtitle">创建你的账号</p>
      </div>

      <!-- 标签切换 -->
      <div class="tab-bar">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'student' }"
          @click="activeTab = 'student'"
        >
          <User class="w-4 h-4" />
          学生注册
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'owner' }"
          @click="activeTab = 'owner'"
        >
          <Building2 class="w-4 h-4" />
          活动主体注册
        </button>
      </div>

      <!-- 提示消息 -->
      <div v-if="errorMsg" class="msg-alert error">
        <AlertCircle class="w-4 h-4" />
        <span>{{ errorMsg }}</span>
      </div>
      <div v-if="successMsg" class="msg-alert success">
        <CheckCircle2 class="w-4 h-4" />
        <span>{{ successMsg }}</span>
      </div>

      <!-- 学生注册表单 -->
      <form v-if="activeTab === 'student'" class="register-form" @submit.prevent="handleStudentRegister">
        <div class="form-row">
          <label class="form-label">学号 <span class="required">*</span></label>
          <input v-model="studentForm.student_id" type="text" placeholder="11位学号" class="form-input" maxlength="11" pattern="\d{11}" />
        </div>
        <div class="form-row">
          <label class="form-label">姓名 <span class="required">*</span></label>
          <input v-model="studentForm.name" type="text" placeholder="真实姓名" class="form-input" />
        </div>
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">密码 <span class="required">*</span></label>
            <input v-model="studentForm.password" type="password" placeholder="8-20位密码" class="form-input" />
          </div>
          <div class="form-row">
            <label class="form-label">确认密码 <span class="required">*</span></label>
            <input v-model="studentForm.confirm_password" type="password" placeholder="再次输入密码" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">学院 <span class="required">*</span></label>
          <select v-model="studentForm.college_id" class="form-input">
            <option :value="null">请选择学院</option>
            <option v-for="c in colleges.filter(x => x.id !== 0)" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">手机号 <span class="optional">（选填）</span></label>
            <input v-model="studentForm.phone" type="tel" placeholder="选填" class="form-input" />
          </div>
          <div class="form-row">
            <label class="form-label">邮箱 <span class="optional">（选填）</span></label>
            <input v-model="studentForm.email" type="email" placeholder="选填" class="form-input" />
          </div>
        </div>

        <button type="submit" class="register-btn" :disabled="loading">
          {{ loading ? '注册中...' : '注 册' }}
        </button>
      </form>

      <!-- 活动主体注册表单 -->
      <form v-else class="register-form" @submit.prevent="handleOwnerRegister">
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">账号 <span class="required">*</span></label>
            <input v-model="ownerForm.account" type="text" placeholder="社团缩写等" class="form-input" />
          </div>
          <div class="form-row">
            <label class="form-label">密码 <span class="required">*</span></label>
            <input v-model="ownerForm.password" type="password" placeholder="8-20位密码" class="form-input" />
          </div>
        </div>
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">确认密码 <span class="required">*</span></label>
            <input v-model="ownerForm.confirm_password" type="password" placeholder="再次输入密码" class="form-input" />
          </div>
          <div class="form-row">
            <label class="form-label">主体名称 <span class="required">*</span></label>
            <input v-model="ownerForm.owner_name" type="text" placeholder="如：XX大学街舞社" class="form-input" />
          </div>
        </div>
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">主体类型 <span class="required">*</span></label>
            <select v-model="ownerForm.owner_type" class="form-input">
              <option value="">请选择</option>
              <option v-for="t in ownerTypes" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="form-row">
            <label class="form-label">所属学院 <span class="required">*</span></label>
            <select v-model="ownerForm.college_id" class="form-input">
              <option :value="null">请选择</option>
              <option v-for="c in colleges" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
        </div>
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">负责人姓名 <span class="required">*</span></label>
            <input v-model="ownerForm.contact_name" type="text" placeholder="负责人真实姓名" class="form-input" />
          </div>
          <div class="form-row">
            <label class="form-label">负责人学号 <span class="required">*</span></label>
            <input v-model="ownerForm.contact_student_id" type="text" placeholder="11位学号" class="form-input" maxlength="11" />
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">负责人手机号 <span class="required">*</span></label>
          <input v-model="ownerForm.contact_phone" type="tel" placeholder="手机号" class="form-input" />
        </div>
        <div class="form-row-group">
          <div class="form-row">
            <label class="form-label">指导老师姓名 <span class="optional">（选填）</span></label>
            <input v-model="ownerForm.advisor_name" type="text" placeholder="选填" class="form-input" />
          </div>
          <div class="form-row">
            <label class="form-label">老师联系方式 <span class="optional">（选填）</span></label>
            <input v-model="ownerForm.advisor_contact" type="tel" placeholder="选填" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">个性介绍 <span class="optional">（选填）</span></label>
          <textarea v-model="ownerForm.bio" placeholder="简单介绍一下你们的组织..." class="form-input" rows="3" />
        </div>

        <button type="submit" class="register-btn" :disabled="loading">
          {{ loading ? '提交中...' : '提交审核' }}
        </button>
      </form>

      <div class="register-footer">
        <span class="text-text-secondary">已有账号？</span>
        <RouterLink to="/login" class="link-primary">去登录 →</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100dvh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 40px 16px;
  position: relative;
}

.register-bg {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #EFF6FF 0%, #F8FAFC 50%, #F1F5F9 100%);
  z-index: -1;
}

.register-card {
  width: 100%;
  max-width: 520px;
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
}

.register-header {
  text-align: center;
  margin-bottom: 24px;
}
.register-title {
  font-size: 22px;
  font-weight: 700;
  color: #1E293B;
  margin-top: 12px;
  margin-bottom: 4px;
}
.register-subtitle {
  font-size: 14px;
  color: #64748B;
}

.tab-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: #F1F5F9;
  padding: 4px;
  border-radius: 10px;
}
.tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
  transition: all 150ms ease;
}
.tab-btn.active {
  background: white;
  color: #3B82F6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.msg-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 16px;
}
.msg-alert.error {
  background: #FEF2F2;
  color: var(--color-danger);
}
.msg-alert.success {
  background: #ECFDF5;
  color: var(--color-success);
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-row-group {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
@media (min-width: 768px) {
  .form-row-group {
    grid-template-columns: 1fr 1fr;
  }
}
.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #1E293B;
}
.required {
  color: var(--color-danger);
}
.optional {
  color: #94A3B8;
  font-weight: 400;
}
.form-input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
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
textarea.form-input {
  height: auto;
  padding: 10px 14px;
  resize: vertical;
}

.register-btn {
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
.register-btn:hover {
  background: #2563EB;
}
.register-btn:active {
  transform: scale(0.98);
}
.register-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.register-footer {
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
