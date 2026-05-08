import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
import redis.asyncio as aioredis

from bot.config import settings
from bot.handlers import setup_routers
from bot.middlewares import (
    DatabaseSessionMiddleware,
    ThrottlingMiddleware,
    AuthMiddleware,
    BanCheckMiddleware,
    AuditLogMiddleware,
    MaintenanceMiddleware,
    ErrorHandlerMiddleware,
    I18nMiddleware,
)
from bot.scheduler.setup import setup_scheduler, scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("Bot ishga tushmoqda...")

    from bot.models.base import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database jadvallar yaratildi")

    sched = setup_scheduler(bot)
    sched.start()
    logger.info("Scheduler ishga tushdi")

    for admin_id in settings.bot_superadmin_ids:
        try:
            await bot.send_message(admin_id, "✅ Bot muvaffaqiyatli ishga tushdi!")
        except Exception:
            pass

    me = await bot.get_me()
    logger.info("Bot tayyor: @%s (id=%d)", me.username, me.id)


async def on_shutdown(bot: Bot):
    logger.info("Bot to'xtatilmoqda...")
    scheduler.shutdown(wait=False)

    for admin_id in settings.bot_superadmin_ids:
        try:
            await bot.send_message(admin_id, "⚠️ Bot to'xtatilmoqda...")
        except Exception:
            pass

    from bot.models.base import engine
    await engine.dispose()
    logger.info("Bot to'xtatildi")


async def main():
    redis_client = aioredis.from_url(
        settings.redis_fsm_url,
        decode_responses=True,
    )

    try:
        await redis_client.ping()
        storage = RedisStorage(redis=redis_client)
        logger.info("Redis FSM storage ulandi")
    except Exception as e:
        logger.warning("Redis ulanmadi (%s), MemoryStorage ishlatiladi", e)
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=storage)

    maintenance = MaintenanceMiddleware()

    root_router = setup_routers()

    dp.message.outer_middleware(ErrorHandlerMiddleware())
    dp.callback_query.outer_middleware(ErrorHandlerMiddleware())
    dp.message.outer_middleware(maintenance)
    dp.callback_query.outer_middleware(maintenance)

    root_router.message.outer_middleware(DatabaseSessionMiddleware())
    root_router.callback_query.outer_middleware(DatabaseSessionMiddleware())
    root_router.message.outer_middleware(ThrottlingMiddleware())
    root_router.callback_query.outer_middleware(ThrottlingMiddleware())
    root_router.message.outer_middleware(AuthMiddleware())
    root_router.callback_query.outer_middleware(AuthMiddleware())
    root_router.message.outer_middleware(BanCheckMiddleware())
    root_router.callback_query.outer_middleware(BanCheckMiddleware())
    root_router.message.outer_middleware(I18nMiddleware())
    root_router.callback_query.outer_middleware(I18nMiddleware())
    root_router.message.outer_middleware(AuditLogMiddleware())

    dp.include_router(root_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Polling boshlanmoqda...")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot qo'lda to'xtatildi")
