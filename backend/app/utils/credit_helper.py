from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CreditAccumulation
from app.schemas.credits import CreditCategoryItem
from app.utils.config_helper import DEFAULT_CONFIG, get_all_configs


async def _get_academic_year_start(db: AsyncSession, now: datetime) -> datetime:
    """根据配置的学年起始月份计算当前学年的起始日期"""
    configs = await get_all_configs(db)
    start_month = configs.get("academic_year_start_month", 9)
    start_day = 1
    if now.month >= start_month:
        year = now.year
    else:
        year = now.year - 1
    return datetime(year, start_month, start_day)


async def calculate_credit_gaps(
    db: AsyncSession, user_id: int
) -> tuple[list[CreditCategoryItem], float, float]:
    """计算用户学分缺口，返回 (details, total, total_gap)"""
    configs = await get_all_configs(db)
    credit_types: list[str] = configs.get("credit_types", DEFAULT_CONFIG["credit_types"])
    required_per_type: float = configs.get("credit_required_per_type", 0.5)
    total_required: float = configs.get("total_credit_required", 6.0)

    all_result = await db.execute(
        select(CreditAccumulation.credit_type, func.sum(CreditAccumulation.credit_value))
        .where(CreditAccumulation.user_id == user_id)
        .group_by(CreditAccumulation.credit_type)
    )
    all_map: dict[str, float] = {r[0]: float(r[1]) for r in all_result.all()}

    details = []
    total = 0.0
    for ct in credit_types:
        current = all_map.get(ct, 0.0)
        total += current
        is_reached = current >= required_per_type
        gap = max(0.0, required_per_type - current)
        details.append(
            CreditCategoryItem(
                type=ct,
                current=current,
                required=required_per_type,
                is_reached=is_reached,
                gap=gap,
            )
        )

    each_type_gap = sum(max(0.0, required_per_type - all_map.get(ct, 0.0)) for ct in credit_types)
    total_gap_raw = max(0.0, total_required - total)
    total_gap = max(total_gap_raw, each_type_gap)
    return details, total, total_gap
