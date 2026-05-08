from math import ceil

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.library_repo import (
    FileCategoryRepository,
    FileItemRepository,
    BookmarkRepository,
)
from bot.keyboards.inline import paginated_keyboard
from bot.keyboards.user_reply import back_keyboard
from bot.config import settings

router = Router(name="library")
router.message.filter(IsRegisteredFilter())


class LibrarySearchState(StatesGroup):
    waiting_query = State()


@router.message(F.text == "📚 Kutubxona")
async def show_library(message: Message, session: AsyncSession):
    repo = FileCategoryRepository(session)
    categories = await repo.get_root_categories()

    if not categories:
        await message.answer("📚 Kutubxona hozircha bo'sh.", reply_markup=back_keyboard())
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    for cat in categories:
        builder.button(
            text=f"{cat.icon} {cat.name}",
            callback_data=f"lib:cat:{cat.id}",
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔍 Qidirish", callback_data="lib:search"))
    builder.row(InlineKeyboardButton(text="⭐ Saqlangan", callback_data="lib:bookmarks"))

    await message.answer("📚 <b>Kutubxona</b>\n\nKategoriyani tanlang:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("lib:cat:"))
async def show_category_files(callback: CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split(":")[-1])
    repo = FileItemRepository(session)
    files = await repo.get_by_category(cat_id, limit=20)

    if not files:
        await callback.answer("Bu kategoriyada fayl yo'q.", show_alert=True)
        return

    items = [
        (f"📄 {f.title}", f"lib:file:{f.id}")
        for f in files
    ]
    total_pages = ceil(len(items) / settings.pagination_size) or 1
    page_items = items[: settings.pagination_size]

    await callback.message.edit_text(
        "📁 <b>Fayllar:</b>",
        reply_markup=paginated_keyboard(
            page_items, page=1, total_pages=total_pages,
            prefix="lib_files", back_button="lib:main",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lib:file:"))
async def view_file(callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser):
    file_id = int(callback.data.split(":")[-1])
    repo = FileItemRepository(session)
    file = await repo.get_by_id(file_id)

    if not file:
        await callback.answer("Fayl topilmadi.", show_alert=True)
        return

    text = (
        f"📄 <b>{file.title}</b>\n\n"
        f"{file.description or ''}\n\n"
        f"📦 Hajm: {file.file_size // 1024} KB\n"
        f"📥 Yuklab olingan: {file.download_count} marta\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Yuklab olish", callback_data=f"lib:download:{file.id}")
    builder.button(text="⭐ Saqlash", callback_data=f"lib:bookmark:{file.id}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"lib:cat:{file.category_id}"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("lib:download:"))
async def download_file(callback: CallbackQuery, session: AsyncSession):
    file_id = int(callback.data.split(":")[-1])
    repo = FileItemRepository(session)
    file = await repo.get_by_id(file_id)

    if not file:
        await callback.answer("Fayl topilmadi.", show_alert=True)
        return

    await repo.increment_download(file_id)

    try:
        from aiogram.types import FSInputFile
        doc = FSInputFile(file.file_path)
        await callback.message.answer_document(doc, caption=f"📄 {file.title}")
    except Exception:
        await callback.answer("Fayl yuklab bo'lmadi.", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("lib:bookmark:"))
async def toggle_bookmark(callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser):
    file_id = int(callback.data.split(":")[-1])
    repo = BookmarkRepository(session)
    added = await repo.toggle_bookmark(db_user.id, file_id)

    if added:
        await callback.answer("⭐ Saqlanganlarga qo'shildi!", show_alert=True)
    else:
        await callback.answer("Saqlangandan o'chirildi.", show_alert=True)


@router.callback_query(F.data == "lib:bookmarks")
async def show_bookmarks(callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser):
    repo = BookmarkRepository(session)
    bookmarks = await repo.get_user_bookmarks(db_user.id, limit=20)

    if not bookmarks:
        await callback.answer("Saqlangan fayllar yo'q.", show_alert=True)
        return

    items = [(f"⭐ Bookmark #{b.file_id}", f"lib:file:{b.file_id}") for b in bookmarks]
    total_pages = ceil(len(items) / settings.pagination_size) or 1

    await callback.message.edit_text(
        "⭐ <b>Saqlangan fayllar:</b>",
        reply_markup=paginated_keyboard(
            items[: settings.pagination_size], page=1,
            total_pages=total_pages, prefix="lib_bm", back_button="lib:main",
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "lib:search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LibrarySearchState.waiting_query)
    await callback.message.answer("🔍 Qidirish so'zini kiriting:")
    await callback.answer()


@router.message(LibrarySearchState.waiting_query, F.text)
async def process_search(message: Message, state: FSMContext, session: AsyncSession):
    repo = FileItemRepository(session)
    files = await repo.search_files(message.text, limit=20)
    await state.clear()

    if not files:
        await message.answer("Hech narsa topilmadi.", reply_markup=back_keyboard())
        return

    items = [(f"📄 {f.title}", f"lib:file:{f.id}") for f in files]
    total_pages = ceil(len(items) / settings.pagination_size) or 1

    await message.answer(
        f"🔍 <b>Natijalar:</b> {len(files)} ta topildi",
        reply_markup=paginated_keyboard(
            items[: settings.pagination_size], page=1,
            total_pages=total_pages, prefix="lib_search",
        ),
    )
