from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: str,
    title: str,
    content: str,
    link_type: str | None = None,
    link_id: int | None = None,
    action: str | None = None,
) -> None:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        link_type=link_type,
        link_id=link_id,
    )
    db.add(notification)
    await db.flush()
