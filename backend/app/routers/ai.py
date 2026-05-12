from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.config_helper import DEFAULT_CONFIG, get_all_configs
from app.database import get_db
from app.models.models import Activity, ActivityImage, CreditAccumulation, User
from app.schemas.ai import (
    CreditAdviceActivityItem,
    CreditAdviceData,
    CreditAdvicePriorityItem,
    ParseActivityData,
    ParseActivityRequest,
    ParsedField,
)
from app.schemas.common import success
from app.utils.ai_client import parse_activity_text
from app.utils.credit_helper import _get_academic_year_start
from app.utils.deps import require_role

router = APIRouter(prefix="/v1/ai", tags=["AI"])

# ---------- 6.1 公众号解析 ----------

PARSED_FIELD_KEYS = [
    "title", "activity_type", "start_time", "end_time",
    "location", "credit_type", "credit_value",
    "registration_deadline", "max_participants", "description",
]


def _normalize_parsed_field(raw: dict | None, key: str) -> ParsedField:
    if not isinstance(raw, dict):
        raw = {}
    value = raw.get("value")
    confidence = raw.get("confidence", "low")
    if confidence not in ("high", "medium", "low"):
        confidence = "low"

    if key == "max_participants":
        try:
            value = int(value) if value is not None else 0
        except (ValueError, TypeError):
            value = 0
            confidence = "low"
    elif key == "credit_value":
        try:
            value = float(value) if value is not None else None
        except (ValueError, TypeError):
            value = None
            confidence = "low"

    return ParsedField(value=value, confidence=confidence)


@router.post("/parse-activity")
async def parse_activity(
    body: ParseActivityRequest,
    current_user: User = Depends(require_role("activity_owner")),
    db: AsyncSession = Depends(get_db),
):
    try:
        raw_result = await parse_activity_text(db, body.article_text, body.group_message)
    except Exception:
        raise HTTPException(status_code=502, detail="AI 解析服务暂不可用，请稍后重试")

    if not isinstance(raw_result, dict):
        raise HTTPException(status_code=502, detail="AI 返回格式异常")

    fields = {}
    for key in PARSED_FIELD_KEYS:
        fields[key] = _normalize_parsed_field(raw_result.get(key), key)

    return success(data=ParseActivityData(**fields).model_dump(mode='json'))


# ---------- 6.2 AI 学分分析与建议 ----------


@router.get("/credit-advice")
async def credit_advice(
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now()
    configs = await get_all_configs(db)
    credit_types = configs.get("credit_types", DEFAULT_CONFIG["credit_types"])
    credit_required_per_type = configs.get("credit_required_per_type", 0.5)
    total_required = configs.get("total_credit_required", 6.0)

    all_result = await db.execute(
        select(CreditAccumulation.credit_type, func.sum(CreditAccumulation.credit_value))
        .where(CreditAccumulation.user_id == current_user.id)
        .group_by(CreditAccumulation.credit_type)
    )
    all_map: dict[str, float] = {r[0]: float(r[1]) for r in all_result.all()}

    details = []
    total = 0.0
    for ct in credit_types:
        current = all_map.get(ct, 0.0)
        total += current
        gap = max(0.0, credit_required_per_type - current)
        details.append({"type": ct, "current": current, "gap": gap, "is_reached": current >= credit_required_per_type})

    total_gap_raw = max(0.0, total_required - total)
    each_type_gap = sum(max(0.0, credit_required_per_type - all_map.get(ct, 0.0)) for ct in credit_types)
    total_gap = max(total_gap_raw, each_type_gap)
    is_total_reached = total >= total_required

    priority_list = sorted(
        [{"type": d["type"], "gap": d["gap"]} for d in details if d["gap"] > 0],
        key=lambda x: x["gap"],
        reverse=True,
    )

    recommended = []
    if priority_list:
        target_type = priority_list[0]["type"]
        activities_result = await db.execute(
            select(Activity)
            .where(
                Activity.status == "active",
                Activity.credit_type == target_type,
                Activity.registration_deadline >= now,
            )
            .order_by(Activity.registration_deadline.asc())
            .limit(3)
        )
        activities = activities_result.scalars().all()

        activity_ids = [a.id for a in activities]
        cover_map: dict[int, str] = {}
        if activity_ids:
            images_result = await db.execute(
                select(ActivityImage.activity_id, ActivityImage.url)
                .where(ActivityImage.activity_id.in_(activity_ids), ActivityImage.is_cover == True)
            )
            for r in images_result.all():
                cover_map[r[0]] = r[1]

        for a in activities:
            recommended.append(CreditAdviceActivityItem(
                id=a.id,
                title=a.title,
                credit_type=a.credit_type,
                credit_value=float(a.credit_value) if a.credit_value is not None else None,
                registration_deadline=a.registration_deadline.isoformat(),
                location=a.location,
                cover_image_url=cover_map.get(a.id),
                match_reason=f"满足你当前最紧缺的 {target_type} 类学分需求",
            ))

    if not priority_list:
        summary = "恭喜！你已完成全部第二课堂学分要求"
    elif not is_total_reached:
        first = priority_list[0]["type"]
        second = priority_list[1]["type"] if len(priority_list) > 1 else None
        if second:
            summary = f"你还差 {total_gap} 分，优先参加{first}和{second}类活动"
        else:
            summary = f"你还差 {total_gap} 分，优先参加{first}类活动"
    else:
        first = priority_list[0]
        summary = f"总分已达标，但{first['type']}还差 {first['gap']} 分"

    return success(data=CreditAdviceData(
        total_gap=total_gap,
        priority_list=[CreditAdvicePriorityItem(**p) for p in priority_list],
        recommended_activities=recommended,
        summary=summary,
    ).model_dump(mode='json'))
