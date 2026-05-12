from datetime import datetime

from pydantic import BaseModel


class HotActivityItem(BaseModel):
    id: int
    title: str
    cover_image_url: str | None
    activity_type: str
    owner_name: str
    registration_deadline: datetime
    participant_count: int


class UpcomingActivityItem(BaseModel):
    id: int
    title: str
    cover_image_url: str | None
    start_time: datetime
    location: str


class ExpiringFavoriteItem(BaseModel):
    id: int
    title: str
    cover_image_url: str | None
    registration_deadline: datetime
    participant_count: int


class RecruitingActivityItem(BaseModel):
    id: int
    title: str
    cover_image_url: str | None
    activity_type: str
    registration_deadline: datetime
    participant_count: int


class PendingIssueItem(BaseModel):
    activity_id: int
    title: str
    status: str
    reject_reason: str


class StatusSummary(BaseModel):
    active: int
    recruiting: int
    pending: int
    draft: int
    ended: int


class HomeStatsData(BaseModel):
    total_users: int
    total_activities: int
    hot_activities: list[HotActivityItem]
    my_participation_count: int | None = None
    upcoming_activities: list[UpcomingActivityItem] | None = None
    expiring_favorites: list[ExpiringFavoriteItem] | None = None
    credit_advice_preview: str | None = None
    my_activity_count: int | None = None
    pending_issues: list[PendingIssueItem] | None = None
    status_summary: StatusSummary | None = None
    recruiting_activities: list[RecruitingActivityItem] | None = None


class BannerItem(BaseModel):
    id: int
    title: str
    subtitle: str | None
    image_url: str
