from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Notification, User
from app.schemas.common import success
from app.schemas.notifications import NotificationItem, NotificationLink, NotificationListData
from app.utils.deps import get_current_user

router = APIRouter(prefix="/v1/notifications", tags=["消息"])


# ---------- 7.1 消息列表 ----------

@router.get("")
async def list_notifications(
    type: str = Query("all", description="announcement/favorite_reminder/audit_result/all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    unread_count_result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    unread_count = unread_count_result.scalar() or 0

    base_where = [Notification.user_id == current_user.id]
    if type != "all":
        base_where.append(Notification.type == type)

    count_query = select(func.count(Notification.id)).where(*base_where)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Notification)
        .where(*base_where)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    notifications = result.scalars().all()

    items = []
    for n in notifications:
        link = None
        if n.link_type and n.link_id is not None:
            link = NotificationLink(type=n.link_type, id=n.link_id)
        items.append(NotificationItem(
            id=n.id,
            type=n.type,
            title=n.title,
            content=n.content,
            is_read=n.is_read,
            created_at=n.created_at.isoformat(),
            link=link,
            action=n.action,
        ))

    return success(data=NotificationListData(
        unread_count=unread_count,
        items=items,
    ).model_dump(mode='json'))


# ---------- 7.2 标记单条已读 ----------

@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该消息")

    notification.is_read = True
    await db.commit()
    return success(message="标记已读成功")


# ---------- 7.2 标记全部已读 ----------

@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        Notification.__table__.update()
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return success(message="全部标记已读成功")
