<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  User,
  PenLine,
  UserCheck,
  GraduationCap,
  Lock,
  Eye,
  EyeOff,
  ChevronRight,
  Camera,
  AlertTriangle,
  Upload,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import { useColleges } from '@/composables/useColleges'
import { fetchPublicConfig } from '@/composables/useSystemConfig'
import type {
  OwnerProfile,
  OwnerProfileUpdate,
  ContactUpdate,
  AdvisorUpdate,
} from '@/types/activity'

const authStore = useAuthStore()

type TabKey = 'profile' | 'contact' | 'advisor' | 'password'

const activeTab = ref<TabKey>('profile')
const tabs: { key: TabKey; label: string; icon: typeof PenLine }[] = [
  { key: 'profile', label: '编辑资料', icon: PenLine },
  { key: 'contact', label: '负责人信息', icon: UserCheck },
  { key: 'advisor', label: '指导老师', icon: GraduationCap },
  { key: 'password', label: '修改密码', icon: Lock },
]

// ── 用户信息 ──
const ownerProfile = ref<OwnerProfile | null>(null)
const loading = ref(true)

const ownerTypes = ref<string[]>([])
const { colleges, fetchColleges } = useColleges()

async function fetchProfile() {
  if (!authStore.isLoggedIn) return
  loading.value = true
  try {
    const data = await request('/users/me')
    if (data.code === 200) {
      ownerProfile.value = data.data
      initForms()
    }
  } catch {
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// ── 编辑资料 ──
const profileForm = ref<OwnerProfileUpdate>({
  owner_name: '',
  owner_type: '',
  college_id: 0,
  bio: '',
})
const profileMsg = ref({ type: '' as 'success' | 'error', text: '' })
const profileSaving = ref(false)
const avatarUploading = ref(false)

function initForms() {
  if (!ownerProfile.value) return
  profileForm.value = {
    owner_name: ownerProfile.value.owner_name,
    owner_type: ownerProfile.value.owner_type,
    college_id: ownerProfile.value.college_id,
    bio: ownerProfile.value.bio || '',
  }
  contactForm.value = {
    contact_name: ownerProfile.value.contact_name || '',
    contact_student_id: ownerProfile.value.contact_student_id || '',
    contact_phone: ownerProfile.value.contact_phone || '',
  }
  advisorForm.value = {
    advisor_name: ownerProfile.value.advisor_name || '',
    advisor_contact: ownerProfile.value.advisor_contact || '',
  }
}

async function saveProfile() {
  if (!authStore.isLoggedIn) return
  profileSaving.value = true
  profileMsg.value = { type: '', text: '' }
  try {
    const data = await request('/users/me', {
      method: 'PUT',
      body: JSON.stringify(profileForm.value),
    })
    if (data.code === 200) {
      profileMsg.value = { type: 'success', text: '保存成功' }
      await fetchProfile()
    } else {
      profileMsg.value = { type: 'error', text: data.message || '保存失败' }
    }
  } catch {
    profileMsg.value = { type: 'error', text: '网络错误' }
  } finally {
    profileSaving.value = false
  }
}

async function handleAvatarUpload(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length || !authStore.isLoggedIn) return
  const file = input.files[0]
  if (file.size > 10 * 1024 * 1024) {
    profileMsg.value = { type: 'error', text: '文件大小不能超过10MB' }
    return
  }
  avatarUploading.value = true
  profileMsg.value = { type: '', text: '' }
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('type', 'avatar')
    const data = await request('/upload', {
      method: 'POST',
      body: form,
    })
    if (data.code === 200 && data.data?.url) {
      // 保存头像 URL 到用户资料
      await request('/users/me', {
        method: 'PUT',
        body: JSON.stringify({ avatar_url: data.data.url }),
      })
      await fetchProfile()
      await authStore.fetchUserInfo()
      profileMsg.value = { type: 'success', text: '头像更新成功' }
    } else {
      profileMsg.value = { type: 'error', text: data.message || '上传失败' }
    }
  } catch {
    profileMsg.value = { type: 'error', text: '上传失败' }
  } finally {
    avatarUploading.value = false
    input.value = ''
  }
}

// ── 负责人信息 ──
const contactForm = ref<ContactUpdate>({
  contact_name: '',
  contact_student_id: '',
  contact_phone: '',
})
const contactMsg = ref({ type: '' as 'success' | 'error', text: '' })
const contactSaving = ref(false)

