from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ParticipationCreateRequest(BaseModel):
    activity_id: int = Field(..., gt=0, description="活动ID")


class ParticipationData(BaseModel):
    id: int
    qrcode_url: str | None


class ParticipationListItem(BaseModel):
    id: int
    activity_id: int
    title: str
    cover_image_url: str | None
    activity_type: str
    credit_type: str
    credit_value: float | None
    owner_name: str
    start_time: datetime
    location: str
    registration_time: datetime
    status: str
    qrcode_url: str | None
    can_view_memento: bool
    can_cancel: bool = False  # 是否可以取消（截止时间前）


ParticipationStatusFilter = Literal["active", "ended", "all"]


class MementoData(BaseModel):
    title: str
    cover_image_url: str | None
    start_time: datetime
    end_time: datetime | None
    owner_name: str
    credit_type: str
    credit_value: float | None
