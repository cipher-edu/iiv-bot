from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.rating_repo import RatingRepository
from bot.repositories.user_repo import UserRepository
from bot.keyboards.user_reply import back_keyboard

router = Router(name="rating")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "🏆 Reyting")
async def show_rating(message: Message, session: AsyncSession, db_user: TelegramUser):
    rating_repo = RatingRepository(session)
    user_repo = UserRepository(session)

    my_rating = await rating_repo.get_by_user_id(db_user.id)
    my_rank = await rating_repo.get_user_rank(db_user.id)
    top_ratings = await rating_repo.get_leaderboard(limit=10)

    text = "🏆 <b>Reyting jadvali</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]
    for idx, rating in enumerate(top_ratings):
        user = await user_repo.get_by_id(rating.user_id)
        if not user:
            continue
        medal = medals[idx] if idx < 3 else f"{idx + 1}."
        name = user.display_name
        if user.id == db_user.id:
            name = f"<b>{name} (siz)</b>"
        text += f"{medal} {name} — {rating.total_points} ball\n"

    text += f"\n{'─' * 25}\n"

    if my_rating:
        text += (
            f"\n👤 <b>Sizning natijangiz:</b>\n"
            f"🏅 O'rin: {my_rank}\n"
            f"💰 Jami ball: {my_rating.total_points}\n"
            f"📅 Haftalik: {my_rating.weekly_points}\n"
            f"📝 Testlar: {my_rating.tests_passed}/{my_rating.tests_taken}\n"
            f"📚 Kurslar: {my_rating.courses_completed}\n"
        )
    else:
        text += "\n📊 Siz hali ball to'plamadingiz."

    await message.answer(text, reply_markup=back_keyboard())
