<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Sparkles,
  MessageCircle,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  Plus,
  X,
  QrCode,
  MapPin,
  Loader2,
  ImagePlus,
  Lock,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { request } from '@/utils/request'
import type { ActivityDetail } from '@/types/activity'
import { ElMessage } from 'element-plus'
import { fetchPublicConfig } from '@/composables/useSystemConfig'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// ── 路由参数 ──
const activityId = computed(() => {
  const id = route.query.edit
  return id ? Number(id) : null
})

// ── 加载状态 ──
const loadingActivity = ref(false)
const activityStatus = ref('') // 加载后的活动状态

// ── 下拉选项 ──
const configData = ref<{ credit_types: string[]; activity_types: string[] }>({
  credit_types: [],
  activity_types: [],
})

// ── AI 解析区 ──
const aiExpanded = ref(false)
const aiArticleText = ref('')
const aiGroupMessage = ref('')
const aiParsing = ref(false)

// ── 置信度标记 ──
type ConfidenceLevel = 'high' | 'medium' | 'low' | ''
const fieldConfidence = reactive<Record<string, ConfidenceLevel>>({
  title: '',
  activity_type: '',
  start_time: '',
  end_time: '',
  location: '',
  credit_type: '',
  registration_deadline: '',
  max_participants: '',
  description: '',
})

function clearConfidence(field: string) {
  fieldConfidence[field] = ''
}

// ── 表单数据 ──
const form = reactive({
  title: '',
  activity_type: '',
  start_date: '',
  start_time: '',
  end_date: '',
  end_time: '',
  location: '',
  credit_type: '',
  credit_value: '',
  registration_deadline_date: '',
  registration_deadline_time: '',
  max_participants: '',
  description: '',
})

// ── 已删除类型标记 ──
const isActivityTypeDeleted = computed(() => {
  return form.activity_type && !configData.value.activity_types.includes(form.activity_type)
})

const isCreditTypeDeleted = computed(() => {
  return form.credit_type && !configData.value.credit_types.includes(form.credit_type)
})

// ── 图片 ──
// 编辑模式下有两种图片：已有的（来自服务器）和新增的
interface ExistingImage {
  id: number
  url: string
  is_cover: boolean
  type: 'existing'
}

interface UploadedImage {
  localUrl: string
  serverUrl: string
  filename: string
  type: 'new'
}

type ActivityImageItem = ExistingImage | UploadedImage

const activityImages = ref<ActivityImageItem[]>([])
const qrcodeImage = ref<UploadedImage | null>(null)
const existingQrcodeUrl = ref<string | null>(null) // 已有的二维码URL
const imageUploading = ref(false)
const qrcodeUploading = ref(false)

// 被删除的已有图片 ID 列表
const deletedImageIds = ref<number[]>([])

// ── 表单错误 ──
const errors = reactive<Record<string, string>>({})

// ── 提交状态 ──
const submitting = ref<'draft' | 'publish' | ''>('')

// ── 消息 ──
const globalMsg = ref({ type: '' as 'success' | 'error', text: '' })
let globalMsgTimer: ReturnType<typeof setTimeout> | null = null

function showMsg(type: 'success' | 'error', text: string, duration = 4000) {
  if (globalMsgTimer) clearTimeout(globalMsgTimer)
  globalMsg.value = { type, text }
  globalMsgTimer = setTimeout(() => {
    globalMsg.value = { type: '', text: '' }
  }, duration)
}

// ── 字段锁定（报名中的活动） ──
// REGISTERING_LOCKED_FIELDS: credit_type, credit_value, max_participants, registration_deadline
const isRegistering = computed(() => activityStatus.value === 'active')
const isLocked = (field: string): boolean => {
  if (!isRegistering.value) return false
  const lockedFields = ['credit_type', 'credit_value', 'max_participants', 'registration_deadline']
  return lockedFields.includes(field)
}

// ── 文件校验 ──
const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']
const maxSize = 10 * 1024 * 1024

function validateFile(file: File): string | null {
  if (!allowedTypes.includes(file.type)) {
    return '仅支持 jpg/png/bmp/gif/webp 格式'
  }
  if (file.size > maxSize) {
    return '单张图片不能超过10MB'
  }
  return null
}

// ── 图片上传 ──
async function uploadFile(file: File, type: 'activity_image' | 'qrcode'): Promise<UploadedImage | null> {
  if (!authStore.isLoggedIn) return null
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)
  try {
    const data = await request('/upload', {
      method: 'POST',
      body: formData,
    })
    if (data.code === 200 && data.data) {
      return {
        localUrl: URL.createObjectURL(file),
        serverUrl: data.data.url,
        filename: data.data.filename,
      }
    }
    showMsg('error', data.message || '上传失败')
    return null
  } catch {
    showMsg('error', '上传失败，请检查网络')
    return null
  }
}

async function handleImageSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const files = Array.from(input.files)
  imageUploading.value = true
  for (const file of files) {
    const err = validateFile(file)
    if (err) {
      showMsg('error', err)
      continue
    }
    const result = await uploadFile(file, 'activity_image')
    if (result) {
      activityImages.value.push({ ...result, type: 'new' })
    }
  }
  imageUploading.value = false
  input.value = ''
}

function removeImage(index: number) {
  const img = activityImages.value[index]
  if (img.type === 'existing') {
    deletedImageIds.value.push(img.id)
  } else {
    URL.revokeObjectURL(img.localUrl)
  }
  activityImages.value.splice(index, 1)
}

