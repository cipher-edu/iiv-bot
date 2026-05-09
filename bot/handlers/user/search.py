from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.course import Course, Lesson
from bot.models.news import News
from bot.models.library import FileItem

router = Router(name="search")
router.message.filter(IsRegisteredFilter())


class SearchState(StatesGroup):
    waiting_query = State()


MIN_QUERY_LEN = 2
MAX_PER_TYPE = 5


@router.message(F.text == "🔍 Qidiruv")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_query)
    await message.answer(
        "🔍 Qidiruv so'zini kiriting (kurslar, darslar, yangiliklar, fayllar bo'yicha):"
    )


@router.message(SearchState.waiting_query, F.text)
async def search_run(
    message: Message, state: FSMContext, session: AsyncSession
):
    query = message.text.strip()
    if len(query) < MIN_QUERY_LEN:
        await message.answer(f"❌ Kamida {MIN_QUERY_LEN} ta belgi kiriting.")
        return

    await state.clear()
    pattern = f"%{query}%"

    courses_stmt = (
        select(Course)
        .where(
            Course.is_deleted == False,
            or_(Course.title.ilike(pattern), Course.description.ilike(pattern)),
        )
        .limit(MAX_PER_TYPE)
    )
    lessons_stmt = (
        select(Lesson)
        .where(
            Lesson.is_deleted == False,
            or_(Lesson.title.ilike(pattern), Lesson.content.ilike(pattern)),
        )
        .limit(MAX_PER_TYPE)
    )
    news_stmt = (
        select(News)
        .where(
            News.is_deleted == False,
            or_(News.title.ilike(pattern), News.content.ilike(pattern)),
        )
        .limit(MAX_PER_TYPE)
    )
    files_stmt = (
        select(FileItem)
        .where(
            FileItem.is_deleted == False,
            FileItem.is_active == True,
            or_(
                FileItem.title.ilike(pattern),
                FileItem.description.ilike(pattern),
            ),
        )
        .limit(MAX_PER_TYPE)
    )

    courses = (await session.execute(courses_stmt)).scalars().all()
    lessons = (await session.execute(lessons_stmt)).scalars().all()
    news_items = (await session.execute(news_stmt)).scalars().all()
    files = (await session.execute(files_stmt)).scalars().all()

    total = len(courses) + len(lessons) + len(news_items) + len(files)

    if total == 0:
        await message.answer(f"❌ <code>{query}</code> bo'yicha hech narsa topilmadi.")
        return

    text = f"🔍 <b>Topildi: {total} ta natija</b>\n"
    builder = InlineKeyboardBuilder()

    if courses:
        text += "\n📚 <b>Kurslar:</b>\n"
        for c in courses:
            text += f"  • {c.title}\n"
            builder.button(
                text=f"📚 {c.title[:40]}", callback_data=f"course:view:{c.id}"
            )

    if lessons:
        text += "\n📖 <b>Darslar:</b>\n"
        for l in lessons:
            text += f"  • {l.title}\n"
            builder.button(
                text=f"📖 {l.title[:40]}", callback_data=f"saved:open_lesson:{l.id}"
            )

    if news_items:
        text += "\n📰 <b>Yangiliklar:</b>\n"
        for n in news_items:
            text += f"  • {n.title}\n"
            builder.button(
                text=f"📰 {n.title[:40]}", callback_data=f"news:view:{n.id}"
            )

    if files:
        text += "\n📁 <b>Fayllar:</b>\n"
        for f in files:
            text += f"  • {f.title}\n"

    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())
