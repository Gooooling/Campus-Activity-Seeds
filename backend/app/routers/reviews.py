from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Activity, Participation, Review, User
from app.schemas.common import PaginatedData, success
from app.schemas.reviews import ReviewCreateRequest, ReviewData, ReviewListItem
from app.utils.deps import get_current_user, require_role

router = APIRouter(prefix="/v1/activities", tags=["评价"])


# ---------- 2.9 POST 发表评价 ----------

@router.post("/{activity_id}/reviews")
async def create_review(
    activity_id: int,
    body: ReviewCreateRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    if activity.status != "ended":
        raise HTTPException(status_code=400, detail="只有已结束的活动可以评价")

    part_result = await db.execute(
        select(Participation.id).where(
            Participation.user_id == current_user.id,
            Participation.activity_id == activity_id,
        )
    )
    if part_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="只有参与过该活动的学生可以评价")

    existing_review = await db.execute(
        select(Review.id).where(
            Review.user_id == current_user.id,
            Review.activity_id == activity_id,
        )
    )
    if existing_review.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="你已经评价过该活动")

    review = Review(
        user_id=current_user.id,
        activity_id=activity_id,
        rating=body.rating,
        content=body.content,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return success(
        data=ReviewData(
            id=review.id,
            rating=review.rating,
            content=review.content,
            reviewer_name=current_user.name,
            created_at=review.created_at,
        ).model_dump(mode='json'),
        message="评价成功",
    )


# ---------- 2.9 GET 评价列表 ----------

@router.get("/{activity_id}/reviews")
async def list_reviews(
    activity_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    count_query = select(func.count(Review.id)).where(Review.activity_id == activity_id)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Review, User.name)
        .join(User, Review.user_id == User.id)
        .where(Review.activity_id == activity_id)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(query)).all()

    items = [
        ReviewListItem(
            id=review.id,
            rating=review.rating,
            content=review.content,
            reviewer_name=reviewer_name,
            created_at=review.created_at,
        ).model_dump(mode='json')
        for review, reviewer_name in rows
    ]

    return success(
        data=PaginatedData(total=total, page=page, page_size=page_size, items=items).model_dump(mode='json')
    )
