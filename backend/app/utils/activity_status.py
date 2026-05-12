from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Activity


async def expire_finished_activities(db: AsyncSession) -> None:
    now = datetime.now()
    stmt = (
        update(Activity)
        .where(
            Activity.status == "active",
            Activity.end_time != None,  # noqa: E711
            Activity.end_time <= now,
        )
        .values(status="ended")
    )
    await db.execute(stmt)
    await db.flush()
