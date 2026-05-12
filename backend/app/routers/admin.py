from datetime import datetime, timedelta, timezone, date

from pydantic import BaseModel, Field

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Query
from sqlalchemy import and_, case, func, select, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Activity, ActivityImage, ActivityOwner, ActivityQrcode, Announcement, Banner, College, CreditAccumulation, Favorite, Notification, OperationLog, Participation, Review, SchedulerState, Student, User
from app.schemas.admin import (
    AdminActivityItem,
    AdminBannerItem,
    BannerCreateRequest,
    BannerUpdateRequest,
    CollegeDistributionItem,
    ContactChangeItem,
    CreateAnnouncementRequest,
    CreateCollegeRequest,
    CreateUserRequest,
    CreateUserResponse,
    DashboardData,
    OperationLogItem,
    OwnerPendingItem,
    RejectActivityRequest,
    RejectOwnerRequest,
    ResetPasswordResponse,
    TrendItem,
    TypeDistributionItem,
    UpdateUserStatusRequest,
    UserListItem,
)
from app.schemas.common import PaginatedData, success
from app.utils.deps import require_admin, require_super_admin
from app.utils.notification_helper import create_notification
from app.utils.operation_log_helper import log_operation
from app.utils.security import hash_password, generate_random_password
from app.utils.file_helper import delete_activity_files
from app.utils.config_helper import DEFAULT_CONFIG, get_all_configs

router = APIRouter(prefix="/v1/admin", tags=["管理端"])