async function handleQrcodeSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  const file = input.files[0]
  const err = validateFile(file)
  if (err) {
    showMsg('error', err)
    input.value = ''
    return
  }
  qrcodeUploading.value = true
  if (qrcodeImage.value) {
    URL.revokeObjectURL(qrcodeImage.value.localUrl)
  }
  const result = await uploadFile(file, 'qrcode')
  if (result) {
    qrcodeImage.value = result
    existingQrcodeUrl.value = null // 新上传覆盖已有二维码
  }
  qrcodeUploading.value = false
  input.value = ''
}

function removeQrcode() {
  if (qrcodeImage.value) {
    URL.revokeObjectURL(qrcodeImage.value.localUrl)
    qrcodeImage.value = null
  }
  // 如果有已有的二维码，也标记删除
  existingQrcodeUrl.value = null
}

// ── 拖拽上传 ──
const dragOver = ref(false)
function onDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}
function onDragLeave() {
  dragOver.value = false
}
async function onDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  if (!e.dataTransfer?.files.length) return
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
  if (!files.length) return
  imageUploading.value = true
  for (const file of files) {
    const err = validateFile(file)
    if (err) {
      showMsg('error', err)
      continue
    }
    const result = await uploadFile(file, 'activity_image')
    if (result) {
      activityImages.value.push({ ...result, type: 'new' })
    }
  }
  imageUploading.value = false
}

