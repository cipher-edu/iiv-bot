import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.timezone)


def setup_scheduler(bot) -> AsyncIOScheduler:
    from bot.scheduler.jobs import (
        news_broadcast_job,
        rating_calculation_job,
        certificate_check_job,
        streak_check_job,
        cleanup_job,
        health_check_job,
    )

    scheduler.add_job(
        news_broadcast_job,
        CronTrigger(
            hour=settings.news_broadcast_hour,
            minute=settings.news_broadcast_minute,
        ),
        id="news_broadcast",
        name="Yangiliklar broadcast",
        kwargs={"bot": bot},
        replace_existing=True,
    )

    scheduler.add_job(
        rating_calculation_job,
        CronTrigger(
            day_of_week=settings.rating_calc_day,
            hour=settings.rating_calc_hour,
        ),
        id="rating_calculation",
        name="Haftalik reyting hisoblash",
        kwargs={"bot": bot},
        replace_existing=True,
    )

    scheduler.add_job(
        certificate_check_job,
        CronTrigger(
            day=settings.certificate_check_day,
            hour=settings.certificate_check_hour,
        ),
        id="certificate_check",
        name="Oylik sertifikat tekshiruvi",
        kwargs={"bot": bot},
        replace_existing=True,
    )

    scheduler.add_job(
        streak_check_job,
        CronTrigger(hour=23, minute=59),
        id="streak_check",
        name="Kunlik streak tekshiruvi",
        replace_existing=True,
    )

    scheduler.add_job(
        cleanup_job,
        CronTrigger(hour=settings.cleanup_hour),
        id="cleanup",
        name="Eski sessiyalarni tozalash",
        replace_existing=True,
    )

    scheduler.add_job(
        health_check_job,
        "interval",
        minutes=5,
        id="health_check",
        name="Tizim salomatligi tekshiruvi",
        kwargs={"bot": bot},
        replace_existing=True,
    )

    logger.info("Scheduler sozlandi: %d ta job", len(scheduler.get_jobs()))
    return scheduler