async function saveContact() {
  if (!authStore.isLoggedIn) return
  contactSaving.value = true
  contactMsg.value = { type: '', text: '' }
  try {
    const data = await request('/users/me/contact', {
      method: 'PUT',
      body: JSON.stringify(contactForm.value),
    })
    if (data.code === 200) {
      contactMsg.value = { type: 'success', text: '负责人信息已提交审核，审核期间当前信息保持不变' }
      await fetchProfile()
    } else {
      contactMsg.value = { type: 'error', text: data.message || '提交失败' }
    }
  } catch {
    contactMsg.value = { type: 'error', text: '网络错误' }
  } finally {
    contactSaving.value = false
  }
}

// ── 指导老师 ──
const advisorForm = ref<AdvisorUpdate>({
  advisor_name: '',
  advisor_contact: '',
})
const advisorMsg = ref({ type: '' as 'success' | 'error', text: '' })
const advisorSaving = ref(false)

async function saveAdvisor() {
  if (!authStore.isLoggedIn) return
  advisorSaving.value = true
  advisorMsg.value = { type: '', text: '' }
  try {
    const data = await request('/users/me/advisor', {
      method: 'PUT',
      body: JSON.stringify(advisorForm.value),
    })
    if (data.code === 200) {
      advisorMsg.value = { type: 'success', text: '保存成功' }
      await fetchProfile()
    } else {
      advisorMsg.value = { type: 'error', text: data.message || '保存失败' }
    }
  } catch {
    advisorMsg.value = { type: 'error', text: '网络错误' }
  } finally {
    advisorSaving.value = false
  }
}

// ── 修改密码（复用P9逻辑）──
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const passwordMsg = ref({ type: '' as 'success' | 'error', text: '' })
const passwordSaving = ref(false)
const showOldPwd = ref(false)
const showNewPwd = ref(false)
const showConfirmPwd = ref(false)

async function changePassword() {
  if (!authStore.isLoggedIn) return
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    passwordMsg.value = { type: 'error', text: '两次密码输入不一致' }
    return
  }
  if (passwordForm.value.new_password.length < 8) {
    passwordMsg.value = { type: 'error', text: '新密码至少8位' }
    return
  }
  passwordSaving.value = true
  passwordMsg.value = { type: '', text: '' }
  try {
    const data = await request('/auth/password', {
      method: 'PUT',
      body: JSON.stringify(passwordForm.value),
    })
    if (data.code === 200) {
      passwordMsg.value = { type: 'success', text: '密码修改成功' }
      passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    } else {
      passwordMsg.value = { type: 'error', text: data.message || '修改失败' }
    }
  } catch {
    passwordMsg.value = { type: 'error', text: '网络错误' }
  } finally {
    passwordSaving.value = false
  }
}

onMounted(async () => {
  fetchColleges()
  fetchProfile()
  const config = await fetchPublicConfig()
  ownerTypes.value = config.owner_types
})
</script>

