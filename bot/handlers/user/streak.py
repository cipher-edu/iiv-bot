from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.services.streak_service import StreakService

router = Router(name="streak")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "🔥 Streak")
async def show_streak(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    service = StreakService(session)
    streak = await service.get(db_user.id)

    fire = "🔥" * min(streak.current_streak, 10)
    text = (
        f"🔥 <b>Sizning streak'ingiz</b>\n\n"
        f"Hozirgi: <b>{streak.current_streak}</b> kun {fire}\n"
        f"Eng uzun: <b>{streak.longest_streak}</b> kun\n"
    )
    if streak.last_activity_date:
        text += f"Oxirgi faollik: {streak.last_activity_date.strftime('%d.%m.%Y')}\n"

    text += (
        "\n💡 Har kuni botga kiring va qandaydir faollik qiling — "
        "streak bu degani 'kuningiz buzilmagan'!\n\n"
        f"🎁 Har 7 kunda <b>bonus ball</b> beriladi."
    )

    await message.answer(text)
