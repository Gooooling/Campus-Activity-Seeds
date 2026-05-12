from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    Activity,
    ActivityImage,
    ActivityQrcode,
    CreditAccumulation,
    Participation,
    User,
)
from app.schemas.common import PaginatedData, success
from app.schemas.participations import (
    MementoData,
    ParticipationCreateRequest,
    ParticipationData,
    ParticipationListItem,
    ParticipationStatusFilter,
)
from app.utils.activity_status import expire_finished_activities
from app.utils.deps import require_role

router = APIRouter(prefix="/v1/participations", tags=["参与"])


# ---------- 3.1 我要参与 ----------

@router.post("")
async def create_participation(
    body: ParticipationCreateRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == body.activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    await expire_finished_activities(db)
    await db.refresh(activity)

    if activity.registration_deadline <= datetime.now():
        raise HTTPException(status_code=400, detail="报名已截止")

    if activity.status != "active":
        raise HTTPException(status_code=400, detail="该活动当前不可报名")

    if activity.max_participants > 0 and activity.participant_count >= activity.max_participants:
        raise HTTPException(status_code=400, detail="报名人数已满")

    existing = await db.execute(
        select(Participation).where(
            Participation.user_id == current_user.id,
            Participation.activity_id == body.activity_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="你已经参与该活动")

    try:
        participation = Participation(
            user_id=current_user.id,
            activity_id=body.activity_id,
            credit_awarded=False,  # 学分暂不计入，等活动结束才发放
        )
        db.add(participation)

        await db.flush()

        await db.execute(
            update(Activity).where(Activity.id == body.activity_id).values(participant_count=Activity.participant_count + 1)
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="你已经参与该活动")

    qr_result = await db.execute(
        select(ActivityQrcode.url).where(ActivityQrcode.activity_id == body.activity_id)
    )
    qr_row = qr_result.scalar_one_or_none()
    qrcode_url = qr_row if qr_row else None

    await db.commit()

    return success(
        data=ParticipationData(id=participation.id, qrcode_url=qrcode_url).model_dump(),
        message="参与成功",
    )


# ---------- 3.2 取消参与 ----------
@router.delete("/{participation_id}")
async def cancel_participation(
    participation_id: int,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Participation).where(Participation.id == participation_id)
    )
    participation = result.scalar_one_or_none()
    if participation is None:
        raise HTTPException(status_code=404, detail="参与记录不存在")

    if participation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权取消此参与记录")

    # 获取活动信息
    activity_result = await db.execute(
        select(Activity).where(Activity.id == participation.activity_id)
    )
    activity = activity_result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    now = datetime.now()

    # 检查是否可以取消：报名截止时间之前可以取消
    if activity.registration_deadline <= now:
        raise HTTPException(status_code=400, detail="报名已截止，无法取消")

    # 如果学分已发放，需要先删除学分记录
    if participation.credit_awarded:
        credit_result = await db.execute(
            select(CreditAccumulation).where(
                CreditAccumulation.participation_id == participation.id
            )
        )
        credit_record = credit_result.scalar_one_or_none()
        if credit_record is not None:
            await db.execute(
                delete(CreditAccumulation).where(CreditAccumulation.id == credit_record.id)
            )

    # 删除参与记录
    await db.execute(
        delete(Participation).where(Participation.id == participation_id)
    )

    # 减少活动的参与人数
    await db.execute(
        update(Activity)
        .where(Activity.id == activity.id)
        .values(participant_count=Activity.participant_count - 1)
    )

    await db.commit()

    return success(message="取消成功")


# ---------- 3.3 我的参与列表 ----------

@router.get("/my")
async def my_participations(
    status: ParticipationStatusFilter = Query("all", description="状态筛选: active/ended/all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    await expire_finished_activities(db)

    base_conditions = [Participation.user_id == current_user.id]

    if status == "active":
        base_conditions.append(
            (Activity.end_time == None) | (Activity.end_time > now)  # noqa: E711
        )
        base_conditions.append(Activity.status != "ended")
    elif status == "ended":
        base_conditions.append(
            (Activity.end_time != None) & (Activity.end_time <= now)  # noqa: E711
            | (Activity.status == "ended")
        )

    count_query = select(func.count(Participation.id)).join(
        Activity, Participation.activity_id == Activity.id
    ).where(*base_conditions)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Participation, Activity)
        .join(Activity, Participation.activity_id == Activity.id)
        .where(*base_conditions)
        .order_by(Participation.registered_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return success(data=PaginatedData(total=total, page=page, page_size=page_size, items=[]).model_dump(mode='json'))

    activity_ids = [row[1].id for row in rows]

    cover_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url, ActivityImage.is_cover, ActivityImage.sort_order)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc(), ActivityImage.sort_order)
    )
    cover_map: dict[int, str] = {}
    for r in cover_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]

    qr_result = await db.execute(
        select(ActivityQrcode.activity_id, ActivityQrcode.url)
        .where(ActivityQrcode.activity_id.in_(activity_ids))
    )
    qr_map: dict[int, str] = {r[0]: r[1] for r in qr_result.all()}

    owner_ids = list({row[1].owner_id for row in rows})
    owners_result = await db.execute(
        select(User.id, User.name).where(User.id.in_(owner_ids))
    )
    owner_map: dict[int, str] = {r[0]: r[1] for r in owners_result.all()}

    items = []
    for participation, activity in rows:
        is_ended = (activity.end_time is not None and activity.end_time <= now) or activity.status == "ended"
        can_cancel = (
            not is_ended
            and activity.registration_deadline > now
            and not participation.credit_awarded
        )
        items.append(
            ParticipationListItem(
                id=participation.id,
                activity_id=activity.id,
                title=activity.title,
                cover_image_url=cover_map.get(activity.id),
                activity_type=activity.activity_type,
                credit_type=activity.credit_type,
                credit_value=float(activity.credit_value) if activity.credit_value is not None else None,
                owner_name=owner_map.get(activity.owner_id, "未知"),
                start_time=activity.start_time,
                location=activity.location,
                registration_time=participation.registered_at,
                status="ended" if is_ended else "active",
                qrcode_url=qr_map.get(activity.id),
                can_view_memento=is_ended,
                can_cancel=can_cancel,
            ).model_dump()
        )

    return success(
        data=PaginatedData(total=total, page=page, page_size=page_size, items=items).model_dump()
    )


