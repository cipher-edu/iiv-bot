from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.repositories.learning_path_repo import LearningPathRepository
from bot.repositories.course_repo import EnrollmentRepository

router = Router(name="learning_paths")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "🎯 O'qish yo'li")
async def show_paths(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    repo = LearningPathRepository(session)
    paths = await repo.get_active(limit=20)

    if not paths:
        await message.answer("🎯 Hozircha o'qish yo'llari mavjud emas.")
        return

    builder = InlineKeyboardBuilder()
    for p in paths:
        builder.button(
            text=f"{p.icon} {p.title} ({len(p.courses)} kurs)",
            callback_data=f"path:view:{p.id}",
        )
    builder.adjust(1)

    await message.answer(
        "🎯 <b>O'qish yo'llari:</b>\n\n"
        "Har bir yo'l — kurslar to'plami, ketma-ket o'zlashtirish uchun.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("path:view:"))
async def view_path(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    path_id = int(callback.data.split(":")[-1])
    repo = LearningPathRepository(session)
    enroll_repo = EnrollmentRepository(session)

    path = await repo.get_with_courses(path_id)
    if not path:
        await callback.answer("Yo'l topilmadi.", show_alert=True)
        return

    courses = await repo.get_courses_titles(path_id)
    user_path = await repo.get_user_enrollment(db_user.id, path_id)

    text = f"{path.icon} <b>{path.title}</b>\n\n{path.description or ''}\n\n"
    text += "<b>Kurslar:</b>\n"

    builder = InlineKeyboardBuilder()
    completed_count = 0
    for c in courses:
        ce = await enroll_repo.get_user_enrollment(db_user.id, c.id)
        if ce and ce.is_completed:
            icon = "✅"
            completed_count += 1
        elif ce:
            icon = "🔄"
        else:
            icon = "🔒"
        text += f"{icon} {c.title}\n"
        builder.button(text=f"📚 {c.title}", callback_data=f"course:view:{c.id}")

    text += f"\nProgress: {completed_count}/{len(courses)}"
    builder.adjust(1)

    if not user_path:
        builder.row(
            InlineKeyboardButton(
                text="📝 Yo'lga yozilish", callback_data=f"path:enroll:{path_id}"
            )
        )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("path:enroll:"))
async def enroll_path(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    path_id = int(callback.data.split(":")[-1])
    repo = LearningPathRepository(session)
    await repo.enroll_user(db_user.id, path_id)
    await callback.answer("✅ Yo'lga yozildingiz!", show_alert=True)
    await view_path(callback, session, db_user)
