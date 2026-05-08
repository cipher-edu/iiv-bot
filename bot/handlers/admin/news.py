from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.news_repo import NewsRepository
from bot.states.admin_states import NewsCreateState
from bot.keyboards.user_reply import cancel_keyboard

router = Router(name="admin_news")


@router.callback_query(F.data == "admin:news")
async def admin_news(callback: CallbackQuery, session: AsyncSession):
    repo = NewsRepository(session)
    news_list = await repo.get_all(limit=20)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi yangilik", callback_data="admin:news:create")
    builder.adjust(1)

    text = "📰 <b>Yangiliklar boshqaruvi</b>\n\n"
    for n in news_list:
        status = "✅" if n.is_active else "❌"
        broadcast = "📢" if n.is_broadcast else "📝"
        text += f"{status}{broadcast} {n.title} (👁 {n.views_count})\n"

    if not news_list:
        text += "Hozircha yangiliklar yo'q."

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:news:create")
async def create_news_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewsCreateState.waiting_title)
    await callback.message.answer(
        "📰 <b>Yangi yangilik yaratish</b>\n\n"
        "Yangilik sarlavhasini kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(NewsCreateState.waiting_title, F.text)
async def news_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(title=message.text)
    await state.set_state(NewsCreateState.waiting_content)
    await message.answer("📝 Yangilik matnini kiriting:")


@router.message(NewsCreateState.waiting_content, F.text)
async def news_content(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    data = await state.get_data()
    repo = NewsRepository(session)

    await repo.create(
        title=data["title"],
        content=message.text,
        author_id=db_user.id,
    )

    await state.clear()
    await message.answer(
        f"✅ Yangilik yaratildi!\n\n"
        f"📰 {data['title']}\n\n"
        f"Broadcast qilish uchun admin panelga boring."
    )
