import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from app.utils.config_helper import get_all_configs
from app.models.models import Activity, CreditAccumulation, Favorite, Notification, OperationLog, Participation, SchedulerState

logger = logging.getLogger(__name__)

REMINDER_NODES = [
    ("7d", timedelta(days=7), "将在 7 天后截止报名"),
    ("4d", timedelta(days=4), "将在 4 天后截止报名"),
    ("24h", timedelta(hours=24), "将在 24 小时后截止报名"),
]


async def _get_scheduler_state(db: AsyncSession) -> SchedulerState:
    result = await db.execute(
        select(SchedulerState).where(SchedulerState.job_name == "daily_reminder_cleanup")
    )
    state = result.scalar_one_or_none()
    if state is None:
        state = SchedulerState(job_name="daily_reminder_cleanup", last_run_at=None)
        db.add(state)
        await db.commit()
        await db.refresh(state)
    return state


async def _is_already_registered(db: AsyncSession, user_id: int, activity_id: int) -> bool:
    result = await db.execute(
        select(Participation.id).where(
            Participation.user_id == user_id,
            Participation.activity_id == activity_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def _notification_exists(db: AsyncSession, user_id: int, activity_id: int, node_type: str) -> bool:
    result = await db.execute(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.link_id == activity_id,
            Notification.node_type == node_type,
        )
    )
    return result.scalar_one_or_none() is not None


async def generate_reminders(db: AsyncSession, now: datetime, last_run_at: datetime | None) -> tuple[int, int]:
    generated = 0
    skipped_registered = 0

    result = await db.execute(
        select(Favorite, Activity)
        .join(Activity, Favorite.activity_id == Activity.id)
        .where(Activity.registration_deadline > now)
    )
    rows = result.all()

    for fav, activity in rows:
        user_id = fav.user_id
        activity_id = activity.id
        deadline = activity.registration_deadline

        for node_type, delta, content_suffix in REMINDER_NODES:
            node_time = deadline - delta

            if node_type == "7d":
                if not (node_time <= now and (now - node_time) <= timedelta(hours=27)):
                    continue
            else:
                if not (node_time <= now and (last_run_at is None or node_time > last_run_at)):
                    continue

            if await _is_already_registered(db, user_id, activity_id):
                skipped_registered += 1
                continue

            if await _notification_exists(db, user_id, activity_id, node_type):
                continue

            notification = Notification(
                user_id=user_id,
                type="favorite_reminder",
                title="收藏提醒",
                content=f"「{activity.title}」{content_suffix}",
                link_type="activity",
                link_id=activity_id,
                node_type=node_type,
            )
            db.add(notification)
            try:
                await db.commit()
                generated += 1
            except IntegrityError:
                await db.rollback()
                continue

    return generated, skipped_registered


async def cleanup_old_notifications(db: AsyncSession, now: datetime) -> int:
    cutoff = now - timedelta(days=settings.NOTIFICATION_CLEANUP_DAYS)
    result = await db.execute(
        delete(Notification).where(Notification.created_at < cutoff)
    )
    await db.commit()
    return result.rowcount or 0


async def award_credits_for_finished_activities(db: AsyncSession) -> int:
    """为已结束但还未发放学分的活动发放学分"""
    from app.models.models import Activity

    result = await db.execute(
        select(Activity).where(
            Activity.status == "active",
            Activity.end_time != None,  # noqa: E711
            Activity.end_time <= datetime.now(),
        )
    )
    activities = result.scalars().all()
    awarded = 0

    # 计算当前学年
    configs = await get_all_configs(db)
    start_month = configs.get("academic_year_start_month", 9)
    now = datetime.now()
    if now.month >= start_month:
        ay_start = now.year
        ay_end = now.year + 1
    else:
        ay_start = now.year - 1
        ay_end = now.year
    academic_year_str = f"{ay_start}-{ay_end}"

    for activity in activities:
        # 查找该活动的未发放学分的参与记录
        participations_result = await db.execute(
            select(Participation).where(
                Participation.activity_id == activity.id,
                Participation.credit_awarded == False,  # noqa: E712
            )
        )
        participations = participations_result.scalars().all()

        for participation in participations:
            # 检查是否已有学分记录（防止重复发放）
            existing = await db.execute(
                select(CreditAccumulation).where(
                    CreditAccumulation.participation_id == participation.id
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            # 发放学分
            credit_record = CreditAccumulation(
                user_id=participation.user_id,
                participation_id=participation.id,
                credit_type=activity.credit_type,
                credit_value=activity.credit_value,
                activity_title=activity.title,
                academic_year=academic_year_str,
            )
            db.add(credit_record)
            participation.credit_awarded = True
            awarded += 1

        # 更新活动状态为已结束
        activity.status = "ended"

    await db.commit()
    if awarded > 0:
        logger.info("[Scheduler] Awarded credits to %d participants from %d finished activities", awarded, len(activities))
    return awarded


async def update_dashboard_stats(db: AsyncSession) -> None:
    """更新 dashboard 统计缓存，先清后写防止脏数据"""
    from datetime import datetime, timedelta, timezone

    result = await db.execute(
        select(SchedulerState).where(SchedulerState.job_name == "daily_stats")
    )
    state = result.scalar_one_or_none()

    # 计算最新的 total_participations
    total_count = await db.execute(select(func.count(Participation.id)))
    total_participations = total_count.scalar() or 0

    if state is None:
        state = SchedulerState(
            job_name="daily_stats",
            last_run_at=datetime.now(timezone(timedelta(hours=8))),
            extra_data={"total_participations": total_participations},
        )
        db.add(state)
    else:
        # 先清空再写入新值（防止旧字段残留）
        state.extra_data = {"total_participations": total_participations}
        state.last_run_at = datetime.now(timezone(timedelta(hours=8)))

    await db.commit()
    logger.info("[Scheduler] Dashboard stats updated: total_participations=%d", total_participations)


async def run_daily_tasks():
    now = datetime.now()
    logger.info("[Scheduler] Daily task started at %s", now.isoformat())

    async with async_session() as db:
        state = await _get_scheduler_state(db)
        last_run_at = state.last_run_at

        try:
            # 1. 为已结束的活动发放学分
            awarded = await award_credits_for_finished_activities(db)

            # 2. 生成收藏提醒
            generated, skipped_registered = await generate_reminders(db, now, last_run_at)

            # 3. 清理旧通知
            cleaned = await cleanup_old_notifications(db, now)

            # 4. 清理过期操作日志
            configs = await get_all_configs(db)
            log_retention_days = configs.get("log_retention_days", 90)
            log_cutoff = now - timedelta(days=log_retention_days)
            log_result = await db.execute(
                delete(OperationLog).where(OperationLog.created_at < log_cutoff)
            )
            log_cleaned = log_result.rowcount or 0

            state.last_run_at = now

            # 5. 更新 dashboard 统计缓存
            await update_dashboard_stats(db)

            await db.commit()

            logger.info(
                "[Scheduler] Awarded credits to %d participants, generated %d reminders, skipped %d already-registered, cleaned %d old messages, cleaned %d old logs",
                awarded, generated, skipped_registered, cleaned, log_cleaned,
            )
        except Exception:
            logger.exception("[Scheduler] Daily task failed")
            raise


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        run_daily_tasks,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_reminder_cleanup",
        max_instances=1,
        misfire_grace_time=300,
        replace_existing=True,
    )
    return scheduler


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    await run_daily_tasks()


if __name__ == "__main__":
    asyncio.run(main())
