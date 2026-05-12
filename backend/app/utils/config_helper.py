from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# 默认配置值（硬编码兜底，不再查询数据库）
DEFAULT_CONFIG: dict[str, Any] = {
    "credit_types": ["思想成长", "实践实习", "创新创业", "志愿公益", "文体活动", "技能特长"],
    "credit_required_per_type": 0.5,
    "total_credit_required": 6.0,
    "academic_year_start_month": 9,
    "activity_types": ["讲座", "志愿活动", "文体活动", "初赛", "观众招募", "分享会", "其他"],
    "owner_types": ["社团", "学生会", "团委", "班级", "其他"],
    "log_retention_days": 15,
}


async def get_config(db: AsyncSession, key: str) -> Any:
    """读取单个配置值（从内存默认值返回）"""
    return DEFAULT_CONFIG.get(key)


async def get_all_configs(db: AsyncSession) -> dict[str, Any]:
    """读取全部配置（从内存默认值返回）"""
    return dict(DEFAULT_CONFIG)
