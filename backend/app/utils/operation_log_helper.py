from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import OperationLog


async def log_operation(
    db: AsyncSession,
    user_id: int | None,
    operation: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> None:
    log = OperationLog(
        user_id=user_id,
        operation=operation,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
