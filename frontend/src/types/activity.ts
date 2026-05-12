export interface ActivityListItem {
  id: number
  title: string
  activity_type: string
  credit_type: string
  credit_value: number | null
  owner_id: number
  owner_name: string
  owner_avatar_url: string | null
  cover_image_url: string | null
  start_time: string
  end_time: string
  location: string
  registration_deadline: string
  participant_count: number
  max_participants: number
  status: string
  created_at: string
  has_qrcode: boolean
  is_favorited: boolean
  is_participated: boolean
}

export interface ActivityImage {
  id: number
  url: string
  is_cover: boolean
}

export interface ActivityOwner {
  id: number
  name: string
  avatar_url: string | null
  bio: string
  activity_count: number
}

export interface ActivityDetail {
  id: number
  title: string
  activity_type: string
  credit_type: string
  credit_value: number | null
  owner: ActivityOwner
  images: ActivityImage[]
  start_time: string
  end_time: string
  location: string
  registration_deadline: string
  max_participants: number
  participant_count: number
  description: string
  status: string
  created_at: string
  updated_at: string
  is_favorited: boolean
  is_participated: boolean
  show_qrcode: boolean
  allow_review: boolean
  allow_edit: boolean
  allow_delete: boolean
}

export interface ActivityReview {
  id: number
  rating: number
  content: string
  reviewer_name: string
  created_at: string
}

export interface ReviewListData {
  total: number
  items: ActivityReview[]
}

export interface ParticipationItem {
  id: number
  activity_id: number
  title: string
  cover_image_url: string | null
  activity_type: string
  credit_type: string
  credit_value: number | null
  owner_name: string
  start_time: string
  location: string
  registration_time: string
  status: 'active' | 'ended'
  qrcode_url: string | null
  can_view_memento: boolean
  can_cancel: boolean
}

export interface CreditDetail {
  type: string
  current: number
  required: number
  is_reached: boolean
  gap: number
}

export interface CreditSummary {
  details: CreditDetail[]
  yearly_total: number
  total: number
  total_required: number
  is_total_reached: boolean
  total_gap: number
}

export interface StudentProfile {
  user_id: number
  account: string
  role: string
  name: string
  avatar_url: string | null
  college_id: number
  college_name: string
  phone: string
  email: string
  status: string
}

export interface OwnerProfile {
  user_id: number
  account: string
  role: string
  owner_name: string
  owner_type: string
  avatar_url: string | null
  college_id: number
  college_name: string
  bio: string
  contact_name: string
  contact_student_id: string
  contact_phone: string
  advisor_name: string
  advisor_contact: string
  status: string
}

export interface OwnerProfileUpdate {
  owner_name: string
  owner_type: string
  college_id: number
  bio: string
}

export interface ContactUpdate {
  contact_name: string
  contact_student_id: string
  contact_phone: string
}

export interface AdvisorUpdate {
  advisor_name: string
  advisor_contact: string
}

// ── 消息中心类型 ──
export interface NotificationLink {
  type: string
  id: number
}

export interface NotificationItem {
  id: number
  type: 'announcement' | 'favorite_reminder' | 'audit_result'
  title: string
  content: string
  is_read: boolean
  created_at: string
  link: NotificationLink | null
  action: 'edit_activity' | 'edit_profile' | null
}

export interface NotificationListData {
  unread_count: number
  items: NotificationItem[]
}

// ── P8 活动主体对外主页类型 ──
export interface OwnerPublicActivity {
  id: number
  title: string
  cover_image_url: string | null
  activity_type: string
  credit_type: string
  credit_value: number | null
  registration_deadline: string
  participant_count: number
  max_participants: number
  status: string
}

export interface OwnerPublicProfile {
  id: number
  name: string
  avatar_url: string | null
  bio: string
  activity_count: number
  is_self: boolean
  activities: OwnerPublicActivity[]
}

// ── P11 我的活动列表类型 ──
export interface MyActivityItem extends ActivityListItem {
  reject_reason?: string | null
}

// ── AI 学分分析类型 ──
export interface PriorityItem {
  type: string
  gap: number
}

export interface RecommendedActivity {
  id: number
  title: string
  credit_type: string
  credit_value: number | null
  registration_deadline: string
  location: string
  cover_image_url: string | null
  match_reason: string
}

export interface CreditAdvice {
  total_gap: number
  priority_list: PriorityItem[]
  recommended_activities: RecommendedActivity[]
  summary: string
}

// ── P17-1 数据看板类型 ──
export interface TypeDistribution {
  type: string
  count: number
  percentage: number
}

export interface CollegeDistribution {
  college: string
  count: number
}

export interface TrendItem {
  date: string
  new_activities: number
  new_participations: number
}

// ── P17-2 活动审核类型 ──
export interface AuditActivityItem {
  id: number
  title: string
  activity_type: string
  credit_type: string
  credit_value: number | null
  owner_id: number
  owner_name: string
  owner_avatar_url: string | null
  cover_image_url: string | null
  start_time: string
  end_time: string
  location: string
  registration_deadline: string
  max_participants: number
  participant_count: number
  status: string
  reject_reason?: string | null
  description: string
  created_at: string
}

// ── P17-3 主体审核类型 ──
export interface AuditOwnerItem {
  id: number
  account: string
  owner_name: string
  owner_type: string
  avatar_url: string | null
  college_id: number
  college_name: string
  contact_name: string
  contact_student_id: string
  contact_phone: string
  advisor_name: string
  advisor_contact: string
  bio: string
  status: string
  reject_reason?: string | null
  created_at: string
}

export interface ContactChangeItem {
  id: number
  owner_id: number
  owner_name: string
  old_contact_name: string
  old_contact_student_id: string
  old_contact_phone: string
  new_contact_name: string
  new_contact_student_id: string
  new_contact_phone: string
  submitted_at: string
  status: string
}

// ── P17-4 活动管理类型 ──
export interface AdminActivityItem {
  id: number
  title: string
  activity_type: string
  credit_type: string
  credit_value: number | null
  owner_id: number
  owner_name: string
  owner_avatar_url: string | null
  cover_image_url: string | null
  start_time: string
  end_time: string
  location: string
  registration_deadline: string
  max_participants: number
  participant_count: number
  status: string
  created_at: string
}

// ── P17-5 用户管理类型 ──
export interface AdminUserItem {
  user_id: number
  account: string
  role: string
  name: string
  avatar_url: string | null
  college_name: string
  status: string
  created_at: string
}

export interface DashboardData {
  total_users: number
  total_activities: number
  total_participations: number
  pending_activities: number
  pending_owners: number
  today_new: number
  type_distribution: TypeDistribution[]
  college_distribution: CollegeDistribution[]
  trend: TrendItem[]
}

// ── P17-6 操作日志类型 ──
export interface LogItem {
  id: number
  user_id: number
  user_name: string
  operation: string
  target_type: string
  target_id: number
  detail: string | null
  ip_address: string
  created_at: string
}

// ── P17-7 公告管理类型 ──
export interface AnnouncementItem {
  id: number
  content: string
  created_at: string
}
