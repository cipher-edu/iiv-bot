from math import ceil

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.news_repo import NewsRepository
from bot.keyboards.inline import paginated_keyboard
from bot.keyboards.user_reply import back_keyboard
from bot.config import settings

router = Router(name="news")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "📰 Yangiliklar")
async def show_news(message: Message, session: AsyncSession, db_user: TelegramUser):
    repo = NewsRepository(session)
    news_list = await repo.get_active_news(limit=50)

    if not news_list:
        await message.answer("Hozircha yangiliklar yo'q.", reply_markup=back_keyboard())
        return

    items = [
        (f"📰 {n.title}", f"news:view:{n.id}")
        for n in news_list
    ]
    total_pages = ceil(len(items) / settings.pagination_size)
    page_items = items[: settings.pagination_size]

    await message.answer(
        "📰 <b>Yangiliklar:</b>",
        reply_markup=paginated_keyboard(
            page_items, page=1, total_pages=total_pages, prefix="news"
        ),
    )


@router.callback_query(F.data.startswith("news:view:"))
async def view_news(callback: CallbackQuery, session: AsyncSession):
    news_id = int(callback.data.split(":")[-1])
    repo = NewsRepository(session)
    news = await repo.get_by_id(news_id)

    if not news:
        await callback.answer("Yangilik topilmadi.", show_alert=True)
        return

    await repo.increment_views(news_id)

    text = (
        f"📰 <b>{news.title}</b>\n\n"
        f"{news.content}\n\n"
        f"📅 {news.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"👁 {news.views_count + 1} marta ko'rilgan"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="news:list"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "news:list")
async def back_to_news_list(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    repo = NewsRepository(session)
    news_list = await repo.get_active_news(limit=50)

    items = [
        (f"📰 {n.title}", f"news:view:{n.id}")
        for n in news_list
    ]
    total_pages = ceil(len(items) / settings.pagination_size)
    page_items = items[: settings.pagination_size]

    await callback.message.edit_text(
        "📰 <b>Yangiliklar:</b>",
        reply_markup=paginated_keyboard(
            page_items, page=1, total_pages=total_pages, prefix="news"
        ),
    )
    await callback.answer()
