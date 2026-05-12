from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    Activity,
    ActivityImage,
    ActivityQrcode,
    Favorite,
    Participation,
    User,
)
from app.schemas.activities import ActivityListItem
from app.schemas.common import PaginatedData, success
from app.schemas.favorites import FavoriteToggleData, FavoriteToggleRequest
from app.utils.deps import require_role

router = APIRouter(prefix="/v1/favorites", tags=["收藏"])


# ---------- 4.1 收藏/取消收藏 ----------

@router.post("")
async def toggle_favorite(
    body: FavoriteToggleRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == body.activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    fav_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.activity_id == body.activity_id,
        )
    )
    existing = fav_result.scalar_one_or_none()

    if existing is not None:
        await db.delete(existing)
        await db.commit()
        return success(
            data=FavoriteToggleData(is_favorited=False).model_dump(),
            message="取消收藏成功",
        )
    else:
        favorite = Favorite(
            user_id=current_user.id,
            activity_id=body.activity_id,
        )
        db.add(favorite)
        await db.commit()
        return success(
            data=FavoriteToggleData(is_favorited=True).model_dump(),
            message="收藏成功",
        )


# ---------- 4.2 我的收藏列表 ----------

@router.get("/my")
async def my_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    base_conditions = [Favorite.user_id == current_user.id]

    count_query = select(func.count(Favorite.id)).where(*base_conditions)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Favorite, Activity)
        .join(Activity, Favorite.activity_id == Activity.id)
        .where(*base_conditions)
        .order_by(Activity.registration_deadline.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return success(data=PaginatedData(total=total, page=page, page_size=page_size, items=[]).model_dump(mode='json'))

    activity_ids = [row[1].id for row in rows]

    owner_ids = list({row[1].owner_id for row in rows})
    owners_result = await db.execute(
        select(User.id, User.name, User.avatar_url).where(User.id.in_(owner_ids))
    )
    owner_map = {r[0]: {"name": r[1], "avatar_url": r[2]} for r in owners_result.all()}

    all_images_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url, ActivityImage.is_cover, ActivityImage.sort_order)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc(), ActivityImage.sort_order)
    )
    cover_map: dict[int, str] = {}
    for r in all_images_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]

    qrcodes_result = await db.execute(
        select(ActivityQrcode.activity_id).where(ActivityQrcode.activity_id.in_(activity_ids))
    )
    qrcode_ids = {r[0] for r in qrcodes_result.all()}

    part_result = await db.execute(
        select(Participation.activity_id).where(
            Participation.user_id == current_user.id,
            Participation.activity_id.in_(activity_ids),
        )
    )
    part_ids = {r[0] for r in part_result.all()}

    items = []
    for favorite, activity in rows:
        owner_info = owner_map.get(activity.owner_id, {"name": "未知", "avatar_url": None})
        items.append(
            ActivityListItem(
                id=activity.id,
                title=activity.title,
                activity_type=activity.activity_type,
                credit_type=activity.credit_type,
                credit_value=float(activity.credit_value) if activity.credit_value is not None else None,
                owner_id=activity.owner_id,
                owner_name=owner_info["name"],
                owner_avatar_url=owner_info["avatar_url"],
                cover_image_url=cover_map.get(activity.id),
                start_time=activity.start_time,
                end_time=activity.end_time,
                location=activity.location,
                registration_deadline=activity.registration_deadline,
                participant_count=activity.participant_count,
                max_participants=activity.max_participants,
                status=activity.status,
                created_at=activity.created_at,
                has_qrcode=activity.id in qrcode_ids,
                is_favorited=True,
                is_participated=activity.id in part_ids,
            ).model_dump()
        )

    return success(
        data=PaginatedData(total=total, page=page, page_size=page_size, items=items).model_dump()
    )
