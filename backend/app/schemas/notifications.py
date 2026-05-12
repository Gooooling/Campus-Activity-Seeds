from pydantic import BaseModel


class NotificationLink(BaseModel):
    type: str
    id: int


class NotificationItem(BaseModel):
    id: int
    type: str
    title: str
    content: str
    is_read: bool
    created_at: str
    link: NotificationLink | None = None
    action: str | None = None  # null=不显示按钮, "edit_activity"=去修改活动, "edit_profile"=去修改资料


class NotificationListData(BaseModel):
    unread_count: int
    items: list[NotificationItem]
