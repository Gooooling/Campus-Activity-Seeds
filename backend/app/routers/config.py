from fastapi import APIRouter

from app.config import settings
from app.schemas.common import success

router = APIRouter(prefix="/v1/config", tags=["配置"])


@router.get("/public")
async def get_public_config():
    """供前端读取的公开配置"""
    return success(data={
        "notification_poll_interval": settings.NOTIFICATION_POLL_INTERVAL,
        "upload_max_size_mb": settings.UPLOAD_MAX_SIZE_MB,
    })