# ---------- 3.4 获取参与纪念卡片数据 ----------

@router.get("/{activity_id}/memento")
async def get_memento(
    activity_id: int,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    part_result = await db.execute(
        select(Participation).where(
            Participation.user_id == current_user.id,
            Participation.activity_id == activity_id,
        )
    )
    if part_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="你未参与该活动")

    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    await expire_finished_activities(db)
    await db.refresh(activity)

    now = datetime.now()
    is_ended = (activity.end_time is not None and activity.end_time <= now) or activity.status == "ended"
    if not is_ended:
        raise HTTPException(status_code=403, detail="活动尚未结束，无法查看纪念卡片")

    cover_result = await db.execute(
        select(ActivityImage.url)
        .where(ActivityImage.activity_id == activity_id)
        .order_by(ActivityImage.is_cover.desc(), ActivityImage.sort_order)
        .limit(1)
    )
    cover_row = cover_result.scalar_one_or_none()

    owner_result = await db.execute(select(User).where(User.id == activity.owner_id))
    owner = owner_result.scalar_one_or_none()
    owner_name = owner.name if owner else "未知"

    return success(
        data=MementoData(
            title=activity.title,
            cover_image_url=cover_row,
            start_time=activity.start_time,
            end_time=activity.end_time,
            owner_name=owner_name,
            credit_type=activity.credit_type,
            credit_value=float(activity.credit_value),
        ).model_dump()
    )
