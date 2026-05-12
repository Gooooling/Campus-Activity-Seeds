from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------- 常量 ----------

ACTIVITY_STATUSES = ("draft", "pending", "active", "ended", "rejected")

ActivityStatusFilter = Literal["draft", "pending", "active", "ended", "rejected"]
DeadlineFilter = Literal["today", "week", "later", "expired"]
SortBy = Literal["deadline_asc", "deadline_desc", "created_desc"]

ACTIVITY_IMAGE_URL_PREFIX = "/uploads/activities"
QRCODE_URL_PREFIX = "/uploads/qrcodes"


# ---------- 2.4 创建活动 ----------

class CreateActivityRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="活动标题")
    activity_type: str | None = Field(None, description="活动类型（草稿可空）")
    credit_type: str | None = Field(None, description="学分类型（草稿可空）")
    credit_value: float | None = Field(None, ge=0.1, le=1.0, description="学分值")
    start_time: datetime | None = Field(None, description="活动开始时间（草稿可空）")
    end_time: datetime | None = Field(None, description="活动结束时间")
    location: str | None = Field(None, min_length=1, max_length=300, description="活动地点（草稿可空）")
    registration_deadline: datetime | None = Field(None, description="报名截止时间（草稿可空）")
    max_participants: int = Field(0, ge=0, description="最大参与人数，0表示不限")
    description: str | None = Field(None, description="活动详情")
    status: str = Field("active", pattern="^(draft|active)$", description="draft=存为草稿, active=直接发布")
    images: list[str] = Field(default_factory=list, description="已上传的图片文件名数组")
    qrcode: str | None = Field(None, description="已上传的群二维码文件名")

    @field_validator("images")
    @classmethod
    def validate_filenames(cls, v):
        for filename in v:
            if "/" in filename or "\\" in filename or ".." in filename:
                raise ValueError(f"无效的文件名: {filename}")
        return v

    @field_validator("qrcode")
    @classmethod
    def validate_qrcode_filename(cls, v):
        if v is not None and ("/" in v or "\\" in v or ".." in v):
            raise ValueError(f"无效的文件名: {v}")
        return v

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.registration_deadline is not None and self.start_time is not None:
            if self.registration_deadline >= self.start_time:
                raise ValueError("报名截止时间必须早于活动开始时间")
        if self.end_time is not None and self.start_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("活动结束时间必须晚于活动开始时间")
        return self


class CreateActivityData(BaseModel):
    id: int
    status: str


# ---------- 2.1 / 2.7 / 2.8 活动列表项 ----------

class ActivityListItem(BaseModel):
    id: int
    title: str
    activity_type: str
    credit_type: str | None
    credit_value: float | None
    owner_id: int
    owner_name: str
    owner_avatar_url: str | None
    cover_image_url: str | None
    start_time: datetime
    end_time: datetime | None
    location: str
    registration_deadline: datetime
    participant_count: int
    max_participants: int
    status: str
    created_at: datetime
    has_qrcode: bool
    is_favorited: bool
    is_participated: bool
    reject_reason: str | None = None


# ---------- 2.2 活动详情 ----------

class ActivityImageItem(BaseModel):
    id: int
    url: str
    is_cover: bool


class ActivityOwnerBrief(BaseModel):
    id: int
    name: str
    avatar_url: str | None
    bio: str | None
    activity_count: int


class ActivityDetail(BaseModel):
    id: int
    title: str
    activity_type: str
    credit_type: str | None
    credit_value: float | None
    owner: ActivityOwnerBrief
    images: list[ActivityImageItem]
    start_time: datetime
    end_time: datetime | None
    location: str
    registration_deadline: datetime
    max_participants: int
    participant_count: int
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    is_favorited: bool
    is_participated: bool
    show_qrcode: bool
    allow_edit: bool
    allow_delete: bool
    allow_review: bool
    edit_mode: str | None = None


# ---------- 2.5 编辑活动 ----------

REGISTERING_LOCKED_FIELDS = ("title", "credit_type", "credit_value", "start_time", "registration_deadline")


class UpdateActivityRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    activity_type: str | None = None
    credit_type: str | None = None
    credit_value: float | None = Field(None, ge=0.1, le=1.0)
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = Field(None, min_length=1, max_length=300)
    registration_deadline: datetime | None = None
    max_participants: int | None = Field(None, ge=0)
    description: str | None = None
    images: list[str] | None = Field(None, description="追加的图片文件名数组")
    qrcode: str | None = Field(None, description="群二维码文件名")

    @field_validator("images")
    @classmethod
    def validate_filenames(cls, v):
        if v is not None:
            for filename in v:
                if "/" in filename or "\\" in filename or ".." in filename:
                    raise ValueError(f"无效的文件名: {filename}")
        return v

    @field_validator("qrcode")
    @classmethod
    def validate_qrcode_filename(cls, v):
        if v is not None and ("/" in v or "\\" in v or ".." in v):
            raise ValueError(f"无效的文件名: {v}")
        return v


class UpdateActivityData(BaseModel):
    id: int
    status: str
    ignored_fields: list[str] = []
