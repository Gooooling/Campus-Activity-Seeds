from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import Activity, ActivityImage, User
from app.schemas.common import success
from app.schemas.owners import OwnerActivityItem, OwnerProfileData
from app.utils.deps import get_current_user

router = APIRouter(prefix="/v1/owners", tags=["活动主体主页"])


@router.get("/{owner_id}")
async def get_owner_profile(
    owner_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner_result = await db.execute(
        select(User).where(User.id == owner_id).options(selectinload(User.activity_owner))
    )
    owner = owner_result.scalar_one_or_none()
    if owner is None or owner.role != "activity_owner":
        raise HTTPException(status_code=404, detail="活动主体不存在")

    conditions = [
        Activity.owner_id == owner_id,
        Activity.status.in_(["active", "ended"]),
    ]
    count_query = select(func.count(Activity.id)).where(*conditions)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Activity)
        .where(*conditions)
        .order_by(Activity.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    activities = result.scalars().all()

    activity_ids = [a.id for a in activities]
    images_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc())
    )
    cover_map: dict[int, str] = {}
    for r in images_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]

    activity_items = [
        OwnerActivityItem(
            id=a.id,
            title=a.title,
            cover_image_url=cover_map.get(a.id),
            activity_type=a.activity_type,
            credit_type=a.credit_type,
            credit_value=float(a.credit_value) if a.credit_value is not None else None,
            max_participants=a.max_participants,
            registration_deadline=a.registration_deadline,
            participant_count=a.participant_count,
            status=a.status,
        )
        for a in activities
    ]

    all_count_result = await db.execute(
        select(func.count(Activity.id)).where(
            Activity.owner_id == owner_id,
            Activity.status.in_(["active", "ended"]),
        )
    )
    activity_count = all_count_result.scalar() or 0

    data = OwnerProfileData(
        id=owner.id,
        name=owner.name,
        avatar_url=owner.avatar_url,
        bio=owner.activity_owner.bio if owner.activity_owner else None,
        activity_count=activity_count,
        is_self=(current_user.id == owner_id),
        activities=activity_items,
    )

    return success(data=data.model_dump(mode='json'))
