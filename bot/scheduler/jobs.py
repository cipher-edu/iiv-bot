import logging
import asyncio
from datetime import date, timedelta

from aiogram import Bot

from bot.models.base import async_session_factory
from bot.repositories.user_repo import UserRepository
from bot.repositories.news_repo import NewsRepository
from bot.repositories.rating_repo import RatingRepository, LeaderboardRepository
from bot.repositories.gamification_repo import StreakRepository
from bot.config import settings

logger = logging.getLogger(__name__)


async def news_broadcast_job(bot: Bot):
    logger.info("Yangiliklar broadcast boshlandi")
    async with async_session_factory() as session:
        async with session.begin():
            news_repo = NewsRepository(session)
            user_repo = UserRepository(session)

            unbroadcast = await news_repo.get_unbroadcast()
            if not unbroadcast:
                logger.info("Broadcast uchun yangilik yo'q")
                return

            active_ids = await user_repo.get_all_active_ids()
            sent_total = 0

            for news in unbroadcast:
                for tg_id in active_ids:
                    try:
                        await bot.send_message(
                            tg_id,
                            f"📰 <b>{news.title}</b>\n\n{news.content[:3000]}",
                        )
                        await news_repo.create_broadcast_log(
                            news.id, tg_id, is_delivered=True
                        )
                        sent_total += 1
                    except Exception as e:
                        await news_repo.create_broadcast_log(
                            news.id, tg_id, is_delivered=False, error=str(e)[:200]
                        )
                    await asyncio.sleep(0.05)

                await news_repo.mark_broadcast(news.id)

            await session.commit()
            logger.info("Broadcast tugadi: %d xabar yuborildi", sent_total)


async def rating_calculation_job(bot: Bot):
    logger.info("Haftalik reyting hisoblash boshlandi")
    async with async_session_factory() as session:
        async with session.begin():
            rating_repo = RatingRepository(session)
            leaderboard_repo = LeaderboardRepository(session)
            user_repo = UserRepository(session)

            top_ratings = await rating_repo.get_weekly_leaderboard(limit=20)

            rankings = []
            for idx, rating in enumerate(top_ratings):
                user = await user_repo.get_by_id(rating.user_id)
                if user:
                    rankings.append({
                        "position": idx + 1,
                        "user_id": user.id,
                        "name": user.display_name,
                        "points": rating.weekly_points,
                    })

            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            await leaderboard_repo.save_weekly(
                week_start=week_start,
                week_end=week_end,
                rankings=rankings,
                total_participants=len(rankings),
            )

            await rating_repo.reset_weekly_points()
            await session.commit()

            if rankings:
                text = "🏆 <b>Haftalik reyting natijalari</b>\n\n"
                medals = ["🥇", "🥈", "🥉"]
                for r in rankings[:10]:
                    medal = medals[r["position"] - 1] if r["position"] <= 3 else f"{r['position']}."
                    text += f"{medal} {r['name']} — {r['points']} ball\n"

                active_ids = await user_repo.get_all_active_ids()
                for tg_id in active_ids:
                    try:
                        await bot.send_message(tg_id, text)
                    except Exception:
                        pass
                    await asyncio.sleep(0.05)

    logger.info("Haftalik reyting hisoblash tugadi")


async def certificate_check_job(bot: Bot):
    logger.info("Oylik sertifikat tekshiruvi boshlandi")
    async with async_session_factory() as session:
        async with session.begin():
            from bot.repositories.course_repo import EnrollmentRepository
            from bot.repositories.certificate_repo import CertificateRepository

            enroll_repo = EnrollmentRepository(session)
            cert_repo = CertificateRepository(session)

            # Bu yerda tugatilgan kurslar uchun sertifikat yaratish logikasi
            logger.info("Sertifikat tekshiruvi tugadi")


async def streak_check_job():
    logger.info("Streak tekshiruvi boshlandi")
    # Streak reset logic — foydalanuvchilar bugun kirmagan bo'lsa reset
    logger.info("Streak tekshiruvi tugadi")


async def cleanup_job():
    logger.info("Cleanup boshlandi")
    async with async_session_factory() as session:
        async with session.begin():
            from bot.repositories.test_repo import TestSessionRepository
            from bot.core.enums import TestSessionStatus
            from sqlalchemy import update, and_
            from datetime import datetime, timedelta
            from bot.models.test import TestSession

            cutoff = datetime.utcnow() - timedelta(hours=24)
            from sqlalchemy import update as sa_update
            stmt = (
                sa_update(TestSession)
                .where(
                    TestSession.status == TestSessionStatus.ACTIVE,
                    TestSession.started_at < cutoff,
                )
                .values(status=TestSessionStatus.ABANDONED)
            )
            await session.execute(stmt)
            await session.commit()
    logger.info("Cleanup tugadi")


async def spaced_repetition_job(bot: Bot):
    """Send reminders for lessons whose next_review_at has passed."""
    from datetime import datetime, timedelta
    from sqlalchemy import select, update as sa_update
    from bot.models.repetition import SpacedRepetition
    from bot.models.course import Lesson

    logger.info("Spaced repetition tekshiruvi boshlandi")
    async with async_session_factory() as session:
        async with session.begin():
            now = datetime.utcnow()
            stmt = select(SpacedRepetition).where(
                SpacedRepetition.is_active == True,
                SpacedRepetition.sent_reminder == False,
                SpacedRepetition.next_review_at <= now,
            ).limit(200)
            items = (await session.execute(stmt)).scalars().all()

            user_repo = UserRepository(session)
            for item in items:
                user = await user_repo.get_by_id(item.user_id)
                lesson = await session.get(Lesson, item.lesson_id)
                if not user or not lesson:
                    item.is_active = False
                    continue
                try:
                    await bot.send_message(
                        user.telegram_id,
                        f"🔁 <b>Takrorlash vaqti</b>\n\n"
                        f"Quyidagi darsni qayta ko'rib chiqing:\n"
                        f"📖 <b>{lesson.title}</b>",
                    )
                    item.sent_reminder = True
                    item.last_reviewed_at = now
                    item.review_count += 1
                    item.interval_days = min(item.interval_days * 2, 90)
                    item.next_review_at = now + timedelta(days=item.interval_days)
                    item.sent_reminder = False
                except Exception:
                    pass
            await session.commit()
    logger.info("Spaced repetition tugadi")


async def health_check_job(bot: Bot):
    try:
        me = await bot.get_me()
        logger.debug("Health check OK: @%s", me.username)
    except Exception as e:
        logger.error("Health check FAILED: %s", e)
        for admin_id in settings.bot_superadmin_ids:
            try:
                await bot.send_message(
                    admin_id, f"⚠️ <b>Tizim ogohlantiruvi</b>\n\nHealth check xatolik: {e}"
                )
            except Exception:
                pass
