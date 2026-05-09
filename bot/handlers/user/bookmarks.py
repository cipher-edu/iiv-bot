from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.repositories.bookmark_repo import SavedItemRepository
from bot.repositories.course_repo import CourseRepository

router = Router(name="bookmarks")
router.message.filter(IsRegisteredFilter())


ENTITY_LABELS = {
    "lesson": "📖 Dars",
    "course": "📚 Kurs",
    "news": "📰 Yangilik",
    "library": "📁 Fayl",
}


@router.message(F.text == "🔖 Saqlanganlar")
async def show_saved(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    repo = SavedItemRepository(session)
    items = await repo.list_for_user(db_user.id, limit=50)

    if not items:
        await message.answer(
            "🔖 Saqlanganlar yo'q.\n\n"
            "Dars yoki yangilikni ochib, '🔖 Saqlash' tugmasini bosing."
        )
        return

    builder = InlineKeyboardBuilder()
    for it in items:
        label = ENTITY_LABELS.get(it.entity_type, "📌")
        title = it.title_cache or f"#{it.entity_id}"
        cb = _entity_callback(it.entity_type, it.entity_id)
        if cb:
            builder.button(text=f"{label} {title[:40]}", callback_data=cb)
        else:
            builder.button(
                text=f"{label} {title[:40]}",
                callback_data=f"saved:noop:{it.id}",
            )
    builder.adjust(1)

    await message.answer(
        f"🔖 <b>Saqlanganlar ({len(items)}):</b>",
        reply_markup=builder.as_markup(),
    )


def _entity_callback(entity_type: str, entity_id: int) -> str | None:
    if entity_type == "lesson":
        return f"saved:open_lesson:{entity_id}"
    if entity_type == "course":
        return f"course:view:{entity_id}"
    if entity_type == "news":
        return f"news:view:{entity_id}"
    return None


@router.callback_query(F.data.startswith("saved:open_lesson:"))
async def open_saved_lesson(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    lesson_id = int(callback.data.split(":")[-1])
    course_repo = CourseRepository(session)
    lesson = await course_repo.get_lesson(lesson_id)
    if not lesson:
        await callback.answer("Dars topilmadi.", show_alert=True)
        return

    text = f"📖 <b>{lesson.title}</b>\n\n{lesson.content or ''}"
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("save:lesson:"))
async def toggle_save_lesson(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    lesson_id = int(callback.data.split(":")[-1])
    course_repo = CourseRepository(session)
    lesson = await course_repo.get_lesson(lesson_id)
    if not lesson:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    repo = SavedItemRepository(session)
    saved = await repo.toggle(
        db_user.id, "lesson", lesson_id, title=lesson.title
    )
    await callback.answer(
        "🔖 Saqlandi" if saved else "❌ Olib tashlandi", show_alert=False
    )


@router.callback_query(F.data.startswith("save:course:"))
async def toggle_save_course(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    course_id = int(callback.data.split(":")[-1])
    course_repo = CourseRepository(session)
    course = await course_repo.get_by_id(course_id)
    if not course:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    repo = SavedItemRepository(session)
    saved = await repo.toggle(
        db_user.id, "course", course_id, title=course.title
    )
    await callback.answer(
        "🔖 Saqlandi" if saved else "❌ Olib tashlandi", show_alert=False
    )
