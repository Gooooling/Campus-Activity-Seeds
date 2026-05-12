from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import ActivityOwner, College, Student, User
from app.schemas.common import success
from app.schemas.users import (
    AdvisorUpdate,
    ContactInfo,
    ContactUpdate,
    OwnerProfile,
    PendingContact,
    StudentProfile,
)
from app.utils.deps import get_current_user, get_current_active_owner
from app.utils.operation_log_helper import log_operation

router = APIRouter(prefix="/v1/users", tags=["用户"])


# ---------- 学院列表 ----------

@router.get("/colleges")
async def list_colleges(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(College).order_by(College.id))
    colleges = result.scalars().all()
    items = [{"id": c.id, "name": c.name} for c in colleges]
    items.append({"id": 0, "name": "校级"})
    return success(data=items)


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 查 college_name
    college_name = None
    if current_user.college_id is not None:
        result = await db.execute(select(College).where(College.id == current_user.college_id))
        college = result.scalar_one_or_none()
        if college:
            college_name = college.name
    if current_user.role == "activity_owner" and current_user.college_id is None:
        college_name = "校级"

    if current_user.role == "student":
        result = await db.execute(select(Student).where(Student.user_id == current_user.id))
        student = result.scalar_one_or_none()
        return success(data=StudentProfile(
            user_id=current_user.id,
            account=current_user.account,
            role=current_user.role,
            name=current_user.name,
            avatar_url=current_user.avatar_url,
            college_id=current_user.college_id if current_user.college_id is not None else 0,
            college_name=college_name,
            phone=student.phone if student else None,
            email=student.email if student else None,
            status=current_user.status,
        ).model_dump(mode='json'))

    # activity_owner
    result = await db.execute(select(ActivityOwner).where(ActivityOwner.user_id == current_user.id))
    owner = result.scalar_one_or_none()
    return success(data=OwnerProfile(
        user_id=current_user.id,
        account=current_user.account,
        role=current_user.role,
        owner_name=current_user.name,
        owner_type=owner.owner_type if owner else "",
        avatar_url=current_user.avatar_url,
        college_id=current_user.college_id if current_user.college_id is not None else 0,
        college_name=college_name,
        bio=owner.bio if owner else None,
        contact_name=owner.contact_name if owner else "",
        contact_student_id=owner.contact_student_id if owner else "",
        contact_phone=owner.contact_phone if owner else "",
        advisor_name=owner.advisor_name if owner else None,
        advisor_contact=owner.advisor_contact if owner else None,
        status=current_user.status,
    ).model_dump(mode='json'))


@router.put("/me")
async def update_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    body: dict = Body(...),
):
    if current_user.role == "student":
        if "name" in body and body["name"] is not None:
            current_user.name = body["name"]
            result = await db.execute(select(Student).where(Student.user_id == current_user.id))
            student = result.scalar_one_or_none()
            if student:
                student.name = body["name"]
        if "college_id" in body and body["college_id"] is not None:
            college_id = None if body["college_id"] == 0 else body["college_id"]
            if college_id is not None:
                college = await db.execute(select(College).where(College.id == college_id))
                if college.scalar_one_or_none() is None:
                    raise HTTPException(status_code=400, detail="学院不存在")
            current_user.college_id = college_id
        if "phone" in body and body["phone"] is not None:
            result = await db.execute(select(Student).where(Student.user_id == current_user.id))
            student = result.scalar_one_or_none()
            if student:
                student.phone = body["phone"]
        if "email" in body and body["email"] is not None:
            result = await db.execute(select(Student).where(Student.user_id == current_user.id))
            student = result.scalar_one_or_none()
            if student:
                student.email = body["email"]
        if "avatar_url" in body:
            current_user.avatar_url = body["avatar_url"]

    elif current_user.role == "activity_owner":
        if "owner_name" in body and body["owner_name"] is not None:
            current_user.name = body["owner_name"]
        if "owner_type" in body and body["owner_type"] is not None:
            result = await db.execute(select(ActivityOwner).where(ActivityOwner.user_id == current_user.id))
            owner = result.scalar_one_or_none()
            if owner:
                owner.owner_type = body["owner_type"]
        if "college_id" in body and body["college_id"] is not None:
            college_id = None if body["college_id"] == 0 else body["college_id"]
            if college_id is not None:
                college = await db.execute(select(College).where(College.id == college_id))
                if college.scalar_one_or_none() is None:
                    raise HTTPException(status_code=400, detail="学院不存在")
            current_user.college_id = college_id
        if "bio" in body:
            result = await db.execute(select(ActivityOwner).where(ActivityOwner.user_id == current_user.id))
            owner = result.scalar_one_or_none()
            if owner:
                owner.bio = body["bio"]
        if "avatar_url" in body:
            current_user.avatar_url = body["avatar_url"]

    # 记录操作日志（活动主体修改资料）
    if current_user.role == "activity_owner":
        changed_fields = [k for k in ("owner_name", "owner_type", "college_id", "bio", "avatar_url") if k in body]
        if changed_fields:
            await log_operation(
                db=db,
                user_id=current_user.id,
                operation="update_profile",
                target_type="user",
                target_id=current_user.id,
                detail=f"修改资料：{', '.join(changed_fields)}",
            )

    await db.commit()
    return success(message="保存成功")


@router.get("/me/contact")
async def get_contact(
    current_user: User = Depends(get_current_active_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ActivityOwner).where(ActivityOwner.user_id == current_user.id))
    owner = result.scalar_one_or_none()

    pending = None
    if owner and owner.pending_contact:
        pending = PendingContact(
            old=owner.pending_contact.get("old", {}),
            new=owner.pending_contact.get("new", {})
        )

    return success(data=ContactInfo(
        contact_name=owner.contact_name if owner else "",
        contact_student_id=owner.contact_student_id if owner else "",
        contact_phone=owner.contact_phone if owner else "",
        pending_change=pending,
    ).model_dump(mode='json'))


@router.put("/me/contact")
async def update_contact(
    body: ContactUpdate,
    current_user: User = Depends(get_current_active_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ActivityOwner).where(ActivityOwner.user_id == current_user.id))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="活动主体信息不存在")

    owner.pending_contact = {
        "old": {
            "contact_name": owner.contact_name,
            "contact_student_id": owner.contact_student_id,
            "contact_phone": owner.contact_phone,
        },
        "new": {
            "contact_name": body.contact_name,
            "contact_student_id": body.contact_student_id,
            "contact_phone": body.contact_phone,
        }
    }
    await db.commit()
    return success(message="负责人信息已提交审核，当前信息保持不变")


@router.put("/me/advisor")
async def update_advisor(
    body: AdvisorUpdate,
    current_user: User = Depends(get_current_active_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ActivityOwner).where(ActivityOwner.user_id == current_user.id))
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="活动主体信息不存在")

    owner.advisor_name = body.advisor_name
    owner.advisor_contact = body.advisor_contact
    await db.commit()
    return success(message="保存成功")
