from datetime import datetime
from pydantic import BaseModel, Field


class CreateCollegeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class RejectActivityRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


# ---------- 活动主体审核模式 ----------


class OwnerPendingItem(BaseModel):
    """待审活动主体列表项"""

    id: int
    account: str
    owner_name: str
    owner_type: str
    avatar_url: str | None = None
    college_name: str | None = None
    contact_name: str
    contact_student_id: str
    contact_phone: str
    advisor_name: str | None = None
    advisor_contact: str | None = None
    bio: str | None = None
    status: str
    reject_reason: str | None = None
    created_at: str


class RejectOwnerRequest(BaseModel):
    """驳回活动主体审核请求"""

    reason: str = Field(..., min_length=1, max_length=500)


# ---------- 负责人变更审核模式 ----------


class ContactChangeItem(BaseModel):
    """待审负责人变更列表项"""

    id: int
    owner_name: str
    old_contact_name: str
    old_contact_student_id: str
    old_contact_phone: str
    new_contact_name: str
    new_contact_student_id: str
    new_contact_phone: str
    submitted_at: str
    status: str


# ---------- 用户管理模式 ----------


class UserListItem(BaseModel):
    """用户列表项"""

    user_id: int
    account: str
    name: str
    role: str
    status: str
    avatar_url: str | None = None
    college_name: str | None = None
    college_id: int | None = None
    created_at: datetime


class CreateUserRequest(BaseModel):
    """创建账号请求"""

    role: str = Field(..., pattern="^(student|activity_owner|admin|super_admin)$")
    account: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)


class UpdateUserStatusRequest(BaseModel):
    """更新用户状态请求"""

    status: str = Field(..., pattern="^(active|disabled)$")


class CreateUserResponse(BaseModel):
    """创建账号响应（返回新生成的密码）"""

    user_id: int
    account: str
    name: str
    initial_password: str


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""

    new_password: str


class TypeDistributionItem(BaseModel):
    type: str
    count: int
    percentage: float


class CollegeDistributionItem(BaseModel):
    college: str
    count: int


class TrendItem(BaseModel):
    date: str
    new_activities: int
    new_participations: int


class DashboardData(BaseModel):
    total_users: int
    total_activities: int
    total_participations: int
    pending_activities: int
    pending_owners: int
    today_new: int
    type_distribution: list[TypeDistributionItem]
    college_distribution: list[CollegeDistributionItem]
    trend: list[TrendItem]


# ---------- 活动管理 ----------

class AdminActivityItem(BaseModel):
    id: int
    title: str
    owner_name: str
    activity_type: str
    credit_type: str
    status: str
    cover_image_url: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None
    credit_value: float | None = None
    max_participants: int | None = None
    description: str | None = None
    reject_reason: str | None = None
    registration_deadline: datetime
    participant_count: int
    created_at: datetime


# ---------- 操作日志 ----------

class OperationLogItem(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None
    operation: str
    target_type: str | None
    target_id: int | None
    detail: str | None
    ip_address: str | None
    created_at: datetime


# ---------- 公告管理 ----------

class CreateAnnouncementRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


# ---------- 轮播图管理 ----------

class BannerCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    subtitle: str | None = Field(None, max_length=200)
    image_url: str = Field(..., min_length=1, max_length=500)
    sort_order: int = Field(0, ge=0)
    is_active: bool = Field(True)


class BannerUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    subtitle: str | None = Field(None, max_length=200)
    image_url: str | None = Field(None, min_length=1, max_length=500)
    sort_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class AdminBannerItem(BaseModel):
    id: int
    title: str
    subtitle: str | None
    image_url: str
    sort_order: int
    is_active: bool
    created_at: str