def escape_like(s: str) -> str:
    """转义 LIKE 特殊字符 % _ \\n"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.put("/activities/{activity_id}/reject")
async def reject_activity(
    activity_id: int,
    body: RejectActivityRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    activity.status = "rejected"
    activity.reject_reason = body.reason

    await create_notification(
        db=db,
        user_id=activity.owner_id,
        type="audit_result",
        title="审核结果",
        content=f"「{activity.title}」已被驳回：{body.reason}",
        link_type="activity",
        link_id=activity.id,
        action="edit_activity",
    )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="reject_activity",
        target_type="activity",
        target_id=activity.id,
        detail=f"驳回原因：{body.reason}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="驳回成功")


@router.put("/activities/{activity_id}/approve")
async def approve_activity(
    activity_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    if activity.status != "pending":
        raise HTTPException(status_code=400, detail="只能审核待审核状态的活动")

    activity.status = "active"
    activity.reject_reason = None

    await create_notification(
        db=db,
        user_id=activity.owner_id,
        type="audit_result",
        title="审核结果",
        content=f"「{activity.title}」已通过审核",
        link_type="activity",
        link_id=activity.id,
    )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="approve_activity",
        target_type="activity",
        target_id=activity.id,
        detail=None,
    )

    await db.commit()
    return success(message="审核通过")


@router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone(timedelta(hours=8)))
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=6)

    # 1. 基础计数
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    total_activities_result = await db.execute(select(func.count(Activity.id)))
    total_activities = total_activities_result.scalar() or 0

    # total_participations 实时 COUNT，保持与 total_users / total_activities 时效一致
    total_participations_result = await db.execute(
        select(func.count(Participation.id))
    )
    total_participations = total_participations_result.scalar() or 0

    pending_activities_result = await db.execute(
        select(func.count(Activity.id)).where(Activity.status == "pending")
    )
    pending_activities = pending_activities_result.scalar() or 0

    pending_owners_result = await db.execute(
        select(func.count(User.id)).where(
            User.role == "activity_owner", User.status == "pending"
        )
    )
    pending_owners = pending_owners_result.scalar() or 0

    today_new_result = await db.execute(
        select(func.count(Activity.id)).where(
            Activity.created_at >= today_start, Activity.status == "active"
        )
    )
    today_new = today_new_result.scalar() or 0

    # 2. 活动类型分布（从配置读取类型列表）
    configs = await get_all_configs(db)
    activity_type_list = configs.get("activity_types", DEFAULT_CONFIG["activity_types"])

    type_result = await db.execute(
        select(Activity.activity_type, func.count(Activity.id))
        .group_by(Activity.activity_type)
    )
    type_counts = {row[0]: row[1] for row in type_result.all()}
    type_distribution = []
    max_idx = 0
    max_count = -1
    for idx, act_type in enumerate(activity_type_list):
        count = type_counts.get(act_type, 0)
        if count >= max_count:
            max_count = count
            max_idx = idx
        percentage = round((count / total_activities * 100), 1) if total_activities > 0 else 0.0
        type_distribution.append(
            TypeDistributionItem(type=act_type, count=count, percentage=percentage)
        )

    # 加上已删除类型的统计
    config_type_set = set(activity_type_list)
    other_count = sum(c for t, c in type_counts.items() if t not in config_type_set)
    if other_count > 0:
        type_distribution.append(
            TypeDistributionItem(type="其他已删除类型", count=other_count, percentage=0.0)
        )
        # 重新计算 max_idx 和 percentages
        total_activities_with_other = total_activities
        for item in type_distribution:
            item.percentage = round((item.count / total_activities_with_other * 100), 1) if total_activities_with_other > 0 else 0.0

    # 百分比兜底
    if total_activities > 0 and type_distribution:
        current_sum = sum(item.percentage for item in type_distribution)
        diff = round(100.0 - current_sum, 1)
        if diff != 0.0:
            type_distribution[max_idx].percentage = round(
                type_distribution[max_idx].percentage + diff, 1
            )

    # 3. 各学院参与人数（左表 colleges，无学生也返回 count=0）
    college_result = await db.execute(
        select(College.name, func.count(User.id))
        .outerjoin(
            User,
            and_(User.college_id == College.id, User.role == "student"),
        )
        .group_by(College.id, College.name)
        .order_by(College.id)
    )
    college_distribution = [
        CollegeDistributionItem(college=row[0], count=row[1])
        for row in college_result.all()
    ]

    # 4. 近7天趋势（含今天）—— MariaDB 使用 func.date_format
    activity_date_result = await db.execute(
        select(
            func.date_format(Activity.created_at, "%Y-%m-%d").label("date"),
            func.count(Activity.id),
        )
        .where(Activity.created_at >= seven_days_ago)
        .group_by(func.date_format(Activity.created_at, "%Y-%m-%d"))
    )
    activity_by_date = {row[0]: row[1] for row in activity_date_result.all()}

    participation_date_result = await db.execute(
        select(
            func.date_format(Participation.registered_at, "%Y-%m-%d").label("date"),
            func.count(Participation.id),
        )
        .where(Participation.registered_at >= seven_days_ago)
        .group_by(func.date_format(Participation.registered_at, "%Y-%m-%d"))
    )
    participation_by_date = {row[0]: row[1] for row in participation_date_result.all()}

    trend = []
    for i in range(7):
        date = (today_start - timedelta(days=6 - i)).strftime("%Y-%m-%d")
        trend.append(
            TrendItem(
                date=date,
                new_activities=activity_by_date.get(date, 0),
                new_participations=participation_by_date.get(date, 0),
            )
        )

    data = DashboardData(
        total_users=total_users,
        total_activities=total_activities,
        total_participations=total_participations,
        pending_activities=pending_activities,
        pending_owners=pending_owners,
        today_new=today_new,
        type_distribution=type_distribution,
        college_distribution=college_distribution,
        trend=trend,
    )

    return success(data=data.model_dump(mode='json'))


# ---------- 学院管理接口 ----------


@router.get("/colleges")
async def list_colleges(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取学院列表，含学生人数和活动主体数"""
    result = await db.execute(
        select(
            College.id,
            College.name,
            func.sum(case((User.role == "student", 1), else_=0)).label("student_count"),
            func.sum(case((User.role == "activity_owner", 1), else_=0)).label("owner_count"),
        )
        .outerjoin(User, User.college_id == College.id)
        .group_by(College.id, College.name)
        .order_by(College.id)
    )
    colleges = [
        {
            "id": row.id,
            "name": row.name,
            "student_count": row.student_count or 0,
            "owner_count": row.owner_count or 0,
        }
        for row in result.all()
    ]
    return success(data=colleges)


