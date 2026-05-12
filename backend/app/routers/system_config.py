from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import success
from app.utils.config_helper import DEFAULT_CONFIG, get_all_configs

# 本文件仅保留公开配置接口，供活动表单下拉选项使用
# 管理端系统配置功能已被移除

public_router = APIRouter(prefix="/v1/system-config", tags=["系统配置（公开）"])


@public_router.get("/public")
async def get_public_config(
    db: AsyncSession = Depends(get_db),
):
    configs = await get_all_configs(db)
    return success(data={
        "credit_types": configs.get("credit_types", DEFAULT_CONFIG["credit_types"]),
        "activity_types": configs.get("activity_types", DEFAULT_CONFIG["activity_types"]),
        "owner_types": configs.get("owner_types", DEFAULT_CONFIG["owner_types"]),
    })
