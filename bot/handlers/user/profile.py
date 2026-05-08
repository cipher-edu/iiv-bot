from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.rating_repo import RatingRepository
from bot.repositories.gamification_repo import StreakRepository, LevelRepository
from bot.keyboards.user_reply import back_keyboard
from bot.core.constants import LEVELS

router = Router(name="profile")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "👤 Profil")
async def show_profile(message: Message, session: AsyncSession, db_user: TelegramUser):
    rating_repo = RatingRepository(session)
    streak_repo = StreakRepository(session)
    level_repo = LevelRepository(session)

    rating = await rating_repo.get_by_user_id(db_user.id)
    rank = await rating_repo.get_user_rank(db_user.id)
    streak = await streak_repo.get_user_streak(db_user.id)
    level = await level_repo.get_user_level(db_user.id)

    current_level = "Yangi xodim"
    if level:
        current_level = level.level_name
    elif rating:
        for lvl in LEVELS:
            if lvl["min_points"] <= rating.total_points <= lvl["max_points"]:
                current_level = lvl["name"]
                break

    text = (
        f"👤 <b>Profil</b>\n\n"
        f"{'─' * 25}\n"
        f"👤 Ism: {db_user.full_name}\n"
        f"📱 Telefon: {db_user.phone or '—'}\n"
        f"💼 Lavozim: {db_user.position or '—'}\n"
        f"🏢 Tashkilot: {db_user.organization.name if db_user.organization else '—'}\n"
        f"{'─' * 25}\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"🎖 Daraja: {current_level}\n"
        f"🏅 O'rin: #{rank or '—'}\n"
        f"💰 Ball: {rating.total_points if rating else 0}\n"
        f"📝 Testlar: {rating.tests_passed if rating else 0}/{rating.tests_taken if rating else 0}\n"
        f"📚 Kurslar: {rating.courses_completed if rating else 0}\n"
        f"🔥 Streak: {streak.current_streak if streak else 0} kun\n"
        f"🏆 Eng uzun streak: {streak.longest_streak if streak else 0} kun\n"
    )

    await message.answer(text, reply_markup=back_keyboard())