<template>
  <div class="profile-page">
    <!-- 用户信息卡片 -->
    <div class="user-card">
      <div class="user-avatar-wrap">
        <img
          v-if="ownerProfile?.avatar_url"
          :src="ownerProfile.avatar_url"
          alt=""
          class="user-avatar-img"
        />
        <div v-else class="user-avatar-placeholder">
          <User class="w-6 h-6" />
        </div>
      </div>
      <div class="user-info">
        <h2 class="user-name">{{ ownerProfile?.owner_name || '加载中...' }}</h2>
        <span class="user-meta">{{ ownerProfile?.account }}</span>
        <span class="user-meta">{{ ownerProfile?.college_name }}</span>
      </div>
    </div>

    <!-- 标签导航 -->
    <div class="tab-nav">
      <div class="tab-scroll">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" class="w-4 h-4" />
          <span>{{ tab.label }}</span>
        </button>
      </div>
    </div>

    <!-- 标签页内容 -->
    <div class="tab-content">
      <!-- 编辑资料 -->
      <div v-if="activeTab === 'profile'" class="tab-panel">
        <div class="form-card">
          <!-- 头像 -->
          <div class="avatar-section">
            <div class="avatar-preview">
              <img
                v-if="ownerProfile?.avatar_url"
                :src="ownerProfile.avatar_url"
                alt=""
                class="avatar-img"
              />
              <div v-else class="avatar-placeholder-lg">
                <User class="w-10 h-10" />
              </div>
            </div>
            <label class="avatar-upload-btn">
              <input
                type="file"
                accept="image/jpeg,image/png,image/gif,image/webp,image/bmp"
                class="hidden-input"
                @change="handleAvatarUpload"
              />
              <Camera class="w-4 h-4" />
              <span>{{ avatarUploading ? '上传中...' : '更换头像' }}</span>
            </label>
          </div>

          <div class="form-grid">
            <div class="form-row">
              <label class="form-label">主体名称</label>
              <input v-model="profileForm.owner_name" type="text" class="form-input" />
            </div>
            <div class="form-row">
              <label class="form-label">主体类型</label>
              <select v-model="profileForm.owner_type" class="form-input">
                <option value="">请选择</option>
                <option v-for="t in ownerTypes" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-row">
              <label class="form-label">所属学院</label>
              <select v-model="profileForm.college_id" class="form-input">
                <option v-for="c in colleges" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
          </div>

          <div class="form-row" style="margin-top: 16px">
            <label class="form-label">个性介绍</label>
            <textarea v-model="profileForm.bio" class="form-input form-textarea" rows="4" placeholder="简单介绍一下你们的组织..." />
          </div>

          <div v-if="profileMsg.text" class="form-msg" :class="profileMsg.type">
            {{ profileMsg.text }}
          </div>

          <button
            class="btn-primary"
            :disabled="profileSaving"
            @click="saveProfile"
          >
            {{ profileSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>

      <!-- 负责人信息 -->
      <div v-if="activeTab === 'contact'" class="tab-panel">
        <div class="form-card">
          <div class="contact-warning">
            <AlertTriangle class="w-4 h-4 text-accent shrink-0" />
            <span class="text-sm text-accent">修改负责人信息将提交管理员审核，审核期间当前信息保持不变</span>
          </div>

          <div class="form-grid">
            <div class="form-row">
              <label class="form-label">负责人姓名</label>
              <input v-model="contactForm.contact_name" type="text" class="form-input" />
            </div>
            <div class="form-row">
              <label class="form-label">负责人学号</label>
              <input v-model="contactForm.contact_student_id" type="text" class="form-input" maxlength="11" />
            </div>
          </div>

          <div class="form-row" style="margin-top: 16px">
            <label class="form-label">负责人手机号</label>
            <input v-model="contactForm.contact_phone" type="tel" class="form-input" />
          </div>

          <div v-if="contactMsg.text" class="form-msg" :class="contactMsg.type">
            {{ contactMsg.text }}
          </div>

          <button
            class="btn-primary"
            :disabled="contactSaving"
            @click="saveContact"
          >
            {{ contactSaving ? '提交中...' : '提交审核' }}
          </button>
        </div>
      </div>

      <!-- 指导老师 -->
      <div v-if="activeTab === 'advisor'" class="tab-panel">
        <div class="form-card">
          <div class="form-grid">
            <div class="form-row">
              <label class="form-label">指导老师姓名</label>
              <input v-model="advisorForm.advisor_name" type="text" class="form-input" />
            </div>
            <div class="form-row">
              <label class="form-label">指导老师联系方式</label>
              <input v-model="advisorForm.advisor_contact" type="tel" class="form-input" />
            </div>
          </div>

          <div v-if="advisorMsg.text" class="form-msg" :class="advisorMsg.type">
            {{ advisorMsg.text }}
          </div>

          <button
            class="btn-primary"
            :disabled="advisorSaving"
            @click="saveAdvisor"
          >
            {{ advisorSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>

      <!-- 修改密码 -->
      <div v-if="activeTab === 'password'" class="tab-panel">
        <div class="form-card">
          <div class="form-grid is-single-col">
            <div class="form-row">
              <label class="form-label">当前密码</label>
              <div class="input-with-toggle">
                <input
                  v-model="passwordForm.old_password"
                  :type="showOldPwd ? 'text' : 'password'"
                  class="form-input"
                />
                <button class="toggle-vis" @click="showOldPwd = !showOldPwd">
                  <Eye v-if="!showOldPwd" class="w-4 h-4" />
                  <EyeOff v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
            <div class="form-row">
              <label class="form-label">新密码</label>
              <div class="input-with-toggle">
                <input
                  v-model="passwordForm.new_password"
                  :type="showNewPwd ? 'text' : 'password'"
                  class="form-input"
                  placeholder="8-20位密码"
                />
                <button class="toggle-vis" @click="showNewPwd = !showNewPwd">
                  <Eye v-if="!showNewPwd" class="w-4 h-4" />
                  <EyeOff v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
            <div class="form-row">
              <label class="form-label">确认新密码</label>
              <div class="input-with-toggle">
                <input
                  v-model="passwordForm.confirm_password"
                  :type="showConfirmPwd ? 'text' : 'password'"
                  class="form-input"
                  placeholder="再次输入新密码"
                />
                <button class="toggle-vis" @click="showConfirmPwd = !showConfirmPwd">
                  <Eye v-if="!showConfirmPwd" class="w-4 h-4" />
                  <EyeOff v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="passwordMsg.text" class="form-msg" :class="passwordMsg.type">
            {{ passwordMsg.text }}
          </div>

          <button
            class="btn-primary"
            :disabled="passwordSaving"
            @click="changePassword"
          >
            {{ passwordSaving ? '修改中...' : '确认修改密码' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── 与 P9 共用的页面框架样式 ── */
.profile-page {
  max-width: 56rem;
  margin: 0 auto;
  padding: 24px 16px 32px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  margin-bottom: 16px;
}
.user-avatar-wrap { flex-shrink: 0; }
.user-avatar-img {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}
.user-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3B82F6;
}
.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.user-name {
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
  line-height: 1.3;
}
.user-meta {
  font-size: 13px;
  color: #64748B;
}
@media (min-width: 768px) {
  .user-avatar-img, .user-avatar-placeholder { width: 56px; height: 56px; }
  .user-name { font-size: 20px; }
}

/* ── 标签导航 ── */
.tab-nav {
  margin-bottom: 16px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.tab-nav::-webkit-scrollbar { display: none; }
.tab-scroll {
  display: flex;
  gap: 4px;
  padding-bottom: 4px;
  min-width: max-content;
  border-bottom: 1px solid #E2E8F0;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
  white-space: nowrap;
  border-radius: 8px 8px 0 0;
  transition: all 150ms ease;
  position: relative;
}
.tab-btn::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: transparent;
  border-radius: 2px 2px 0 0;
  transition: background 150ms ease;
}
.tab-btn:hover { color: #1E293B; background: rgba(59, 130, 246, 0.05); }
.tab-btn.active { color: #3B82F6; }
.tab-btn.active::after { background: #3B82F6; }
@media (min-width: 768px) {
  .tab-btn { padding: 10px 18px; font-size: 14px; }
}

/* ── 标签内容 ── */
.tab-content { min-height: 300px; }
.tab-panel { animation: fadeIn 200ms ease; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── 表单卡片 ── */
.form-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* ── 头像区 ── */
.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #F1F5F9;
}
.avatar-preview {
  flex-shrink: 0;
}
.avatar-img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #F1F5F9;
}
.avatar-placeholder-lg {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3B82F6;
}
.avatar-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  cursor: pointer;
  transition: all 150ms ease;
}
.avatar-upload-btn:hover { background: rgba(59, 130, 246, 0.2); }
.hidden-input { display: none; }

/* ── 表单网格 ── */
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-grid.is-single-col {
  max-width: 480px;
}
@media (min-width: 768px) {
  .form-grid:not(.is-single-col) {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #1E293B;
}
.form-input {
  width: 100%;
  height: 42px;
  padding: 0 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 14px;
  color: #1E293B;
  background: white;
  transition: all 150ms ease;
}
.form-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  outline: none;
}
.form-textarea {
  height: auto;
  padding: 10px 12px;
  resize: vertical;
  line-height: 1.5;
}

/* ── 密码眼睛切换 ── */
.input-with-toggle { position: relative; }
.input-with-toggle .form-input { padding-right: 40px; }
.toggle-vis {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: #94A3B8;
  padding: 4px;
}
.toggle-vis:hover { color: #64748B; }

/* ── 消息提示 ── */
.form-msg {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  margin-top: 8px;
}
.form-msg.success { background: #ECFDF5; color: var(--color-success); }
.form-msg.error { background: #FEF2F2; color: var(--color-danger); }

/* ── 负责人审核提示 ── */
.contact-warning {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  background: rgba(245, 158, 11, 0.08);
  border-radius: 10px;
  margin-bottom: 20px;
}

/* ── 按钮 ── */
.btn-primary {
  width: 100%;
  height: 44px;
  background: #3B82F6;
  color: white;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 150ms ease;
  margin-top: 20px;
}
.btn-primary:hover { background: #2563EB; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
@media (min-width: 768px) {
  .btn-primary { max-width: 320px; }
}
</style>
