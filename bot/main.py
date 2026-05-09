import asyncio
import logging
import signal
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

_heartbeat_task: asyncio.Task | None = None


async def on_startup(bot: Bot):
    global _heartbeat_task
    logger.info("Bot ishga tushmoqda...")

    from bot.models.base import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database jadvallar yaratildi")

    from bot.models.migrations import apply_additive_migrations
    await apply_additive_migrations(engine)
    logger.info("Schema patches applied")

    from bot.services.superadmin_sync import sync_superadmins
    await sync_superadmins(settings.bot_superadmin_ids)
    logger.info("Superadmin sinxronizatsiyasi tugadi")

    sched = setup_scheduler(bot)
    sched.start()
    logger.info("Scheduler ishga tushdi")

    from bot.core.broadcast_queue import init_broadcast_queue
    init_broadcast_queue(bot)
    logger.info("Broadcast queue ishga tushdi")

    from bot.core.heartbeat import heartbeat_loop
    _heartbeat_task = asyncio.create_task(heartbeat_loop(), name="heartbeat")

    for admin_id in settings.bot_superadmin_ids:
        try:
            await bot.send_message(admin_id, "✅ Bot muvaffaqiyatli ishga tushdi!")
        except Exception:
            pass

    me = await bot.get_me()
    logger.info("Bot tayyor: @%s (id=%d)", me.username, me.id)


async def on_shutdown(bot: Bot):
    global _heartbeat_task
    logger.info("Bot to'xtatilmoqda...")

    try:
        scheduler.shutdown(wait=False)
    except Exception:
        logger.exception("Scheduler to'xtashda xato")

    if _heartbeat_task and not _heartbeat_task.done():
        _heartbeat_task.cancel()
        try:
            await _heartbeat_task
        except (asyncio.CancelledError, Exception):
            pass

    try:
        from bot.core.broadcast_queue import broadcast_queue
        if broadcast_queue:
            await broadcast_queue.stop()
    except Exception:
        logger.exception("Broadcast queue to'xtashda xato")

    try:
        from bot.core.cache import cache
        await cache.close()
    except Exception:
        pass

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

    from bot.core.bot_middleware import RetryRequestMiddleware
    bot.session.middleware(RetryRequestMiddleware())

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

    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Tashqi to'xtatish signali keldi")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig_name in ("SIGTERM", "SIGINT"):
        sig = getattr(signal, sig_name, None)
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows
            signal.signal(sig, lambda *_: stop_event.set())

    polling_task = asyncio.create_task(
        dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            handle_signals=False,
        ),
        name="polling",
    )

    stop_task = asyncio.create_task(stop_event.wait(), name="stop")

    done, pending = await asyncio.wait(
        {polling_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
    )

    if stop_task in done and not polling_task.done():
        await dp.stop_polling()
        try:
            await asyncio.wait_for(polling_task, timeout=15)
        except asyncio.TimeoutError:
            polling_task.cancel()

    for t in pending:
        t.cancel()

    try:
        await bot.session.close()
    except Exception:
        pass

    try:
        await redis_client.aclose()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot qo'lda to'xtatildi")
