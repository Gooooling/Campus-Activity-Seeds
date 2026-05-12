from datetime import datetime

from pydantic import BaseModel


class OwnerActivityItem(BaseModel):
    id: int
    title: str
    cover_image_url: str | None
    activity_type: str
    credit_type: str
    credit_value: float | None
    max_participants: int
    registration_deadline: datetime
    participant_count: int
    status: str


class OwnerProfileData(BaseModel):
    id: int
    name: str
    avatar_url: str | None
    bio: str | None
    activity_count: int
    is_self: bool
    activities: list[OwnerActivityItem]
