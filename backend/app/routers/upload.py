from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import ActivityQrcode, Activity, Participation, User
from app.schemas.common import success
from app.utils.deps import get_current_user, get_current_user_optional
from app.utils.file_helper import validate_file_content, validate_file_size, save_uploaded_file

router = APIRouter(prefix="/v1", tags=["文件"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    type: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    if type not in ("activity_image", "qrcode", "avatar"):
        raise HTTPException(status_code=400, detail="无效的 type")

    validate_file_size(file)
    validate_file_content(file)

    relative_path = save_uploaded_file(file, type)
    url = f"/uploads/{relative_path}"

    return success(data={"filename": relative_path.split("/")[-1], "url": url})


@router.get("/files/{file_path:path}")
async def serve_file(
    file_path: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    # 1. 路径安全校验：禁止 ../
    if ".." in file_path:
        raise HTTPException(status_code=400, detail="无效的路径")

    # 统一去掉前导斜杠，避免 "/activities/" 和 "activities/" 判断混乱
    file_path = file_path.lstrip("/")

    full_path = Path(file_path)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 2. 权限校验（file_path 此时无前导斜杠）
    if "activities/" in file_path or "avatars/" in file_path:
        # 公开访问（首页、活动卡片等需要未登录也能看）
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        ext = full_path.suffix.lower()
        media_type = mime_map.get(ext, "application/octet-stream")
        return FileResponse(full_path, media_type=media_type)

    if "qrcodes/" in file_path:
        # 未登录不能查看二维码
        if current_user is None:
            raise HTTPException(status_code=401, detail="请先登录")

        # 反查 activity_id（DB 中 url 以 /uploads/ 开头）
        result = await db.execute(
            select(ActivityQrcode)
            .options(selectinload(ActivityQrcode.activity))
            .where(ActivityQrcode.url == f"/{file_path}")
        )
        qrcode = result.scalar_one_or_none()
        if qrcode is None:
            raise HTTPException(status_code=404, detail="文件不存在")

        activity_id = qrcode.activity_id

        # 校验权限：发布者或已参与学生
        if current_user.id == qrcode.activity.owner_id:
            pass  # 是发布者
        else:
            # 查 participations
            result = await db.execute(
                select(Participation).where(
                    Participation.user_id == current_user.id,
                    Participation.activity_id == activity_id
                )
            )
            participation = result.scalar_one_or_none()
            if participation is None:
                raise HTTPException(status_code=403, detail="无权限访问此文件")

        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".webp": "image/webp", ".bmp": "image/bmp",
        }
        ext = full_path.suffix.lower()
        media_type = mime_map.get(ext, "application/octet-stream")
        return FileResponse(full_path, media_type=media_type)

    raise HTTPException(status_code=400, detail="无效的文件路径")
