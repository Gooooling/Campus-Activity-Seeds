from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import (
    Activity,
    ActivityImage,
    ActivityQrcode,
    CreditAccumulation,
    Favorite,
    Participation,
    Review,
    User,
)
from app.schemas.activities import (
    ACTIVITY_IMAGE_URL_PREFIX,
    QRCODE_URL_PREFIX,
    ActivityDetail,
    ActivityImageItem,
    ActivityListItem,
    ActivityOwnerBrief,
    CreateActivityData,
    CreateActivityRequest,
    DeadlineFilter,
    REGISTERING_LOCKED_FIELDS,
    SortBy,
    UpdateActivityData,
    UpdateActivityRequest,
)
from app.schemas.common import PaginatedData, success
from app.utils.activity_status import expire_finished_activities
from app.utils.deps import get_current_active_owner, get_current_user, require_admin, require_role
from app.utils.file_helper import delete_activity_files
from app.utils.operation_log_helper import log_operation

router = APIRouter(prefix="/v1/activities", tags=["活动"])


# ---------- 自然周辅助函数 ----------

def _get_deadline_filter_bounds(deadline_filter: str) -> tuple[datetime | None, datetime | None]:
    """根据 deadline_filter 返回 (起始时间, 结束时间)，自然周以周一为起始日。"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    if deadline_filter == "today":
        return today_start, today_end

    if deadline_filter == "week":
        days_since_monday = now.weekday()  # 0=周一, 6=周日
        monday_start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sunday_end = (monday_start + timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return monday_start, sunday_end

    if deadline_filter == "later":
        days_since_monday = now.weekday()
        monday_start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        next_monday_start = monday_start + timedelta(days=7)
        return next_monday_start, None

    if deadline_filter == "expired":
        return None, now

    return None, None


# ---------- 2.1 活动列表 ----------

@router.get("")
async def list_activities(
    keyword: str | None = Query(None, description="搜索关键词"),
    credit_type: str | None = Query(None, description="学分类型筛选"),
    activity_type: str | None = Query(None, description="活动类型筛选"),
    deadline_filter: DeadlineFilter | None = Query(None, description="截止时间筛选"),
    sort_by: SortBy = Query("deadline_asc", description="排序方式"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    await expire_finished_activities(db)

    # 基础查询：status=active
    base_where = [Activity.status == "active"]

    # 截止时间过滤
    if deadline_filter is not None:
        start, end = _get_deadline_filter_bounds(deadline_filter)
        if start is not None:
            base_where.append(Activity.registration_deadline >= start)
        if end is not None:
            base_where.append(Activity.registration_deadline <= end)
    else:
        # 默认：只返回未截止的活动
        base_where.append(Activity.registration_deadline > now)

    # 可选筛选
    if credit_type is not None:
        base_where.append(Activity.credit_type == credit_type)
    if activity_type is not None:
        base_where.append(Activity.activity_type == activity_type)
    if keyword is not None and keyword.strip():
        base_where.append(Activity.title.ilike(f"%{keyword.strip()}%"))

    # 计数
    count_query = select(func.count(Activity.id)).where(*base_where)
    total = (await db.execute(count_query)).scalar() or 0

    # 排序
    if sort_by == "deadline_desc":
        order = Activity.registration_deadline.desc()
    elif sort_by == "created_desc":
        order = Activity.created_at.desc()
    else:
        order = Activity.registration_deadline.asc()

    # 分页查询
    offset = (page - 1) * page_size
    query = select(Activity).where(*base_where).order_by(order).offset(offset).limit(page_size)
    result = await db.execute(query)
    activities = result.scalars().all()

    if not activities:
        return success(data=PaginatedData(total=total, page=page, page_size=page_size, items=[]).model_dump(mode='json'))

    # 批量查询关联数据
    activity_ids = [a.id for a in activities]
    owner_ids = list({a.owner_id for a in activities})

    # 活动主体信息
    owners_result = await db.execute(
        select(User.id, User.name, User.avatar_url).where(User.id.in_(owner_ids))
    )
    owner_map = {r[0]: {"name": r[1], "avatar_url": r[2]} for r in owners_result.all()}

    # 封面图片：优先 is_cover=True，其次按 sort_order 取第一张
    all_images_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url, ActivityImage.is_cover, ActivityImage.sort_order)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc(), ActivityImage.sort_order)
    )
    cover_map: dict[int, str] = {}
    for r in all_images_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]

    # 二维码
    qrcodes_result = await db.execute(
        select(ActivityQrcode.activity_id).where(ActivityQrcode.activity_id.in_(activity_ids))
    )
    qrcode_ids = {r[0] for r in qrcodes_result.all()}

    # 收藏
    fav_result = await db.execute(
        select(Favorite.activity_id).where(
            Favorite.user_id == current_user.id,
            Favorite.activity_id.in_(activity_ids),
        )
    )
    fav_ids = {r[0] for r in fav_result.all()}

    # 参与
    part_result = await db.execute(
        select(Participation.activity_id).where(
            Participation.user_id == current_user.id,
            Participation.activity_id.in_(activity_ids),
        )
    )
    part_ids = {r[0] for r in part_result.all()}

    # 组装
    items = []
    for a in activities:
        owner_info = owner_map.get(a.owner_id, {"name": "未知", "avatar_url": None})
        items.append(
            ActivityListItem(
                id=a.id,
                title=a.title,
                activity_type=a.activity_type,
                credit_type=a.credit_type,
                credit_value=float(a.credit_value) if a.credit_value is not None else None,
                owner_id=a.owner_id,
                owner_name=owner_info["name"],
                owner_avatar_url=owner_info["avatar_url"],
                cover_image_url=cover_map.get(a.id),
                start_time=a.start_time,
                end_time=a.end_time,
                location=a.location,
                registration_deadline=a.registration_deadline,
                participant_count=a.participant_count,
                max_participants=a.max_participants,
                status=a.status,
                created_at=a.created_at,
                has_qrcode=a.id in qrcode_ids,
                is_favorited=a.id in fav_ids,
                is_participated=a.id in part_ids,
            ).model_dump()
        )

    return success(
        data=PaginatedData(total=total, page=page, page_size=page_size, items=items).model_dump()
    )


# ---------- 2.4 创建活动 ----------

@router.post("")
async def create_activity(
    body: CreateActivityRequest,
    request: Request,
    current_user: User = Depends(get_current_active_owner),
    db: AsyncSession = Depends(get_db),
):
    # 检查是否有被打回的活动未处理
    rejected_result = await db.execute(
        select(Activity.id).where(
            Activity.owner_id == current_user.id,
            Activity.status == "rejected",
        ).limit(1)
    )
    if rejected_result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="请先处理被打回的活动")

    activity = Activity(
        owner_id=current_user.id,
        title=body.title,
        activity_type=body.activity_type,
        credit_type=body.credit_type,
        credit_value=body.credit_value,
        start_time=body.start_time,
        end_time=body.end_time,
        location=body.location,
        registration_deadline=body.registration_deadline,
        max_participants=body.max_participants,
        description=body.description,
        status=body.status,
    )
    db.add(activity)
    await db.flush()

    # 图片
    for idx, filename in enumerate(body.images):
        image = ActivityImage(
            activity_id=activity.id,
            url=f"{ACTIVITY_IMAGE_URL_PREFIX}/{filename}",
            is_cover=(idx == 0),
            sort_order=idx,
        )
        db.add(image)

    # 二维码
    if body.qrcode:
        qrcode = ActivityQrcode(
            activity_id=activity.id,
            url=f"{QRCODE_URL_PREFIX}/{body.qrcode}",
        )
        db.add(qrcode)

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="create_activity",
        target_type="activity",
        target_id=activity.id,
        detail=f"创建活动：{activity.title}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()

    return success(
        data=CreateActivityData(id=activity.id, status=activity.status).model_dump(),
        message="创建成功",
    )


# ---------- 2.8 我的活动列表（必须在 /{activity_id} 之前注册） ----------

@router.get("/my")
async def my_activities(
    status: str | None = Query(None, description="状态筛选: draft/pending/active/ended/rejected"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(require_role("activity_owner")),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Activity.owner_id == current_user.id]
    if status is not None:
        conditions.append(Activity.status == status)

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

    if not activities:
        return success(data=PaginatedData(total=total, page=page, page_size=page_size, items=[]).model_dump(mode='json'))

    activity_ids = [a.id for a in activities]

    # 封面图片
    all_images_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url, ActivityImage.is_cover, ActivityImage.sort_order)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc(), ActivityImage.sort_order)
    )
    cover_map: dict[int, str] = {}
    for r in all_images_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]

    # 二维码
    qrcodes_result = await db.execute(
        select(ActivityQrcode.activity_id).where(ActivityQrcode.activity_id.in_(activity_ids))
    )
    qrcode_ids = {r[0] for r in qrcodes_result.all()}

    # 收藏和参与（活动主体视角不需要，但 Schema 要求，填充 False）
    items = []
    for a in activities:
        items.append(
            ActivityListItem(
                id=a.id,
                title=a.title,
                activity_type=a.activity_type,
                credit_type=a.credit_type,
                credit_value=float(a.credit_value) if a.credit_value is not None else None,
                owner_id=a.owner_id,
                owner_name=current_user.name,
                owner_avatar_url=current_user.avatar_url,
                cover_image_url=cover_map.get(a.id),
                start_time=a.start_time,
                end_time=a.end_time,
                location=a.location,
                registration_deadline=a.registration_deadline,
                participant_count=a.participant_count,
                max_participants=a.max_participants,
                status=a.status,
                created_at=a.created_at,
                has_qrcode=a.id in qrcode_ids,
                is_favorited=False,
                is_participated=False,
                reject_reason=a.reject_reason if a.status == "rejected" else None,
            ).model_dump()
        )

    return success(
        data=PaginatedData(total=total, page=page, page_size=page_size, items=items).model_dump()
    )


# ---------- 2.7 某活动主体的活动列表（必须在 /{activity_id} 之前注册） ----------

@router.get("/owner/{owner_id}")
async def owner_activities(
    owner_id: int,
    status: str | None = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 检查活动主体是否存在
    owner_result = await db.execute(select(User).where(User.id == owner_id))
    owner = owner_result.scalar_one_or_none()
    if owner is None or owner.role != "activity_owner":
        raise HTTPException(status_code=404, detail="活动主体不存在")

    # 默认只返回 active 和 ended
    if status is not None:
        conditions = [Activity.owner_id == owner_id, Activity.status == status]
    else:
        conditions = [Activity.owner_id == owner_id, Activity.status.in_(["active", "ended"])]

    count_query = select(func.count(Activity.id)).where(*conditions)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Activity)
        .where(*conditions)
        .order_by(Activity.registration_deadline.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    activities = result.scalars().all()

    if not activities:
        return success(data=PaginatedData(total=total, page=page, page_size=page_size, items=[]).model_dump(mode='json'))

    activity_ids = [a.id for a in activities]

    # 封面图片
    all_images_result = await db.execute(
        select(ActivityImage.activity_id, ActivityImage.url, ActivityImage.is_cover, ActivityImage.sort_order)
        .where(ActivityImage.activity_id.in_(activity_ids))
        .order_by(ActivityImage.activity_id, ActivityImage.is_cover.desc(), ActivityImage.sort_order)
    )
    cover_map: dict[int, str] = {}
    for r in all_images_result.all():
        if r[0] not in cover_map:
            cover_map[r[0]] = r[1]

    # 二维码
    qrcodes_result = await db.execute(
        select(ActivityQrcode.activity_id).where(ActivityQrcode.activity_id.in_(activity_ids))
    )
    qrcode_ids = {r[0] for r in qrcodes_result.all()}

    # 收藏
    fav_result = await db.execute(
        select(Favorite.activity_id).where(
            Favorite.user_id == current_user.id,
            Favorite.activity_id.in_(activity_ids),
        )
    )
    fav_ids = {r[0] for r in fav_result.all()}

    # 参与
    part_result = await db.execute(
        select(Participation.activity_id).where(
            Participation.user_id == current_user.id,
            Participation.activity_id.in_(activity_ids),
        )
    )
    part_ids = {r[0] for r in part_result.all()}

    items = []
    for a in activities:
        items.append(
            ActivityListItem(
                id=a.id,
                title=a.title,
                activity_type=a.activity_type,
                credit_type=a.credit_type,
                credit_value=float(a.credit_value) if a.credit_value is not None else None,
                owner_id=a.owner_id,
                owner_name=owner.name,
                owner_avatar_url=owner.avatar_url,
                cover_image_url=cover_map.get(a.id),
                start_time=a.start_time,
                end_time=a.end_time,
                location=a.location,
                registration_deadline=a.registration_deadline,
                participant_count=a.participant_count,
                max_participants=a.max_participants,
                status=a.status,
                created_at=a.created_at,
                has_qrcode=a.id in qrcode_ids,
                is_favorited=a.id in fav_ids,
                is_participated=a.id in part_ids,
            ).model_dump()
        )

    return success(
        data=PaginatedData(total=total, page=page, page_size=page_size, items=items).model_dump()
    )


# ---------- 2.2 活动详情 ----------

@router.get("/{activity_id}")
async def get_activity_detail(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Activity)
        .options(joinedload(Activity.owner).joinedload(User.activity_owner))
        .where(Activity.id == activity_id)
    )
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    # Extract owner from joinedload
    owner = activity.owner

    # 图片列表
    images_result = await db.execute(
        select(ActivityImage)
        .where(ActivityImage.activity_id == activity_id)
        .order_by(ActivityImage.sort_order)
    )
    images = [
        ActivityImageItem(id=img.id, url=img.url, is_cover=img.is_cover)
        for img in images_result.scalars().all()
    ]

    # 该主体的活动数（active + ended）
    owner_activity_count = 0
    if owner is not None:
        count_result = await db.execute(
            select(func.count(Activity.id)).where(
                Activity.owner_id == owner.id,
                Activity.status.in_(["active", "ended"]),
            )
        )
        owner_activity_count = count_result.scalar() or 0

    owner_brief = ActivityOwnerBrief(
        id=owner.id if owner else activity.owner_id,
        name=owner.name if owner else "未知",
        avatar_url=owner.avatar_url if owner else None,
        bio=owner.activity_owner.bio if owner and owner.activity_owner else None,
        activity_count=owner_activity_count,
    )

    # 计算字段
    is_owner = current_user.id == activity.owner_id

    fav_result = await db.execute(
        select(Favorite.id).where(
            Favorite.user_id == current_user.id,
            Favorite.activity_id == activity_id,
        )
    )
    is_favorited = fav_result.scalar_one_or_none() is not None

    part_result = await db.execute(
        select(Participation.id).where(
            Participation.user_id == current_user.id,
            Participation.activity_id == activity_id,
        )
    )
    is_participated = part_result.scalar_one_or_none() is not None

    # 二维码是否可展示
    qrcode_result = await db.execute(
        select(ActivityQrcode.id).where(ActivityQrcode.activity_id == activity_id)
    )
    has_qrcode = qrcode_result.scalar_one_or_none() is not None
    show_qrcode = is_participated

    allow_review = is_participated and activity.status == "ended"

    if is_owner:
        if activity.status in ("draft", "active", "rejected"):
            allow_edit = True
            edit_mode = "full"
        elif activity.status == "ended":
            allow_edit = True
            edit_mode = "images_only"
        else:
            allow_edit = False
            edit_mode = None
    else:
        allow_edit = False
        edit_mode = None

    allow_delete = is_owner and activity.status in ("draft", "pending", "rejected")

    detail = ActivityDetail(
        id=activity.id,
        title=activity.title,
        activity_type=activity.activity_type,
        credit_type=activity.credit_type,
        credit_value=float(activity.credit_value) if activity.credit_value is not None else None,
        owner=owner_brief,
        images=images,
        start_time=activity.start_time,
        end_time=activity.end_time,
        location=activity.location,
        registration_deadline=activity.registration_deadline,
        max_participants=activity.max_participants,
        participant_count=activity.participant_count,
        description=activity.description,
        status=activity.status,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
        is_favorited=is_favorited,
        is_participated=is_participated,
        show_qrcode=show_qrcode,
        allow_edit=allow_edit,
        allow_delete=allow_delete,
        allow_review=allow_review,
        edit_mode=edit_mode,
    )

    return success(data=detail.model_dump(mode='json'))


# ---------- 2.3 获取活动群二维码 ----------

@router.get("/{activity_id}/qrcode")
async def get_activity_qrcode(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    part_result = await db.execute(
        select(Participation.id).where(
            Participation.user_id == current_user.id,
            Participation.activity_id == activity_id,
        )
    )
    is_participated = part_result.scalar_one_or_none() is not None
    is_owner = current_user.id == activity.owner_id

    if not is_participated and not is_owner:
        raise HTTPException(status_code=403, detail="无权查看该活动二维码")

    qr_result = await db.execute(
        select(ActivityQrcode.url).where(ActivityQrcode.activity_id == activity_id)
    )
    qrcode_url = qr_result.scalar_one_or_none()
    if qrcode_url is None:
        raise HTTPException(status_code=404, detail="该活动未上传群二维码")

    return success(data={"qrcode_url": qrcode_url})


# ---------- 2.5 编辑活动 ----------

@router.put("/{activity_id}")
async def update_activity(
    activity_id: int,
    body: UpdateActivityRequest,
    request: Request,
    current_user: User = Depends(get_current_active_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    if activity.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能编辑自己发布的活动")

    ignored_fields: list[str] = []

    original_status = activity.status

    if original_status in ("draft", "rejected"):
        # 全字段可改
        if body.title is not None:
            activity.title = body.title
        if body.activity_type is not None:
            activity.activity_type = body.activity_type
        if body.credit_type is not None:
            activity.credit_type = body.credit_type
        if body.credit_value is not None:
            activity.credit_value = body.credit_value
        if body.start_time is not None:
            activity.start_time = body.start_time
        if body.end_time is not None:
            activity.end_time = body.end_time
        if body.location is not None:
            activity.location = body.location
        if body.registration_deadline is not None:
            activity.registration_deadline = body.registration_deadline
        if body.max_participants is not None:
            activity.max_participants = body.max_participants
        if body.description is not None:
            activity.description = body.description

        # 追加图片
        if body.images:
            max_sort_result = await db.execute(
                select(func.max(ActivityImage.sort_order)).where(ActivityImage.activity_id == activity_id)
            )
            max_sort = max_sort_result.scalar() or -1
            for idx, filename in enumerate(body.images):
                max_sort += 1
                db.add(ActivityImage(
                    activity_id=activity_id,
                    url=f"{ACTIVITY_IMAGE_URL_PREFIX}/{filename}",
                    is_cover=False,
                    sort_order=max_sort,
                ))

        # 更新二维码
        if body.qrcode is not None:
            existing_qr = await db.execute(
                select(ActivityQrcode).where(ActivityQrcode.activity_id == activity_id)
            )
            qr = existing_qr.scalar_one_or_none()
            if qr is not None:
                qr.url = f"{QRCODE_URL_PREFIX}/{body.qrcode}"
            else:
                db.add(ActivityQrcode(
                    activity_id=activity_id,
                    url=f"{QRCODE_URL_PREFIX}/{body.qrcode}",
                ))

        # draft 直接上线；rejected 需重新审核
        if original_status == "rejected":
            activity.status = "pending"
            activity.reject_reason = None
        else:
            activity.status = "active"

    elif original_status == "active":
        # 报名中：仅部分字段可改
        if body.description is not None:
            activity.description = body.description
        if body.location is not None:
            activity.location = body.location
        if body.max_participants is not None:
            activity.max_participants = body.max_participants
        if body.end_time is not None:
            activity.end_time = body.end_time

        # 追加图片
        if body.images:
            max_sort_result = await db.execute(
                select(func.max(ActivityImage.sort_order)).where(ActivityImage.activity_id == activity_id)
            )
            max_sort = max_sort_result.scalar() or -1
            for idx, filename in enumerate(body.images):
                max_sort += 1
                db.add(ActivityImage(
                    activity_id=activity_id,
                    url=f"{ACTIVITY_IMAGE_URL_PREFIX}/{filename}",
                    is_cover=False,
                    sort_order=max_sort,
                ))

        # 更新二维码
        if body.qrcode is not None:
            existing_qr = await db.execute(
                select(ActivityQrcode).where(ActivityQrcode.activity_id == activity_id)
            )
            qr = existing_qr.scalar_one_or_none()
            if qr is not None:
                qr.url = f"{QRCODE_URL_PREFIX}/{body.qrcode}"
            else:
                db.add(ActivityQrcode(
                    activity_id=activity_id,
                    url=f"{QRCODE_URL_PREFIX}/{body.qrcode}",
                ))

        # 检查不可改字段是否被尝试修改
        field_values = {
            "title": body.title,
            "credit_type": body.credit_type,
            "credit_value": body.credit_value,
            "start_time": body.start_time,
            "registration_deadline": body.registration_deadline,
        }
        for field_name, value in field_values.items():
            if value is not None:
                ignored_fields.append(field_name)

    elif original_status == "ended":
        # 已结束：仅追加图片
        if body.images:
            max_sort_result = await db.execute(
                select(func.max(ActivityImage.sort_order)).where(ActivityImage.activity_id == activity_id)
            )
            max_sort = max_sort_result.scalar() or -1
            for idx, filename in enumerate(body.images):
                max_sort += 1
                db.add(ActivityImage(
                    activity_id=activity_id,
                    url=f"{ACTIVITY_IMAGE_URL_PREFIX}/{filename}",
                    is_cover=False,
                    sort_order=max_sort,
                ))

        # 报告其他字段被忽略
        all_other_fields = {
            "title": body.title,
            "activity_type": body.activity_type,
            "credit_type": body.credit_type,
            "credit_value": body.credit_value,
            "start_time": body.start_time,
            "end_time": body.end_time,
            "location": body.location,
            "registration_deadline": body.registration_deadline,
            "max_participants": body.max_participants,
            "description": body.description,
            "qrcode": body.qrcode,
        }
        for field_name, value in all_other_fields.items():
            if value is not None and field_name != "images":
                ignored_fields.append(field_name)

    else:
        raise HTTPException(status_code=403, detail="该活动状态不允许编辑")

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="update_activity",
        target_type="activity",
        target_id=activity.id,
        detail=f"编辑活动：{activity.title}（状态：{activity.status}）",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(activity)

    return success(
        data=UpdateActivityData(
            id=activity.id, status=activity.status, ignored_fields=ignored_fields
        ).model_dump(),
        message="更新成功",
    )


# ---------- 2.6 删除活动 ----------

@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    is_owner = current_user.id == activity.owner_id
    is_admin = current_user.role in ("admin", "super_admin")

    if is_owner and not is_admin:
        if activity.status in ("ended",):
            raise HTTPException(status_code=403, detail="该活动状态不允许删除，已结束活动请联系管理员")
    elif not is_admin:
        raise HTTPException(status_code=403, detail="无权删除该活动")

    # 收集物理文件路径（CASCADE 删除前先查出来）
    img_result = await db.execute(
        select(ActivityImage.url).where(ActivityImage.activity_id == activity_id)
    )
    image_urls = [r[0] for r in img_result.all()]

    qr_result = await db.execute(
        select(ActivityQrcode.url).where(ActivityQrcode.activity_id == activity_id)
    )
    qrcode_urls = [r[0] for r in qr_result.all()]

    # 清理物理文件（失败不影响数据库操作）
    file_result = delete_activity_files(image_urls, qrcode_urls)

    # 级联删除（应用层）
    # 1. credit_accumulation → DELETE
    participation_ids_result = await db.execute(
        select(Participation.id).where(Participation.activity_id == activity_id)
    )
    participation_ids = [r[0] for r in participation_ids_result.all()]

    if participation_ids:
        await db.execute(
            CreditAccumulation.__table__.delete()
            .where(CreditAccumulation.participation_id.in_(participation_ids))
        )

    # 2. 删除 participations
    await db.execute(
        Participation.__table__.delete().where(Participation.activity_id == activity_id)
    )

    # 3. 删除 favorites
    await db.execute(
        Favorite.__table__.delete().where(Favorite.activity_id == activity_id)
    )

    # 4. 删除 reviews
    await db.execute(
        Review.__table__.delete().where(Review.activity_id == activity_id)
    )

    # 5. 删除 activities（activity_images / activity_qrcodes 由数据库 CASCADE）
    await db.delete(activity)

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="delete_activity",
        target_type="activity",
        target_id=activity.id,
        detail=f"删除活动：{activity.title}（{file_result}）",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()

    return success(message="删除成功")
