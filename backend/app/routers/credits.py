from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.config_helper import get_all_configs
from app.database import get_db
from app.models.models import CreditAccumulation, User
from app.schemas.credits import CreditSummaryData
from app.schemas.common import success
from app.utils.credit_helper import calculate_credit_gaps, _get_academic_year_start
from app.utils.deps import require_role

router = APIRouter(prefix="/v1/credits", tags=["学分"])


# ---------- 5.1 我的学分汇总 ----------

@router.get("/summary")
async def credit_summary(
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    academic_year_start = await _get_academic_year_start(db, now)
    configs = await get_all_configs(db)
    total_required = configs.get("total_credit_required", 6.0)
    required_per_type = configs.get("credit_required_per_type", 0.5)

    details, total, total_gap = await calculate_credit_gaps(db, current_user.id)

    # 学年求和
    yearly_result = await db.execute(
        select(CreditAccumulation.credit_type, func.sum(CreditAccumulation.credit_value))
        .where(
            CreditAccumulation.user_id == current_user.id,
            CreditAccumulation.earned_at >= academic_year_start,
        )
        .group_by(CreditAccumulation.credit_type)
    )
    yearly_map = {r[0]: float(r[1]) for r in yearly_result.all()}
    yearly_total = sum(yearly_map.values())

    return success(
        data=CreditSummaryData(
            details=details,
            yearly_total=yearly_total,
            total=total,
            total_required=total_required,
            is_total_reached=total >= total_required and all(d.is_reached for d in details),
            total_gap=total_gap,
            per_type_required=required_per_type,
        ).model_dump(mode='json')
    )
