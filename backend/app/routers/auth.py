from datetime import datetime, timedelta, timezone
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.models import ActivityOwner, College, Student, User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForceChangePasswordRequest,
    LoginData,
    LoginRequest,
    LoginUser,
    OwnerRegisterRequest,
    StudentRegisterData,
    StudentRegisterRequest,
)
from app.schemas.common import success
from app.utils.deps import get_current_user
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/v1/auth", tags=["认证"])

# 简易内存速率限制：同一 IP 60 秒内失败 5 次后返回 429
_login_fails: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_SECONDS = 60
_RATE_LIMIT_MAX_FAILS = 5


def _check_login_rate(client_ip: str):
    now = time()
    fails = _login_fails[client_ip]
    # 清理过期记录
    _login_fails[client_ip] = [t for t in fails if now - t < _RATE_LIMIT_SECONDS]
    if len(_login_fails[client_ip]) >= _RATE_LIMIT_MAX_FAILS:
        raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")


# ---------- 1.1 学生注册 ----------

@router.post("/register/student")
async def register_student(body: StudentRegisterRequest, db: AsyncSession = Depends(get_db)):
    # 学号唯一性
    existing = await db.execute(select(Student).where(Student.student_id == body.student_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该学号已注册")

    # account 唯一性
    existing = await db.execute(select(User).where(User.account == body.student_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该学号已注册")

    # college_id 存在性
    college = await db.execute(select(College).where(College.id == body.college_id))
    if college.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail="学院不存在")

    user = User(
        account=body.student_id,
        password_hash=hash_password(body.password),
        role="student",
        name=body.name,
        college_id=body.college_id,
        status="active",
        need_change_pwd=False,
    )
    db.add(user)
    await db.flush()

    student = Student(
        user_id=user.id,
        student_id=body.student_id,
        name=body.name,
        phone=body.phone,
        email=body.email,
    )
    db.add(student)
    await db.commit()

    return success(
        data=StudentRegisterData(student_id=body.student_id, name=body.name).model_dump(),
        message="注册成功",
    )


# ---------- 1.2 活动主体注册 ----------

@router.post("/register/owner")
async def register_owner(body: OwnerRegisterRequest, db: AsyncSession = Depends(get_db)):
    # account 唯一性
    existing = await db.execute(select(User).where(User.account == body.account))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该账号已注册")

    # college_id 校验：0 代表校级，否则必须存在
    if body.college_id != 0:
        college = await db.execute(select(College).where(College.id == body.college_id))
        if college.scalar_one_or_none() is None:
            raise HTTPException(status_code=400, detail="学院不存在")

    user = User(
        account=body.account,
        password_hash=hash_password(body.password),
        role="activity_owner",
        name=body.owner_name,
        college_id=body.college_id if body.college_id != 0 else None,
        status="pending",
        need_change_pwd=False,
    )
    db.add(user)
    await db.flush()

    owner = ActivityOwner(
        user_id=user.id,
        owner_type=body.owner_type,
        bio=body.bio,
        contact_name=body.contact_name,
        contact_student_id=body.contact_student_id,
        contact_phone=body.contact_phone,
        advisor_name=body.advisor_name,
        advisor_contact=body.advisor_contact,
    )
    db.add(owner)
    await db.commit()

    return success(message="提交成功，请等待管理员审核")


# ---------- 1.3 登录 ----------

@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    _check_login_rate(client_ip)

    result = await db.execute(
        select(User).where(User.account == body.account)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        _login_fails[client_ip].append(time())
        raise HTTPException(status_code=401, detail="账号或密码错误")

    # 活动主体 pending 状态不能登录
    if user.status == "pending":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号正在审核中")

    # disabled 状态
    if user.status == "disabled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    # 查 college_name
    college_name = None
    if user.college_id is not None:
        college_result = await db.execute(select(College).where(College.id == user.college_id))
        college = college_result.scalar_one_or_none()
        if college:
            college_name = college.name

    # 活动主体 college_id=0 时显示"校级"
    if user.role == "activity_owner" and user.college_id is None:
        college_name = "校级"

    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=expires_delta,
        token_version=user.token_version,
    )

    login_user = LoginUser(
        user_id=user.id,
        account=user.account,
        role=user.role,
        name=user.name,
        avatar_url=user.avatar_url,
        college_id=user.college_id if user.college_id is not None else 0,
        college_name=college_name,
        need_change_password=user.need_change_pwd,
        status=user.status,
    )

    response = JSONResponse(
        content=success(
            data=LoginData(
                access_token=access_token,
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=login_user,
            ).model_dump(),
            message="登录成功",
        ),
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1800,
        path="/",
    )
    return response


# ---------- 1.4 修改密码 ----------

@router.put("/password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    if body.old_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    current_user.password_hash = hash_password(body.new_password)
    current_user.token_version += 1
    await db.commit()

    return success(message="密码修改成功")


# ---------- 1.6 退出登录 ----------

@router.post("/logout")
async def logout():
    response = JSONResponse(content={"code": 200, "message": "已退出登录"})
    response.delete_cookie("access_token", path="/")
    return response


# ---------- 1.5 首次登录强制改密 ----------

@router.put("/force-change-password")
async def force_change_password(
    body: ForceChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.need_change_pwd:
        raise HTTPException(status_code=400, detail="无需强制改密")

    current_user.password_hash = hash_password(body.new_password)
    current_user.need_change_pwd = False
    current_user.token_version += 1
    await db.commit()

    return success(message="密码设置成功，请重新登录")