@router.post("/colleges")
async def create_college(
    body: CreateCollegeRequest,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """新建学院"""
    existing = await db.execute(select(College).where(College.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该学院已存在")

    college = College(name=body.name)
    db.add(college)
    await db.commit()
    await db.refresh(college)
    return success(data={"id": college.id, "name": college.name}, message="学院已添加 ~")


@router.put("/colleges/{college_id}")
async def update_college(
    college_id: int,
    body: CreateCollegeRequest,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """编辑学院名称"""
    result = await db.execute(select(College).where(College.id == college_id))
    college = result.scalar_one_or_none()
    if college is None:
        raise HTTPException(status_code=404, detail="学院不存在")

    # 检查新名称是否与其他学院重复
    dup = await db.execute(
        select(College).where(College.name == body.name, College.id != college_id)
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该学院名称已存在")

    college.name = body.name
    await db.commit()
    return success(message="学院名称已更新 ~")


@router.delete("/colleges/{college_id}")
async def delete_college(
    college_id: int,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除学院（有用户时禁止删除）"""
    result = await db.execute(select(College).where(College.id == college_id))
    college = result.scalar_one_or_none()
    if college is None:
        raise HTTPException(status_code=404, detail="学院不存在")

    # 检查是否有学生归属
    s_result = await db.execute(
        select(func.count(User.id)).where(User.college_id == college_id, User.role == "student")
    )
    o_result = await db.execute(
        select(func.count(User.id)).where(User.college_id == college_id, User.role == "activity_owner")
    )
    s_count = s_result.scalar() or 0
    o_count = o_result.scalar() or 0
    if s_count > 0 or o_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该学院下有 {s_count} 名同学和 {o_count} 个活动主体，请先将他们转移到其他学院后再删除",
        )

    await db.delete(college)
    await db.commit()
    return success(message="学院已删除 ~")


class TransferUsersRequest(BaseModel):
    source_college_id: int = Field(..., gt=0)
    target_college_id: int = Field(..., gt=0)


@router.post("/colleges/transfer-users")
async def transfer_college_users(
    body: TransferUsersRequest,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """批量转移学院用户（事务保护）"""
    if body.source_college_id == body.target_college_id:
        raise HTTPException(status_code=400, detail="源学院和目标学院不能相同")

    # 获取学院名称
    src_result = await db.execute(select(College).where(College.id == body.source_college_id))
    src_college = src_result.scalar_one_or_none()
    if src_college is None:
        raise HTTPException(status_code=404, detail="源学院不存在")

    tgt_result = await db.execute(select(College).where(College.id == body.target_college_id))
    tgt_college = tgt_result.scalar_one_or_none()
    if tgt_college is None:
        raise HTTPException(status_code=404, detail="目标学院不存在")

    # 统计
    s_result = await db.execute(
        select(func.count(User.id)).where(
            User.college_id == body.source_college_id,
            User.role == "student",
        )
    )
    o_result = await db.execute(
        select(func.count(User.id)).where(
            User.college_id == body.source_college_id,
            User.role == "activity_owner",
        )
    )
    student_count = s_result.scalar() or 0
    owner_count = o_result.scalar() or 0

    # 批量更新（事务内）
    async with db.begin():
        await db.execute(
            User.__table__.update()
            .where(User.college_id == body.source_college_id)
            .values(college_id=body.target_college_id)
        )

    return success(
        data={
            "transferred_students": student_count,
            "transferred_owners": owner_count,
        },
        message=f"已将 {student_count} 名同学和 {owner_count} 个活动主体从「{src_college.name}」转移到「{tgt_college.name}」~",
    )


# ---------- 12.3 活动主体审核接口 ----------

@router.get("/owners/pending")
async def get_pending_owners(
    status: str | None = Query(None, pattern="^(pending|approved|rejected|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取待审核活动主体列表，支持 status 筛选"""
    query = (
        select(User, ActivityOwner, College)
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .outerjoin(College, User.college_id == College.id)
        .where(User.role == "activity_owner")
    )

    if status == "pending":
        query = query.where(User.status == "pending")
    elif status == "approved":
        query = query.where(User.status == "active")
    elif status == "rejected":
        query = query.where(User.status == "disabled")
    # "all" 或 None：不加状态筛选

    query = query.order_by(User.created_at.desc())

    count_query = (
        select(func.count(User.id))
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .where(User.role == "activity_owner")
    )
    if status == "pending":
        count_query = count_query.where(User.status == "pending")
    elif status == "approved":
        count_query = count_query.where(User.status == "active")
    elif status == "rejected":
        count_query = count_query.where(User.status == "disabled")

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = [
        OwnerPendingItem(
            id=user.id,
            account=user.account,
            owner_name=user.name,
            owner_type=owner.owner_type,
            avatar_url=user.avatar_url,
            college_name=college.name if college else None,
            contact_name=owner.contact_name,
            contact_student_id=owner.contact_student_id,
            contact_phone=owner.contact_phone,
            advisor_name=owner.advisor_name,
            advisor_contact=owner.advisor_contact,
            bio=owner.bio,
            status=user.status,
            reject_reason=None,  # 驳回原因可从通知等渠道扩展
            created_at=user.created_at.isoformat(),
        )
        for user, owner, college in rows
    ]

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


@router.put("/owners/{owner_id}/approve")
async def approve_owner(
    owner_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """通过活动主体审核"""
    result = await db.execute(
        select(User, ActivityOwner)
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .where(User.id == owner_id, User.role == "activity_owner")
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="活动主体不存在")

    user, owner = row

    if user.status != "pending":
        raise HTTPException(status_code=400, detail="该活动主体不是待审核状态")

    user.status = "active"

    await create_notification(
        db=db,
        user_id=user.id,
        type="audit_result",
        title="审核通过",
        content=f"「{user.name}」的账号审核已通过，现在可以发布活动了",
        link_type="profile",
        link_id=user.id,
    )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="approve_owner",
        target_type="user",
        target_id=user.id,
        detail=None,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="审核通过")


@router.put("/owners/{owner_id}/reject")
async def reject_owner(
    owner_id: int,
    body: RejectOwnerRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """驳回活动主体审核"""
    result = await db.execute(
        select(User, ActivityOwner)
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .where(User.id == owner_id, User.role == "activity_owner")
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="活动主体不存在")

    user, owner = row

    if user.status != "pending":
        raise HTTPException(status_code=400, detail="该活动主体不是待审核状态")

    user.status = "disabled"

    await create_notification(
        db=db,
        user_id=user.id,
        type="audit_result",
        title="审核未通过",
        content=f"「{user.name}」的账号审核未通过，原因：{body.reason}",
        link_type="profile",
        link_id=user.id,
        action="edit_profile",
    )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="reject_owner",
        target_type="user",
        target_id=user.id,
        detail=f"驳回原因：{body.reason}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="审核已驳回")


# ---------- 12.4 负责人变更审核接口 ----------

@router.get("/owners/contact-changes")
async def get_pending_contact_changes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取待审核负责人变更列表（扁平化结构）"""
    query = (
        select(User, ActivityOwner)
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .where(ActivityOwner.pending_contact.isnot(None))
        .order_by(User.created_at.desc())
    )

    count_result = await db.execute(
        select(func.count(ActivityOwner.user_id)).where(
            ActivityOwner.pending_contact.isnot(None)
        )
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for user, owner in rows:
        pc = owner.pending_contact
        if not isinstance(pc, dict):
            continue

        pending = pc.get("new", {})
        if not pending:
            continue

        items.append(
            ContactChangeItem(
                id=user.id,
                owner_name=user.name,
                old_contact_name=owner.contact_name,
                old_contact_student_id=owner.contact_student_id,
                old_contact_phone=owner.contact_phone,
                new_contact_name=pending.get("contact_name", ""),
                new_contact_student_id=pending.get("contact_student_id", ""),
                new_contact_phone=pending.get("contact_phone", ""),
                submitted_at=pc.get("timestamp", owner.updated_at).isoformat() if hasattr(pc.get("timestamp", owner.updated_at), 'isoformat') else str(pc.get("timestamp", owner.updated_at)),
                status="pending",
            )
        )

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


@router.put("/owners/{owner_id}/approve-contact-change")
async def approve_contact_change(
    owner_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """通过负责人变更申请"""
    result = await db.execute(
        select(User, ActivityOwner)
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .where(User.id == owner_id, User.role == "activity_owner", ActivityOwner.pending_contact.isnot(None))
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="待审核的负责人变更不存在")

    user, owner = row

    pc = owner.pending_contact
    if not isinstance(pc, dict) or "new" not in pc:
        raise HTTPException(status_code=400, detail="待审核的变更信息格式错误")

    new_info = pc.get("new", {})

    old_name = owner.contact_name
    owner.contact_name = new_info.get("contact_name", owner.contact_name)
    owner.contact_student_id = new_info.get("contact_student_id", owner.contact_student_id)
    owner.contact_phone = new_info.get("contact_phone", owner.contact_phone)

    owner.pending_contact = None

    await create_notification(
        db=db,
        user_id=user.id,
        type="audit_result",
        title="负责人变更通过",
        content=f"「{user.name}」的负责人信息已由 {old_name} 变更为 {owner.contact_name}",
        link_type="profile",
        link_id=user.id,
    )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="approve_contact_change",
        target_type="user",
        target_id=user.id,
        detail=f"新负责人：{owner.contact_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="负责人变更已通过")


@router.put("/owners/{owner_id}/reject-contact-change")
async def reject_contact_change(
    owner_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """驳回负责人变更申请"""
    result = await db.execute(
        select(User, ActivityOwner)
        .join(ActivityOwner, User.id == ActivityOwner.user_id)
        .where(User.id == owner_id, User.role == "activity_owner", ActivityOwner.pending_contact.isnot(None))
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="待审核的负责人变更不存在")

    user, owner = row

    pc = owner.pending_contact or {}
    new_name = pc.get("new", {}).get("contact_name", "") if isinstance(pc, dict) else ""

    owner.pending_contact = None

    await create_notification(
        db=db,
        user_id=user.id,
        type="audit_result",
        title="负责人变更未通过",
        content=f"「{user.name}」提交的负责人信息变更申请（申请人：{new_name}）未通过审核",
        link_type="profile",
        link_id=user.id,
        action="edit_profile",
    )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="reject_contact_change",
        target_type="user",
        target_id=user.id,
        detail=f"驳回的申请人：{new_name}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="负责人变更已驳回")


# ---------- 12.6 用户管理接口 ----------

@router.get("/users")
async def get_users(
    role: str | None = Query(None, pattern="^(student|activity_owner|admin|super_admin)$"),
    status: str | None = Query(None, pattern="^(active|disabled|pending)$"),
    search: str | None = Query(None, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（支持角色、状态、搜索筛选）"""
    query = select(User, College).outerjoin(College, User.college_id == College.id)

    if role:
        query = query.where(User.role == role)

    if status:
        query = query.where(User.status == status)

    if search:
        escaped = escape_like(search)
        query = query.where(
            or_(
                User.account.ilike(f"%{escaped}%", escape="\\"),
                User.name.ilike(f"%{escaped}%", escape="\\"),
            )
        )

    count_query = query.with_only_columns(func.count(User.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = [
        UserListItem(
            user_id=user.id,
            account=user.account,
            name=user.name,
            role=user.role,
            status=user.status,
            avatar_url=user.avatar_url,
            college_name=college.name if college else None,
            college_id=user.college_id,
            created_at=user.created_at,
        )
        for user, college in rows
    ]

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


@router.post("/users")
async def create_user(
    body: CreateUserRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建用户账号（管理员及以上可用，非 super_admin 只能创建非管理员角色）"""
    if body.role in ("admin", "super_admin") and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限才能创建管理员账号")

    existing = await db.execute(select(User).where(User.account == body.account))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="账号已存在")

    initial_password = generate_random_password(8)

    new_user = User(
        account=body.account,
        password_hash=hash_password(initial_password),
        role=body.role,
        name=body.name,
        status="active",
        need_change_pwd=True,
    )
    db.add(new_user)
    await db.flush()

    if body.role == "student":
        student = Student(
            user_id=new_user.id,
            student_id=body.account,
            name=body.name,
        )
        db.add(student)

    await db.flush()

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="create_user",
        target_type="user",
        target_id=new_user.id,
        detail=f"初始密码: ******, 角色: {body.role}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()

    return success(data=CreateUserResponse(
        user_id=new_user.id,
        account=new_user.account,
        name=new_user.name,
        initial_password=initial_password,
    ).model_dump(), message="创建成功")


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    body: UpdateUserStatusRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户状态（禁用/启用）"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_status = user.status

    if user.role in ("admin", "super_admin") and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="只有 Super 管理员可以操作其他管理员账号")

    user.status = body.status

    if body.status == "disabled":
        await create_notification(
            db=db,
            user_id=user.id,
            type="system",
            title="账号状态变更",
            content="您的账号已被管理员禁用，如有疑问请联系系统管理员",
        )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="update_user_status",
        target_type="user",
        target_id=user.id,
        detail=f"状态从 {old_status} 变更为 {body.status}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()

    status_text = "已禁用" if body.status == "disabled" else "已启用"
    return success(message=status_text)


@router.put("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """重置用户密码"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.role in ("admin", "super_admin") and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="只有 Super 管理员可以操作其他管理员账号")

    new_password = generate_random_password(8)
    user.password_hash = hash_password(new_password)
    user.need_change_pwd = True

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="reset_password",
        target_type="user",
        target_id=user.id,
        detail=None,
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()

    return success(data=ResetPasswordResponse(new_password=new_password).model_dump(), message="重置成功")


# ---------- 12.5 活动管理接口 ----------

@router.get("/activities/pending")
async def get_pending_activities(
    status: str | None = Query(None, pattern="^(pending|active|ended|rejected|draft)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """待审/活动审核列表"""
    cover_subq = (
        select(ActivityImage.url)
        .where(ActivityImage.activity_id == Activity.id, ActivityImage.is_cover == True)
        .order_by(ActivityImage.sort_order)
        .limit(1)
        .correlate(Activity)
        .scalar_subquery()
    )

    query = (
        select(Activity, User.name.label("owner_name"), cover_subq.label("cover_image_url"))
        .join(Activity.owner)
    )

    if status:
        query = query.where(Activity.status == status)

    count_query = select(func.count(Activity.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.order_by(Activity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = [
        AdminActivityItem(
            id=act.id,
            title=act.title,
            owner_name=owner_name,
            activity_type=act.activity_type,
            credit_type=act.credit_type,
            status=act.status,
            cover_image_url=cover_url,
            start_time=act.start_time,
            end_time=act.end_time,
            location=act.location,
            credit_value=float(act.credit_value) if act.credit_value is not None else None,
            max_participants=act.max_participants,
            description=act.description,
            reject_reason=act.reject_reason,
            registration_deadline=act.registration_deadline,
            participant_count=act.participant_count,
            created_at=act.created_at,
        )
        for act, owner_name, cover_url in rows
    ]

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


@router.get("/activities")
async def get_admin_activities(
    keyword: str | None = Query(None, max_length=100),
    status: str | None = Query(None, pattern="^(draft|pending|active|ended|rejected)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """全量活动搜索"""
    cover_subq = (
        select(ActivityImage.url)
        .where(ActivityImage.activity_id == Activity.id, ActivityImage.is_cover == True)
        .order_by(ActivityImage.sort_order)
        .limit(1)
        .correlate(Activity)
        .scalar_subquery()
    )

    query = (
        select(Activity, User.name.label("owner_name"), cover_subq.label("cover_image_url"))
        .join(Activity.owner)
    )

    if keyword:
        escaped = escape_like(keyword)
        query = query.where(
            or_(
                Activity.title.ilike(f"%{escaped}%", escape="\\"),
                User.name.ilike(f"%{escaped}%", escape="\\"),
            )
        )

    if status:
        query = query.where(Activity.status == status)

    count_query = select(func.count(Activity.id)).join(Activity.owner)
    if keyword:
        escaped = escape_like(keyword)
        count_query = count_query.where(
            or_(
                Activity.title.ilike(f"%{escaped}%", escape="\\"),
                User.name.ilike(f"%{escaped}%", escape="\\"),
            )
        )
    if status:
        count_query = count_query.where(Activity.status == status)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.order_by(Activity.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    items = [
        AdminActivityItem(
            id=act.id,
            title=act.title,
            owner_name=owner_name,
            activity_type=act.activity_type,
            credit_type=act.credit_type,
            status=act.status,
            cover_image_url=cover_url,
            start_time=act.start_time,
            end_time=act.end_time,
            location=act.location,
            credit_value=float(act.credit_value) if act.credit_value is not None else None,
            max_participants=act.max_participants,
            description=act.description,
            reject_reason=act.reject_reason,
            registration_deadline=act.registration_deadline,
            participant_count=act.participant_count,
            created_at=act.created_at,
        )
        for act, owner_name, cover_url in rows
    ]

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


@router.delete("/activities/{activity_id}")
async def admin_delete_activity(
    activity_id: int,
    body: RejectActivityRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """强制删除活动（管理员兜底，任何状态均可删除）"""
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    activity = result.scalar_one_or_none()
    if activity is None:
        raise HTTPException(status_code=404, detail="活动不存在")

    activity_title = activity.title
    credit_info = f"（{activity.credit_type} {activity.credit_value or '-'}分）" if activity.credit_type else ""

    # 收集物理文件路径（CASCADE 删除前先查出来）
    img_result = await db.execute(
        select(ActivityImage.url).where(ActivityImage.activity_id == activity_id)
    )
    image_urls = [r[0] for r in img_result.all()]

    qr_result = await db.execute(
        select(ActivityQrcode.url).where(ActivityQrcode.activity_id == activity_id)
    )
    qrcode_urls = [r[0] for r in qr_result.all()]

    # 收集通知对象：参与者 + 活动主体
    part_users_result = await db.execute(
        select(Participation.user_id).where(Participation.activity_id == activity_id)
    )
    participant_ids = [r[0] for r in part_users_result.all()]

    owner_id = activity.owner_id

    # 清理物理文件（失败不影响数据库操作）
    file_result = delete_activity_files(image_urls, qrcode_urls)

    # 级联删除顺序（应用层处理）：
    # 1. credit_accumulation → DELETE
    await db.execute(
        CreditAccumulation.__table__.delete().where(
            CreditAccumulation.participation_id.in_(
                select(Participation.id).where(Participation.activity_id == activity_id)
            )
        )
    )

    # 2. participations → DELETE
    await db.execute(
        Participation.__table__.delete().where(Participation.activity_id == activity_id)
    )

    # 3. favorites → DELETE
    await db.execute(
        Favorite.__table__.delete().where(Favorite.activity_id == activity_id)
    )

    # 4. reviews → DELETE
    await db.execute(
        Review.__table__.delete().where(Review.activity_id == activity_id)
    )

    # 5. activities → DELETE（activity_images 和 activity_qrcodes 由数据库 CASCADE 自动删除）
    await db.execute(Activity.__table__.delete().where(Activity.id == activity_id))

    # 6. 系统通知
    notify_content = f"您参与的活动「{activity_title}」{credit_info}已被管理员删除。原因：{body.reason}"
    for uid in participant_ids:
        await create_notification(
            db=db,
            user_id=uid,
            type="system",
            title="活动已删除",
            content=notify_content,
        )
    if owner_id not in participant_ids:
        await create_notification(
            db=db,
            user_id=owner_id,
            type="system",
            title="活动已删除",
            content=notify_content,
        )

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="delete_activity",
        target_type="activity",
        target_id=activity_id,
        detail=f"管理员强制删除活动「{activity_title}」，原因：{body.reason}（{file_result}）",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()

    return success(message="活动已删除")


# ---------- 12.7 操作日志接口 ----------

@router.get("/logs")
async def get_operation_logs(
    user_id: int | None = Query(None),
    operation: str | None = Query(None, max_length=50),
    operator_name: str | None = Query(None, max_length=50),
    start_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """操作日志列表"""
    query = select(OperationLog).options(joinedload(OperationLog.user))

    if user_id:
        query = query.where(OperationLog.user_id == user_id)

    if operation:
        query = query.where(OperationLog.operation == operation)

    if operator_name:
        escaped = escape_like(operator_name)
        query = query.join(User, OperationLog.user_id == User.id, isouter=True).where(
            User.name.ilike(f"%{escaped}%", escape="\\")
        )

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        query = query.where(OperationLog.created_at >= start_dt)

    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.where(OperationLog.created_at <= end_dt)

    count_query = query.with_only_columns(func.count(OperationLog.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    query = query.order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        OperationLogItem(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.name if log.user else None,
            operation=log.operation,
            target_type=log.target_type,
            target_id=log.target_id,
            detail=log.detail,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


# ---------- 12.8 公告管理接口 ----------

@router.get("/announcements")
async def list_announcements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """公告列表"""
    count_result = await db.execute(select(func.count(Announcement.id)))
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Announcement)
        .order_by(Announcement.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    announcements = result.scalars().all()

    items = [
        {
            "id": a.id,
            "content": a.content,
            "created_at": a.created_at,
        }
        for a in announcements
    ]

    return success(data=PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    ).model_dump(mode='json'))


@router.post("/announcements")
async def create_announcement(
    body: CreateAnnouncementRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """发布公告"""
    # 1. 插入公告记录
    announcement = Announcement(
        content=body.content,
        publisher_id=current_user.id,
    )
    db.add(announcement)
    await db.flush()

    # 2. 查询所有 active 用户
    users_result = await db.execute(
        select(User.id).where(User.status == "active")
    )
    user_ids = [row[0] for row in users_result.all()]

    # 3. 分批推送通知（每批 500 条）
    batch_size = 500
    for i in range(0, len(user_ids), batch_size):
        batch_ids = user_ids[i:i + batch_size]
        notifications = [
            Notification(
                user_id=uid,
                type="announcement",
                title="系统公告",
                content=body.content,
            )
            for uid in batch_ids
        ]
        db.add_all(notifications)
        await db.flush()

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="create_announcement",
        target_type="announcement",
        target_id=announcement.id,
        detail="发布系统公告",
    )

    await db.commit()
    return success(message="公告已发布")


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除公告"""
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise HTTPException(status_code=404, detail="公告不存在")

    await db.execute(Announcement.__table__.delete().where(Announcement.id == announcement_id))
    await db.commit()

    return success(message="公告已删除")


# ---------- 12.9 轮播图管理接口 ----------

@router.get("/banners")
async def list_banners(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """轮播图列表（含未激活）"""
    result = await db.execute(
        select(Banner).order_by(Banner.sort_order)
    )
    banners = result.scalars().all()
    items = [
        AdminBannerItem(
            id=b.id,
            title=b.title,
            subtitle=b.subtitle,
            image_url=b.image_url,
            sort_order=b.sort_order,
            is_active=b.is_active,
            created_at=b.created_at.isoformat(),
        ).model_dump()
        for b in banners
    ]
    return success(data=items)


@router.post("/banners")
async def create_banner(
    body: BannerCreateRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """新增轮播图"""
    banner = Banner(
        title=body.title,
        subtitle=body.subtitle,
        image_url=body.image_url,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )
    db.add(banner)

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="create_banner",
        target_type="banner",
        target_id=banner.id,
        detail=f"标题：{body.title}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="创建成功")


@router.put("/banners/{banner_id}")
async def update_banner(
    banner_id: int,
    body: BannerUpdateRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """编辑轮播图"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if banner is None:
        raise HTTPException(status_code=404, detail="轮播图不存在")

    if body.title is not None:
        banner.title = body.title
    if body.subtitle is not None:
        banner.subtitle = body.subtitle
    if body.image_url is not None:
        banner.image_url = body.image_url
    if body.sort_order is not None:
        banner.sort_order = body.sort_order
    if body.is_active is not None:
        banner.is_active = body.is_active

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="update_banner",
        target_type="banner",
        target_id=banner.id,
        detail=f"标题：{banner.title}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="更新成功")


@router.delete("/banners/{banner_id}")
async def delete_banner(
    banner_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除轮播图"""
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if banner is None:
        raise HTTPException(status_code=404, detail="轮播图不存在")

    await db.execute(Banner.__table__.delete().where(Banner.id == banner_id))

    await log_operation(
        db=db,
        user_id=current_user.id,
        operation="delete_banner",
        target_type="banner",
        target_id=banner_id,
        detail=f"标题：{banner.title}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return success(message="删除成功")
