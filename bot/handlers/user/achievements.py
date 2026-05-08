from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.gamification_repo import (
    BadgeRepository,
    StreakRepository,
    ChallengeRepository,
)
from bot.keyboards.user_reply import back_keyboard
from bot.core.constants import BADGE_LABELS

router = Router(name="achievements")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "🎮 Yutuqlar")
async def show_achievements(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    badge_repo = BadgeRepository(session)
    streak_repo = StreakRepository(session)
    challenge_repo = ChallengeRepository(session)

    user_badges = await badge_repo.get_user_badges(db_user.id)
    streak = await streak_repo.get_user_streak(db_user.id)
    active_challenges = await challenge_repo.get_active_challenges()

    text = "🎮 <b>Yutuqlar va muvaffaqiyatlar</b>\n\n"

    text += "🏅 <b>Nishonlar:</b>\n"
    if user_badges:
        for ub in user_badges:
            badge = ub.badge
            text += f"  {badge.icon} {badge.name} — {badge.description}\n"
    else:
        text += "  Hali nishon yo'q. Testlar va kurslar orqali qo'lga kiriting!\n"

    text += f"\n🔥 <b>Streak:</b>\n"
    if streak:
        text += (
            f"  Joriy: {streak.current_streak} kun\n"
            f"  Eng uzun: {streak.longest_streak} kun\n"
        )
    else:
        text += "  Hali streakingiz yo'q. Har kuni kirib, streak boshlang!\n"

    text += f"\n🎯 <b>Faol challengelar:</b>\n"
    if active_challenges:
        for ch in active_challenges:
            participation = await challenge_repo.get_participation(db_user.id, ch.id)
            if participation:
                progress = f"{participation.current_value}/{ch.target_value}"
                status = "✅" if participation.is_completed else "🔄"
            else:
                progress = f"0/{ch.target_value}"
                status = "⏳"
            text += f"  {status} {ch.title} [{progress}] +{ch.reward_points} ball\n"
    else:
        text += "  Hozircha faol challenge yo'q.\n"

    await message.answer(text, reply_markup=back_keyboard())