// ── AI 解析 ──
async function handleAiParse() {
  if (!aiArticleText.value.trim()) {
    showMsg('error', '请先粘贴公众号文章内容')
    return
  }
  if (!authStore.isLoggedIn) return
  aiParsing.value = true
  globalMsg.value = { type: '', text: '' }
  try {
    const body: Record<string, string> = { article_text: aiArticleText.value.trim() }
    if (aiGroupMessage.value.trim()) {
      body.group_message = aiGroupMessage.value.trim()
    }
    const data = await request('/ai/parse-activity', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    if (data.code === 200 && data.data) {
      applyAiResult(data.data)
      showMsg('success', '解析完成，请核对信息')
      aiExpanded.value = false
    } else {
      showMsg('error', data.message || '解析失败，请手动填写')
    }
  } catch {
    showMsg('error', '解析失败，请手动填写')
  } finally {
    aiParsing.value = false
  }
}

interface AiParsedField<T = string | number> {
  value: T
  confidence: 'high' | 'medium' | 'low'
}

function applyAiResult(result: Record<string, AiParsedField>) {
  // AI 解析不覆盖被锁定的字段
  if (result.title?.value) {
    form.title = String(result.title.value)
    fieldConfidence.title = result.title.confidence
  }
  if (result.activity_type?.value) {
    form.activity_type = String(result.activity_type.value)
    fieldConfidence.activity_type = result.activity_type.confidence
  }
  if (result.start_time?.value && !isLocked('start_time')) {
    const dt = splitDatetime(String(result.start_time.value))
    form.start_date = dt.date
    form.start_time = dt.time
    fieldConfidence.start_time = result.start_time.confidence
  }
  if (result.end_time?.value) {
    const dt = splitDatetime(String(result.end_time.value))
    form.end_date = dt.date
    form.end_time = dt.time
    fieldConfidence.end_time = result.end_time.confidence
  }
  if (result.location?.value) {
    form.location = String(result.location.value)
    fieldConfidence.location = result.location.confidence
  }
  if (result.credit_type?.value && !isLocked('credit_type')) {
    form.credit_type = String(result.credit_type.value)
    fieldConfidence.credit_type = result.credit_type.confidence
  }
  if (result.credit_value?.value !== undefined && result.credit_value?.value !== null && !isLocked('credit_value')) {
    form.credit_value = String(result.credit_value.value)
  }
  if (result.registration_deadline?.value && !isLocked('registration_deadline')) {
    const dt = splitDatetime(String(result.registration_deadline.value))
    form.registration_deadline_date = dt.date
    form.registration_deadline_time = dt.time
    fieldConfidence.registration_deadline = result.registration_deadline.confidence
  }
  if (result.max_participants?.value !== undefined && result.max_participants?.value !== null && !isLocked('max_participants')) {
    form.max_participants = String(result.max_participants.value)
    fieldConfidence.max_participants = result.max_participants.confidence
  }
  if (result.description?.value) {
    form.description = String(result.description.value)
    fieldConfidence.description = result.description.confidence
  }
}

function splitDatetime(iso: string): { date: string; time: string } {
  if (!iso) return { date: '', time: '' }
  // 直接字符串切割，避免 new Date() + toISOString() 的时区转换
  // AI 返回的已是北京时间，直接取日期和时间部分即可
  const date = iso.slice(0, 10)
  const time = iso.slice(11, 16)
  if (!date || !time) return { date: '', time: '' }
  return { date, time }
}

// ── 合并日期时间为 ISO 字符串 ──
function combineDatetime(dateStr: string, timeStr: string): string {
  if (!dateStr) return ''
  const time = timeStr || '00:00'
  return `${dateStr}T${time}:00`
}

// ── 加载活动数据 ──
async function loadActivity() {
  if (!activityId.value) {
    showMsg('error', '缺少活动ID参数')
    return
  }
  loadingActivity.value = true
  try {
    const data = await request<ActivityDetail>(`/activities/${activityId.value}`)
    if (data.code === 200 && data.data) {
      const act = data.data
      activityStatus.value = act.status

      // 预填表单
      form.title = act.title
      form.activity_type = act.activity_type
      form.credit_type = act.credit_type
      form.credit_value = act.credit_value != null ? String(act.credit_value) : ''
      form.location = act.location
      form.description = act.description

      if (act.max_participants) {
        form.max_participants = String(act.max_participants)
      }

      // 时间拆分
      const startDt = splitDatetime(act.start_time)
      form.start_date = startDt.date
      form.start_time = startDt.time

      if (act.end_time) {
        const endDt = splitDatetime(act.end_time)
        form.end_date = endDt.date
        form.end_time = endDt.time
      }

      const deadlineDt = splitDatetime(act.registration_deadline)
      form.registration_deadline_date = deadlineDt.date
      form.registration_deadline_time = deadlineDt.time

      // 图片加载
      activityImages.value = (act.images || []).map(img => ({
        id: img.id,
        url: img.url,
        is_cover: img.is_cover,
        type: 'existing' as const,
      }))

      // 二维码
      if (act.show_qrcode) {
        // 详情页有 show_qrcode 字段表示是否展示了二维码
        // 编辑页需要获取二维码URL，通过活动图片中 is_cover=false 且非普通图片判断
        // 后端返回的 ActivityDetail 没有 qrcode_url 字段，需要额外请求
        // 暂不预填已有二维码（用户可重新上传）
      }
    } else {
      showMsg('error', data.message || '加载活动数据失败')
    }
  } catch {
    showMsg('error', '加载失败，请检查网络')
  } finally {
    loadingActivity.value = false
  }
}

// ── 表单校验 ──
function validateForm(isDraft: boolean): boolean {
  Object.keys(errors).forEach(k => delete errors[k])

  if (!form.title.trim() || form.title.trim().length < 2 || form.title.trim().length > 200) {
    errors.title = '请输入活动标题（2-200字）'
  }

  if (isDraft) {
    return Object.keys(errors).length === 0
  }

  if (!form.activity_type) {
    errors.activity_type = '请选择活动类型'
  }
  if (!form.start_date || !form.start_time) {
    errors.start_time = '请选择开始时间'
  }
  if (form.end_date && form.end_time) {
    const startDt = new Date(combineDatetime(form.start_date, form.start_time))
    const endDt = new Date(combineDatetime(form.end_date, form.end_time))
    if (endDt <= startDt) {
      errors.end_time = '结束时间必须晚于开始时间'
    }
  }
  if (!form.location.trim()) {
    errors.location = '请输入活动地点'
  }
  if (!form.credit_type) {
    errors.credit_type = '请选择学分类型'
  }
  // credit_value 范围校验
  if (form.credit_value !== '' && form.credit_value !== null) {
    const val = Number(form.credit_value)
    if (isNaN(val) || val < 0.1) {
      errors.credit_value = '学分分值最小0.1'
    } else if (val > 2.0) {
      errors.credit_value = '学分分值最大2.0'
    }
  }
  if (!form.registration_deadline_date || !form.registration_deadline_time) {
    errors.registration_deadline = '请选择报名截止时间'
  } else if (form.start_date && form.start_time) {
    const deadlineDt = new Date(combineDatetime(form.registration_deadline_date, form.registration_deadline_time))
    const startDt = new Date(combineDatetime(form.start_date, form.start_time))
    if (deadlineDt > startDt) {
      errors.registration_deadline = '报名截止时间不能晚于活动开始时间'
    }
  }
  if (form.max_participants) {
    const n = Number(form.max_participants)
    if (!Number.isInteger(n) || n < 0) {
      errors.max_participants = '请输入有效的正整数'
    }
  }
  if (!form.description.trim() || form.description.trim().length < 2) {
    errors.description = '请输入活动描述（至少2字）'
  }
  // 编辑模式下不需要强制上传图片（已有图片保留）
  const totalImages = activityImages.value.length
  if (totalImages === 0) {
    errors.images = '请至少保留或上传一张活动图片作为封面'
  }

  return Object.keys(errors).length === 0
}

// ── 提交 ──
async function handleSubmit(isDraft: boolean) {
  if (!validateForm(isDraft)) {
    const firstErr = document.querySelector('.field-error input, .field-error select, .field-error textarea')
    if (firstErr) (firstErr as HTMLElement).focus()
    return
  }
  if (!authStore.isLoggedIn || !activityId.value) return

  submitting.value = isDraft ? 'draft' : 'publish'
  globalMsg.value = { type: '', text: '' }

  // 驳回活动编辑后状态变为 pending
  let status: string
  if (isDraft) {
    status = 'draft'
  } else if (activityStatus.value === 'rejected') {
    status = 'pending' // 驳回活动修改后提交状态变为 pending
  } else if (activityStatus.value === 'draft') {
    status = 'active' // 草稿直接发布变为 active (待审核)
  } else {
    status = activityStatus.value // 报名中的活动保持状态
  }

  // 构建 credit_value
  let creditValue: number | null = null
  if (form.credit_value !== '' && form.credit_value !== null) {
    const val = Number(form.credit_value)
    if (!isNaN(val) && val >= 0.1) {
      creditValue = val
    }
  }

  // 构建图片列表
  const existingIds = activityImages.value
    .filter(img => img.type === 'existing')
    .map(img => (img as ExistingImage).id)
  const newFilenames = activityImages.value
    .filter(img => img.type === 'new')
    .map(img => (img as UploadedImage).filename)

  const body: Record<string, unknown> = {
    title: form.title.trim(),
    activity_type: form.activity_type,
    credit_type: form.credit_type,
    credit_value: creditValue,
    start_time: combineDatetime(form.start_date, form.start_time),
    location: form.location.trim(),
    registration_deadline: combineDatetime(form.registration_deadline_date, form.registration_deadline_time),
    description: form.description.trim(),
    status,
    // 图片：保留的已有图片 ID + 新增图片 filename
    existing_image_ids: existingIds,
    new_image_filenames: newFilenames,
    // 删除的图片
    deleted_image_ids: deletedImageIds.value,
  }

  if (form.end_date && form.end_time) {
    body.end_time = combineDatetime(form.end_date, form.end_time)
  }
  if (form.max_participants) {
    body.max_participants = Number(form.max_participants)
  }
  if (qrcodeImage.value) {
    body.qrcode = qrcodeImage.value.filename
  }
  // 如果删除了已有二维码
  if (!existingQrcodeUrl.value && !qrcodeImage.value) {
    body.remove_qrcode = true
  }

  try {
    const data = await request(`/activities/${activityId.value}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    })
    if (data.code === 200) {
      const msg = isDraft ? '已保存草稿' : (activityStatus.value === 'rejected' ? '已重新提交审核' : '修改成功！')
      showMsg('success', msg)
      setTimeout(() => {
        router.push('/my-activities')
      }, 1200)
    } else {
      showMsg('error', data.message || '修改失败')
    }
  } catch {
    showMsg('error', '网络错误，请重试')
  } finally {
    submitting.value = ''
  }
}

// ── 置信度样式计算 ──
function confidenceClass(field: string): string {
  const c = fieldConfidence[field]
  if (!c) return ''
  return c === 'high' ? 'confidence-high' : 'confidence-low'
}
function confidenceIcon(field: string): 'high' | 'low' | '' {
  const c = fieldConfidence[field]
  if (!c) return ''
  return c === 'high' ? 'high' : 'low'
}

// ── 获取图片显示 URL ──
function getImageUrl(img: ActivityImageItem): string {
  if (img.type === 'existing') {
    return img.url
  }
  return img.localUrl
}

// ── 判断封面 ──
function isCoverImage(index: number): boolean {
  if (index === 0) return true
  return false
}

onMounted(async () => {
  const config = await fetchPublicConfig()
  configData.value = {
    credit_types: config.credit_types,
    activity_types: config.activity_types,
  }
  loadActivity()
})
</script>

<template>
  <div class="publish-page">
    <!-- 加载中 -->
    <div v-if="loadingActivity" class="loading-state">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
      <span>加载活动数据...</span>
    </div>

    <template v-else>
      <!-- 驳回活动提示 -->
      <div v-if="activityStatus === 'rejected'" class="reject-notice">
        <AlertTriangle class="w-5 h-5 shrink-0" />
        <span>此活动已被驳回，修改后将重新提交审核</span>
      </div>

      <!-- 报名中锁定提示 -->
      <div v-if="isRegistering" class="lock-notice">
        <Lock class="w-4 h-4 shrink-0" />
        <span>报名中的活动，学分类型/分值/报名人数/报名截止时间不可修改</span>
      </div>

      <!-- AI 智能解析区 -->
      <div class="ai-section" :class="{ expanded: aiExpanded }">
        <button class="ai-header" @click="aiExpanded = !aiExpanded">
          <div class="ai-header-left">
            <Sparkles class="w-5 h-5 text-primary" />
            <div>
              <span class="ai-title">AI 智能解析</span>
              <span class="ai-optional">（选填）</span>
            </div>
          </div>
          <div class="ai-header-right">
            <span class="ai-subtitle" v-if="!aiExpanded">粘贴文章一键填表</span>
            <component :is="aiExpanded ? ChevronUp : ChevronDown" class="w-4 h-4 text-text-secondary" />
          </div>
        </button>

        <Transition name="slide">
          <div v-if="aiExpanded" class="ai-body">
            <p class="ai-hint">粘贴公众号文章，AI 帮你自动填表</p>
            <div class="form-row">
              <label class="form-label">公众号文章</label>
              <textarea
                v-model="aiArticleText"
                class="form-input form-textarea"
                placeholder="粘贴公众号推文正文..."
                rows="4"
              />
            </div>

            <div class="form-row" style="margin-top: 12px">
              <label class="form-label">
                <MessageCircle class="w-3.5 h-3.5 inline-block mr-1 align-text-bottom" />
                群消息补充<span class="optional">（选填）</span>
              </label>
              <textarea
                v-model="aiGroupMessage"
                class="form-input form-textarea"
                placeholder="粘贴群公告/转发文案..."
                rows="2"
              />
            </div>

            <button
              class="btn-primary ai-parse-btn"
              :disabled="aiParsing || !aiArticleText.trim()"
              @click="handleAiParse"
            >
              <Loader2 v-if="aiParsing" class="w-4 h-4 animate-spin" />
              <Sparkles v-else class="w-4 h-4" />
              {{ aiParsing ? '解析中...' : 'AI 智能解析' }}
            </button>
          </div>
        </Transition>
      </div>

      <!-- 双栏布局容器 -->
      <div class="publish-layout">
        <!-- 左栏：表单 -->
        <div class="publish-left">
          <h2 class="section-title">
            <ImagePlus class="w-5 h-5 text-primary" />
            编辑活动信息
          </h2>

          <div class="form-card">
            <!-- 活动标题 -->
            <div class="form-row" :class="{ 'field-error': errors.title }">
              <label class="form-label">
                活动标题 <span class="text-danger">*</span>
              </label>
              <div class="input-with-confidence">
                <input
                  v-model="form.title"
                  type="text"
                  class="form-input"
                  :class="confidenceClass('title')"
                  placeholder="输入活动标题"
                  maxlength="200"
                  @input="clearConfidence('title'); delete errors.title"
                />
                <CheckCircle2 v-if="confidenceIcon('title') === 'high'" class="w-4 h-4 confidence-icon-high" />
                <AlertTriangle v-else-if="confidenceIcon('title') === 'low'" class="w-4 h-4 confidence-icon-low" />
              </div>
              <p v-if="errors.title" class="field-error-msg">{{ errors.title }}</p>
            </div>

            <!-- 活动类型 + 学分类型 双列 -->
            <div class="form-grid">
              <div class="form-row" :class="{ 'field-error': errors.activity_type }">
                <label class="form-label">活动类型 <span class="text-danger">*</span></label>
                <div class="select-wrap">
                  <select
                    v-model="form.activity_type"
                    class="form-input"
                    :class="confidenceClass('activity_type')"
                    :disabled="isActivityTypeDeleted"
                    @change="clearConfidence('activity_type'); delete errors.activity_type"
                  >
                    <option value="">请选择</option>
                    <option v-for="t in configData.activity_types" :key="t" :value="t">{{ t }}</option>
                    <option v-if="isActivityTypeDeleted" :value="form.activity_type" disabled>
                      {{ form.activity_type }}（已删除）
                    </option>
                  </select>
                  <ChevronDown class="select-arrow" />
                </div>
                <p v-if="errors.activity_type" class="field-error-msg">{{ errors.activity_type }}</p>
                <p v-if="isActivityTypeDeleted" class="field-error-msg" style="color: #D97706;">
                  此活动的活动类型已被管理员删除，如需修改请联系超级管理员 ~
                </p>
              </div>
              <div class="form-row" :class="{ 'field-error': errors.credit_type }">
                <label class="form-label">
                  学分类型 <span class="text-danger">*</span>
                  <Lock v-if="isLocked('credit_type')" class="w-3 h-3 inline-block ml-1 text-amber-500 align-text-bottom" />
                </label>
                <div class="select-wrap">
                  <select
                    v-model="form.credit_type"
                    class="form-input"
                    :class="[confidenceClass('credit_type'), { 'input-locked': isLocked('credit_type') }]"
                    :disabled="isLocked('credit_type') || isCreditTypeDeleted"
                    @change="clearConfidence('credit_type'); delete errors.credit_type"
                  >
                    <option value="">请选择</option>
                    <option v-for="t in configData.credit_types" :key="t" :value="t">{{ t }}</option>
                    <option v-if="isCreditTypeDeleted" :value="form.credit_type" disabled>
                      {{ form.credit_type }}（已删除）
                    </option>
                  </select>
                  <ChevronDown class="select-arrow" />
                </div>
                <p v-if="errors.credit_type" class="field-error-msg">{{ errors.credit_type }}</p>
                <p v-if="isCreditTypeDeleted" class="field-error-msg" style="color: #D97706;">
                  此活动的学分类型已被管理员删除，如需修改请联系超级管理员 ~
                </p>
              </div>
            </div>

            <!-- 学分分值（单独一行，与发布页一致） -->
            <div class="form-row" :class="{ 'field-error': errors.credit_value }">
              <label class="form-label">
                学分分值<span class="optional">（选填）</span>
                <Lock v-if="isLocked('credit_value')" class="w-3 h-3 inline-block ml-1 text-amber-500 align-text-bottom" />
              </label>
              <input
                v-model="form.credit_value"
                type="number"
                class="form-input"
                :class="{ 'input-locked': isLocked('credit_value') }"
                placeholder="学分分值（选填）"
                min="0"
                max="2.0"
                step="0.1"
                :disabled="isLocked('credit_value')"
                @input="delete errors.credit_value"
              />
              <p v-if="errors.credit_value" class="field-error-msg">{{ errors.credit_value }}</p>
            </div>

            <!-- 开始时间（独自一行，与发布页一致） -->
            <div class="form-row" :class="{ 'field-error': errors.start_time }">
              <label class="form-label">开始时间 <span class="text-danger">*</span></label>
              <div class="dt-row" :class="confidenceClass('start_time')">
                <el-date-picker
                  v-model="form.start_date"
                  type="date"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  placeholder="选择日期"
                  :teleported="false"
                  class="dt-date"
                  @change="clearConfidence('start_time'); delete errors.start_time"
                />
                <el-time-picker
                  v-model="form.start_time"
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="选择时间"
                  :teleported="false"
                  class="dt-time"
                  @change="clearConfidence('start_time'); delete errors.start_time"
                />
              </div>
              <div class="dt-conf">
                <CheckCircle2 v-if="confidenceIcon('start_time') === 'high'" class="w-4 h-4 text-success" />
                <AlertTriangle v-else-if="confidenceIcon('start_time') === 'low'" class="w-4 h-4 text-accent" />
              </div>
              <p v-if="errors.start_time" class="field-error-msg">{{ errors.start_time }}</p>
            </div>

            <!-- 结束时间（独自一行，与发布页一致） -->
            <div class="form-row" :class="{ 'field-error': errors.end_time }">
              <label class="form-label">结束时间<span class="optional">（选填）</span></label>
              <div class="dt-row" :class="confidenceClass('end_time')">
                <el-date-picker
                  v-model="form.end_date"
                  type="date"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  placeholder="选择日期"
                  :teleported="false"
                  class="dt-date"
                  @change="clearConfidence('end_time'); delete errors.end_time"
                />
                <el-time-picker
                  v-model="form.end_time"
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="选择时间"
                  :teleported="false"
                  class="dt-time"
                  @change="clearConfidence('end_time'); delete errors.end_time"
                />
              </div>
              <div class="dt-conf">
                <CheckCircle2 v-if="confidenceIcon('end_time') === 'high'" class="w-4 h-4 text-success" />
                <AlertTriangle v-else-if="confidenceIcon('end_time') === 'low'" class="w-4 h-4 text-accent" />
              </div>
              <p v-if="errors.end_time" class="field-error-msg">{{ errors.end_time }}</p>
            </div>

            <!-- 地点 -->
            <div class="form-row" :class="{ 'field-error': errors.location }">
              <label class="form-label">
                <MapPin class="w-3.5 h-3.5 inline-block mr-1 align-text-bottom" />
                地点 <span class="text-danger">*</span>
              </label>
              <div class="input-with-confidence">
                <input
                  v-model="form.location"
                  type="text"
                  class="form-input"
                  :class="confidenceClass('location')"
                  placeholder="教室/报告厅/线上链接等"
                  @input="clearConfidence('location'); delete errors.location"
                />
                <CheckCircle2 v-if="confidenceIcon('location') === 'high'" class="w-4 h-4 confidence-icon-high" />
                <AlertTriangle v-else-if="confidenceIcon('location') === 'low'" class="w-4 h-4 confidence-icon-low" />
              </div>
              <p v-if="errors.location" class="field-error-msg">{{ errors.location }}</p>
            </div>

            <!-- 报名截止时间（单独一行，与发布页一致） -->
            <div class="form-row" :class="{ 'field-error': errors.registration_deadline }">
              <label class="form-label">
                报名截止时间 <span class="text-danger">*</span>
                <Lock v-if="isLocked('registration_deadline')" class="w-3 h-3 inline-block ml-1 text-amber-500 align-text-bottom" />
              </label>
              <div class="dt-row" :class="confidenceClass('registration_deadline')">
                <el-date-picker
                  v-model="form.registration_deadline_date"
                  type="date"
                  format="YYYY/MM/DD"
                  value-format="YYYY-MM-DD"
                  placeholder="选择日期"
                  :teleported="false"
                  class="dt-date"
                  @change="clearConfidence('registration_deadline'); delete errors.registration_deadline"
                />
                <el-time-picker
                  v-model="form.registration_deadline_time"
                  format="HH:mm"
                  value-format="HH:mm"
                  placeholder="选择时间"
                  :teleported="false"
                  class="dt-time"
                  @change="clearConfidence('registration_deadline'); delete errors.registration_deadline"
                />
              </div>
              <div class="dt-conf">
                <CheckCircle2 v-if="confidenceIcon('registration_deadline') === 'high'" class="w-4 h-4 text-success" />
                <AlertTriangle v-else-if="confidenceIcon('registration_deadline') === 'low'" class="w-4 h-4 text-accent" />
              </div>
              <p v-if="errors.registration_deadline" class="field-error-msg">{{ errors.registration_deadline }}</p>
            </div>

            <!-- 报名人数上限（单独一行，与发布页一致） -->
            <div class="form-row" :class="{ 'field-error': errors.max_participants }">
              <label class="form-label">
                报名人数上限<span class="optional">（选填）</span>
                <Lock v-if="isLocked('max_participants')" class="w-3 h-3 inline-block ml-1 text-amber-500 align-text-bottom" />
              </label>
              <input
                v-model="form.max_participants"
                type="number"
                class="form-input"
                :class="{ 'input-locked': isLocked('max_participants') }"
                placeholder="0 表示不限制"
                min="0"
                :disabled="isLocked('max_participants')"
                @input="delete errors.max_participants"
              />
              <p v-if="errors.max_participants" class="field-error-msg">{{ errors.max_participants }}</p>
            </div>

            <!-- 活动描述 -->
            <div class="form-row" :class="{ 'field-error': errors.description }">
              <label class="form-label">活动描述 <span class="text-danger">*</span></label>
              <div class="input-with-confidence textarea-wrap">
                <textarea
                  v-model="form.description"
                  class="form-input form-textarea"
                  :class="confidenceClass('description')"
                  placeholder="输入活动详情描述..."
                  rows="5"
                  @input="clearConfidence('description'); delete errors.description"
                />
                <CheckCircle2 v-if="confidenceIcon('description') === 'high'" class="w-4 h-4 confidence-icon-high textarea-icon" />
                <AlertTriangle v-else-if="confidenceIcon('description') === 'low'" class="w-4 h-4 confidence-icon-low textarea-icon" />
              </div>
              <p v-if="errors.description" class="field-error-msg">{{ errors.description }}</p>
            </div>
          </div>
        </div>

        <!-- 右栏：图片 + 按钮 -->
        <div class="publish-right">
          <h2 class="section-title">
            <ImagePlus class="w-5 h-5 text-primary" />
            图片管理
          </h2>

          <div class="form-card">
            <!-- 活动图片 -->
            <div class="form-row" :class="{ 'field-error': errors.images }">
              <label class="form-label">活动图片（第一张为封面）<span class="text-danger">*</span></label>
              <div
                class="image-grid"
                :class="{ 'drag-over': dragOver }"
                @dragover="onDragOver"
                @dragleave="onDragLeave"
                @drop="onDrop"
              >
                <div v-for="(img, i) in activityImages" :key="img.type === 'existing' ? `e-${img.id}` : `n-${(img as UploadedImage).filename}`" class="image-item">
                  <img :src="getImageUrl(img)" alt="" class="image-thumb" />
                  <span v-if="isCoverImage(i)" class="cover-badge">封面</span>
                  <button class="image-remove" @click="removeImage(i)">
                    <X class="w-3 h-3" />
                  </button>
                </div>
                <label class="image-add">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/gif,image/webp,image/bmp"
                    multiple
                    class="hidden-input"
                    @change="handleImageSelect"
                  />
                  <Plus class="w-6 h-6 text-text-disabled" />
                  <span class="text-xs text-text-disabled mt-1">添加</span>
                </label>
              </div>
              <p class="image-hint">支持 jpg/png/bmp/gif/webp，单张不超过10MB</p>
              <p v-if="errors.images" class="field-error-msg">{{ errors.images }}</p>
            </div>

            <!-- 群二维码 -->
            <div class="form-row" style="margin-top: 20px">
              <label class="form-label">
                <QrCode class="w-3.5 h-3.5 inline-block mr-1 align-text-bottom" />
                群二维码<span class="optional">（选填）</span>
              </label>
              <div class="qrcode-upload">
                <template v-if="qrcodeImage">
                  <div class="qrcode-preview">
                    <img :src="qrcodeImage.localUrl" alt="" class="qrcode-img" />
                    <button class="image-remove" @click="removeQrcode">
                      <X class="w-3 h-3" />
                    </button>
                  </div>
                </template>
                <template v-else-if="existingQrcodeUrl">
                  <div class="qrcode-preview">
                    <img :src="existingQrcodeUrl" alt="" class="qrcode-img" />
                    <button class="image-remove" @click="removeQrcode">
                      <X class="w-3 h-3" />
                    </button>
                  </div>
                </template>
                <template v-else>
                  <label class="qrcode-add">
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/gif,image/webp,image/bmp"
                      class="hidden-input"
                      @change="handleQrcodeSelect"
                    />
                    <QrCode class="w-8 h-8 text-text-disabled" />
                    <span class="text-xs text-text-disabled mt-1">上传二维码</span>
                  </label>
                </template>
              </div>
              <p class="image-hint">上传后学生点击参与时弹出</p>
            </div>

            <!-- 底部按钮 -->
            <div class="submit-buttons">
              <button
                class="btn-outline"
                :disabled="submitting !== ''"
                @click="handleSubmit(true)"
              >
                <Loader2 v-if="submitting === 'draft'" class="w-4 h-4 animate-spin" />
                {{ submitting === 'draft' ? '保存中...' : '存为草稿' }}
              </button>
              <button
                class="btn-primary"
                :disabled="submitting !== ''"
                @click="handleSubmit(false)"
              >
                <Loader2 v-if="submitting === 'publish'" class="w-4 h-4 animate-spin" />
                {{ submitting === 'publish' ? '提交中...' : (activityStatus === 'rejected' ? '重新提交审核' : '保存修改') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 全局消息 -->
      <Transition name="fade">
        <div v-if="globalMsg.text" class="global-msg" :class="globalMsg.type">
          <CheckCircle2 v-if="globalMsg.type === 'success'" class="w-4 h-4 shrink-0" />
          <AlertTriangle v-else class="w-4 h-4 shrink-0" />
          {{ globalMsg.text }}
        </div>
      </Transition>
    </template>
  </div>
</template>

<style scoped>
/* ── 页面容器 ── */
.publish-page {
  max-width: 72rem;
  margin: 0 auto;
  padding: 24px 16px 32px;
  position: relative;
}

/* ── 加载状态 ── */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  color: #64748B;
  font-size: 14px;
  gap: 12px;
}

/* ── 驳回提示 ── */
.reject-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #FEF3C7;
  border: 1px solid #F59E0B;
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #92400E;
  font-weight: 500;
}

/* ── 锁定提示 ── */
.lock-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #F1F5F9;
  border: 1px solid #CBD5E1;
  border-radius: 10px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #64748B;
}

/* ── AI 解析区 ── */
.ai-section {
  background: #FFFFFF;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  margin-bottom: 24px;
  overflow: hidden;
}
.ai-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  text-align: left;
  transition: background 150ms ease;
}
.ai-header:hover {
  background: rgba(59, 130, 246, 0.03);
}
.ai-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.ai-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}
.ai-optional {
  font-size: 12px;
  color: #94A3B8;
  margin-left: 2px;
}
.ai-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ai-subtitle {
  font-size: 13px;
  color: #94A3B8;
}
.ai-body {
  padding: 0 16px 16px;
  border-top: 1px solid #F1F5F9;
}
.ai-hint {
  font-size: 13px;
  color: #64748B;
  margin: 12px 0 0;
}
.ai-parse-btn {
  margin-top: 16px;
  max-width: 100%;
}

/* slide 动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 200ms ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.slide-enter-to,
.slide-leave-from {
  max-height: 500px;
  opacity: 1;
}

/* ── 双栏布局 ── */
.publish-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
@media (min-width: 1024px) {
  .publish-layout {
    flex-direction: row;
    align-items: flex-start;
  }
  .publish-left {
    width: 60%;
    flex-shrink: 0;
  }
  .publish-right {
    width: 40%;
    position: sticky;
    top: 80px;
    align-self: flex-start;
  }
}

/* ── 区段标题 ── */
.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 12px;
}

/* ── 表单卡片 ── */
.form-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* ── 表单通用 ── */
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 16px;
}
@media (min-width: 768px) {
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}
.form-row {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 16px;
}
.form-row:first-child {
  margin-top: 0;
}
/* form-grid 内的 row 不要额外 margin-top */
.form-grid > .form-row {
  margin-top: 0;
}
.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #1E293B;
}
.optional {
  font-size: 12px;
  color: #94A3B8;
  margin-left: 4px;
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

/* ── 锁定字段样式 ── */
.input-locked {
  background: #F1F5F9 !important;
  color: #94A3B8 !important;
  cursor: not-allowed;
}
.input-locked-wrap {
  background: #F1F5F9;
}
.input-locked-wrap .datetime-input {
  background: #F1F5F9 !important;
  color: #94A3B8 !important;
  cursor: not-allowed;
}

/* ── 下拉选择 ── */
.select-wrap {
  position: relative;
}
.select-wrap .form-input {
  appearance: none;
  padding-right: 36px;
}
.select-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #94A3B8;
  pointer-events: none;
}

/* ── 日期时间（与发布页一致：使用 el-date-picker/el-time-picker） ── */
.dt-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.dt-date {
  flex: 1;
}
.dt-time {
  width: 140px;
  flex-shrink: 0;
}
.dt-date :deep(.el-input__wrapper),
.dt-time :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  height: 42px;
}
.dt-date :deep(.el-input__wrapper:hover),
.dt-time :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
}
.dt-date :deep(.el-input__wrapper.is-focus),
.dt-time :deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}
.dt-date :deep(.el-input__inner),
.dt-time :deep(.el-input__inner) {
  font-size: 14px;
  color: #1e293b;
}
.dt-conf {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  pointer-events: none;
  z-index: 1;
}
.datetime-row:focus-within {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.datetime-input {
  border: none !important;
  box-shadow: none !important;
  height: 38px;
  flex: 1;
  min-width: 0;
}
.datetime-input:focus {
  border: none !important;
  box-shadow: none !important;
}

/* ── 带后缀输入 ── */
.input-with-suffix {
  position: relative;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  background: white;
  transition: all 150ms ease;
}
.input-with-suffix:focus-within {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.input-with-suffix .form-input {
  border: none !important;
  box-shadow: none !important;
  padding-right: 36px;
}
.input-with-suffix .form-input:focus {
  border: none !important;
  box-shadow: none !important;
}
.input-suffix {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: #64748B;
  pointer-events: none;
}

/* ── 置信度标记 ── */
.confidence-high {
  border-color: var(--color-success) !important;
  background: rgba(16, 185, 129, 0.05);
}
.confidence-low {
  border-color: #F59E0B !important;
  background: rgba(245, 158, 11, 0.05);
}
.input-with-confidence {
  position: relative;
}
.input-with-confidence .form-input {
  padding-right: 36px;
}
.confidence-icon-high {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-success);
}
.confidence-icon-low {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #F59E0B;
}
.textarea-wrap {
  position: relative;
}
.textarea-wrap .form-textarea {
  padding-right: 36px;
}
.textarea-icon {
  position: absolute;
  right: 10px;
  top: 14px;
}

/* ── 错误字段 ── */
.field-error .form-input:not(.datetime-input) {
  border-color: var(--color-danger);
}
.field-error .datetime-row {
  border-color: var(--color-danger);
}
.field-error-msg {
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 2px;
}

/* ── 图片网格 ── */
.image-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.image-grid.drag-over {
  background: rgba(59, 130, 246, 0.05);
  border-radius: 8px;
}
.image-item {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #E2E8F0;
  position: relative;
}
.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.cover-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: #3B82F6;
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1.2;
}
.image-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.85);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 150ms ease;
}
.image-remove:hover {
  background: var(--color-danger);
  transform: scale(1.1);
}
.image-add {
  aspect-ratio: 1;
  border-radius: 8px;
  border: 2px dashed #CBD5E1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms ease;
}
.image-add:hover {
  border-color: #3B82F6;
  background: rgba(59, 130, 246, 0.05);
}
.image-hint {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 8px;
}
.hidden-input {
  display: none;
}

/* ── 群二维码 ── */
.qrcode-upload {
  margin-top: 4px;
}
.qrcode-preview {
  width: 128px;
  height: 128px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #E2E8F0;
  position: relative;
}
.qrcode-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.qrcode-add {
  width: 128px;
  height: 128px;
  border-radius: 8px;
  border: 2px dashed #CBD5E1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms ease;
}
.qrcode-add:hover {
  border-color: #3B82F6;
  background: rgba(59, 130, 246, 0.05);
}

/* ── 底部按钮 ── */
.submit-buttons {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}
.btn-outline {
  flex: 1;
  height: 44px;
  border: 2px solid #3B82F6;
  color: #3B82F6;
  background: transparent;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 150ms ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.btn-outline:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.08);
}
.btn-primary {
  flex: 1;
  height: 44px;
  background: #3B82F6;
  color: white;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 150ms ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.btn-primary:hover:not(:disabled) {
  background: #2563EB;
}
.btn-outline:disabled,
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── 全局消息 ── */
.global-msg {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 90;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}
.global-msg.success {
  background: #ECFDF5;
  color: var(--color-success);
}
.global-msg.error {
  background: #FEF2F2;
  color: var(--color-danger);
}
.fade-enter-active,
.fade-leave-active {
  transition: all 200ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}
</style>
