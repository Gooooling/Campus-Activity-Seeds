from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import User
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)
oauth2_scheme_strict = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


async def _extract_token(request: Request) -> str | None:
    """优先从 Cookie 读取 access_token，读不到再从 Authorization header 兜底。"""
    token = request.cookies.get("access_token")
    if token:
        return token
    # 兜底：从 Authorization header 获取（保持 Swagger 兼容）
    from fastapi.security.utils import get_authorization_scheme_param
    auth = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(auth)
    if scheme.lower() == "bearer" and param:
        return param
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = await _extract_token(request)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据")

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证凭据")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    # Token invalidation: token_version must match
    token_version = payload.get("token_version")
    if token_version is None or token_version != user.token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭据已失效，请重新登录")

    if user.status == "disabled":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    return user


def require_role(*roles: str):
    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限执行此操作")
        return current_user
    return check_role


async def get_current_active_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "activity_owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅活动主体可执行此操作")
    if current_user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号尚未通过审核")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")
    return current_user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = await _extract_token(request)
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or user.status == "disabled":
        return None
    # Token invalidation: token_version must match
    token_version = payload.get("token_version")
    if token_version is None or token_version != user.token_version:
        return None
    return user
