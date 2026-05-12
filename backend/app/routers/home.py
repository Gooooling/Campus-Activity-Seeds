from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Activity, ActivityImage, Banner, Favorite, Participation, User
from app.schemas.common import success
from app.schemas.home import (
    BannerItem,
    ExpiringFavoriteItem,
    HomeStatsData,
    HotActivityItem,
    PendingIssueItem,
    RecruitingActivityItem,
    StatusSummary,
    UpcomingActivityItem,
)
from app.utils.credit_helper import calculate_credit_gaps
from app.utils.deps import get_current_user_optional

router = APIRouter(prefix="/v1/home", tags=["首页"])


async def _get_cover_map(db: AsyncSession, activity_ids: list[int]) -> dict[int, str]:
    if not activity_ids:
        return {}
    images_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc())
    )
    cover_map: dict[int, str] = {}
    for r in images_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]
    return cover_map


@router.get("/stats")
async def home_stats(
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    seven_days_later = now + timedelta(days=7)

    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    total_activities_result = await db.execute(
        select(func.count(Activity.id)).where(Activity.status.in_(["active", "ended"]))
    )
    total_activities = total_activities_result.scalar() or 0

    hot_result = await db.execute(
        select(Activity)
        .where(Activity.status == "active", Activity.registration_deadline > now)
        .order_by(Activity.participant_count.desc())
        .limit(5)
    )
    hot_raw = hot_result.scalars().all()
    hot_ids = [a.id for a in hot_raw]
    hot_owner_ids = list({a.owner_id for a in hot_raw})

    hot_owner_map = {}
    if hot_owner_ids:
        owners_result = await db.execute(
            select(User.id, User.name).where(User.id.in_(hot_owner_ids))
        )
        hot_owner_map = {r[0]: r[1] for r in owners_result.all()}

    hot_cover_map = await _get_cover_map(db, hot_ids)

    hot_activities = [
        HotActivityItem(
            id=a.id,
            title=a.title,
            cover_image_url=hot_cover_map.get(a.id),
            activity_type=a.activity_type,
            owner_name=hot_owner_map.get(a.owner_id, "未知"),
            registration_deadline=a.registration_deadline,
            participant_count=a.participant_count,
        )
        for a in hot_raw
    ]

    data = HomeStatsData(
        total_users=total_users,
        total_activities=total_activities,
        hot_activities=hot_activities,
    )

    if current_user is None:
        return success(data=data.model_dump(exclude_none=True))

    if current_user.role == "student":
        part_count_result = await db.execute(
            select(func.count(Participation.id))
            .where(Participation.user_id == current_user.id)
        )
        data.my_participation_count = part_count_result.scalar() or 0

        upcoming_result = await db.execute(
            select(Activity)
            .join(Participation, Participation.activity_id == Activity.id)
            .where(
                Participation.user_id == current_user.id,
                Activity.start_time > now,
            )
            .order_by(Activity.start_time.asc())
            .limit(3)
        )
        upcoming_raw = upcoming_result.scalars().all()
        upcoming_cover_map = await _get_cover_map(db, [a.id for a in upcoming_raw])

        data.upcoming_activities = [
            UpcomingActivityItem(
                id=a.id,
                title=a.title,
                cover_image_url=upcoming_cover_map.get(a.id),
                start_time=a.start_time,
                location=a.location,
            )
            for a in upcoming_raw
        ]

        fav_result = await db.execute(
            select(Activity)
            .join(Favorite, Favorite.activity_id == Activity.id)
            .where(
                Favorite.user_id == current_user.id,
                Activity.registration_deadline > now,
                Activity.registration_deadline <= seven_days_later,
            )
            .order_by(Activity.registration_deadline.asc())
            .limit(3)
        )
        fav_raw = fav_result.scalars().all()
        fav_cover_map = await _get_cover_map(db, [a.id for a in fav_raw])

        data.expiring_favorites = [
            ExpiringFavoriteItem(
                id=a.id,
                title=a.title,
                cover_image_url=fav_cover_map.get(a.id),
                registration_deadline=a.registration_deadline,
                participant_count=a.participant_count,
            )
            for a in fav_raw
        ]

        details, total, total_gap = await calculate_credit_gaps(db, current_user.id)
        if total_gap <= 0:
            data.credit_advice_preview = "恭喜！你的学分已全部达标"
        else:
            unreached = [d for d in details if not d.is_reached]
            top_gap_type = unreached[0].type if unreached else ""
            gap_type_names = [d.type for d in unreached]
            if gap_type_names:
                act_count_result = await db.execute(
                    select(func.count(Activity.id)).where(
                        Activity.status == "active",
                        Activity.registration_deadline > now,
                        Activity.credit_type.in_(gap_type_names),
                    )
                )
                act_count = act_count_result.scalar() or 0
                data.credit_advice_preview = (
                    f"你还差 {total_gap:.1f} 分，优先参加{top_gap_type}类活动，"
                    f"本月有 {act_count} 个相关活动"
                )
            else:
                data.credit_advice_preview = f"你还差 {total_gap:.1f} 分"

    elif current_user.role == "activity_owner":
        my_act_count_result = await db.execute(
            select(func.count(Activity.id)).where(
                Activity.owner_id == current_user.id,
                Activity.status.in_(["active", "ended", "rejected"]),
            )
        )
        data.my_activity_count = my_act_count_result.scalar() or 0

        rejected_result = await db.execute(
            select(Activity)
            .where(
                Activity.owner_id == current_user.id,
                Activity.status == "rejected",
            )
            .order_by(Activity.created_at.desc())
        )
        rejected_acts = rejected_result.scalars().all()
        data.pending_issues = [
            PendingIssueItem(
                activity_id=a.id,
                title=a.title,
                status=a.status,
                reject_reason=a.reject_reason or "",
            )
            for a in rejected_acts
        ]

        status_result = await db.execute(
            select(Activity.status, func.count(Activity.id))
            .where(Activity.owner_id == current_user.id)
            .group_by(Activity.status)
        )
        status_counts = {r[0]: r[1] for r in status_result.all()}

        active_total = status_counts.get("active", 0)
        recruiting_result = await db.execute(
            select(func.count(Activity.id)).where(
                Activity.owner_id == current_user.id,
                Activity.status == "active",
                Activity.registration_deadline > now,
            )
        )
        recruiting_count = recruiting_result.scalar() or 0

        data.status_summary = StatusSummary(
            active=active_total,
            recruiting=recruiting_count,
            pending=status_counts.get("pending", 0),
            draft=status_counts.get("draft", 0),
            ended=status_counts.get("ended", 0),
        )

        recruiting_list_result = await db.execute(
            select(Activity)
            .where(
                Activity.owner_id == current_user.id,
                Activity.status == "active",
                Activity.registration_deadline > now,
            )
            .order_by(Activity.registration_deadline.asc())
            .limit(3)
        )
        recruiting_raw = recruiting_list_result.scalars().all()
        rec_cover_map = await _get_cover_map(db, [a.id for a in recruiting_raw])

        data.recruiting_activities = [
            RecruitingActivityItem(
                id=a.id,
                title=a.title,
                cover_image_url=rec_cover_map.get(a.id),
                activity_type=a.activity_type,
                registration_deadline=a.registration_deadline,
                participant_count=a.participant_count,
            )
            for a in recruiting_raw
        ]

    return success(data=data.model_dump(exclude_none=True))


@router.get("/banners")
async def get_banners(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Banner).where(Banner.is_active == True).order_by(Banner.sort_order)
    )
    banners = result.scalars().all()
    return success(data=[
        BannerItem(id=b.id, title=b.title, subtitle=b.subtitle, image_url=b.image_url).model_dump()
        for b in banners
    ])
