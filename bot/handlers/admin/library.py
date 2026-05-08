from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.library_repo import FileCategoryRepository, FileItemRepository

router = Router(name="admin_library")


class FileUploadState(StatesGroup):
    waiting_category = State()
    waiting_title = State()
    waiting_description = State()
    waiting_file = State()


class CategoryCreateState(StatesGroup):
    waiting_name = State()
    waiting_icon = State()


@router.callback_query(F.data == "admin:library")
async def admin_library(callback: CallbackQuery, session: AsyncSession):
    cat_repo = FileCategoryRepository(session)
    file_repo = FileItemRepository(session)
    categories = await cat_repo.get_active_categories()
    total_files = await file_repo.count()

    text = (
        "📚 <b>Kutubxona boshqaruvi</b>\n\n"
        f"📁 Kategoriyalar: {len(categories)}\n"
        f"📄 Jami fayllar: {total_files}\n\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Kategoriya yaratish", callback_data="admin:lib:create_cat")
    builder.button(text="📤 Fayl yuklash", callback_data="admin:lib:upload")
    builder.adjust(1)

    for cat in categories:
        builder.button(text=f"{cat.icon} {cat.name}", callback_data=f"admin:lib:cat:{cat.id}")
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:lib:create_cat")
async def create_category(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CategoryCreateState.waiting_name)
    await callback.message.answer("📁 Kategoriya nomini kiriting:")
    await callback.answer()


@router.message(CategoryCreateState.waiting_name, F.text)
async def category_name(message: Message, state: FSMContext):
    await state.update_data(cat_name=message.text)
    await state.set_state(CategoryCreateState.waiting_icon)
    await message.answer("Emoji ikonka tanlang (masalan: 📁, 📚, 🎓):")


@router.message(CategoryCreateState.waiting_icon, F.text)
async def category_icon(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    repo = FileCategoryRepository(session)
    await repo.create(name=data["cat_name"], icon=message.text.strip()[:10])
    await state.clear()
    await message.answer(f"✅ Kategoriya yaratildi: {message.text} {data['cat_name']}")


@router.callback_query(F.data == "admin:lib:upload")
async def upload_file_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    cat_repo = FileCategoryRepository(session)
    categories = await cat_repo.get_active_categories()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"{cat.icon} {cat.name}", callback_data=f"admin:lib:upcat:{cat.id}")
    builder.adjust(2)

    await state.set_state(FileUploadState.waiting_category)
    await callback.message.edit_text("📤 Kategoriyani tanlang:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(FileUploadState.waiting_category, F.data.startswith("admin:lib:upcat:"))
async def select_upload_category(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[-1])
    await state.update_data(category_id=cat_id)
    await state.set_state(FileUploadState.waiting_title)
    await callback.message.answer("📄 Fayl nomini kiriting:")
    await callback.answer()


@router.message(FileUploadState.waiting_title, F.text)
async def file_title(message: Message, state: FSMContext):
    await state.update_data(file_title=message.text)
    await state.set_state(FileUploadState.waiting_file)
    await message.answer("📤 Faylni yuboring (document sifatida):")


@router.message(FileUploadState.waiting_file, F.document)
async def receive_file(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    doc = message.document
    data = await state.get_data()

    file_path = f"data/library/{doc.file_id}_{doc.file_name}"

    repo = FileItemRepository(session)
    await repo.create(
        title=data["file_title"],
        file_path=file_path,
        file_type=doc.file_name.split(".")[-1] if "." in doc.file_name else "unknown",
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        category_id=data["category_id"],
        uploaded_by=db_user.id,
    )

    await state.clear()
    await message.answer(f"✅ Fayl yuklandi: {data['file_title']}")
