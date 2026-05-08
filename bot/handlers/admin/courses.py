from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.course_repo import CourseRepository
from bot.states.admin_states import CourseCreateState
from bot.keyboards.user_reply import cancel_keyboard

router = Router(name="admin_courses")


@router.callback_query(F.data == "admin:courses")
async def admin_courses(callback: CallbackQuery, session: AsyncSession):
    repo = CourseRepository(session)
    courses = await repo.get_all(limit=50)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi kurs", callback_data="admin:courses:create")
    builder.adjust(1)

    text = "📚 <b>Kurslar boshqaruvi</b>\n\n"
    for c in courses:
        status = "✅" if c.is_active else "❌"
        text += f"{status} {c.title} ({c.total_lessons} dars)\n"

    if not courses:
        text += "Kurslar yo'q."

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:courses:create")
async def create_course_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourseCreateState.waiting_title)
    await callback.message.answer(
        "📚 <b>Yangi kurs yaratish</b>\n\nKurs nomini kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(CourseCreateState.waiting_title, F.text)
async def course_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(title=message.text)
    await state.set_state(CourseCreateState.waiting_description)
    await message.answer("📋 Kurs tavsifini kiriting (yoki '-'):")


@router.message(CourseCreateState.waiting_description, F.text)
async def course_description(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    desc = message.text if message.text != "-" else None

    repo = CourseRepository(session)
    course = await repo.create(title=data["title"], description=desc)

    await state.update_data(course_id=course.id, description=desc)
    await state.set_state(CourseCreateState.waiting_module_title)
    await message.answer(
        f"✅ Kurs yaratildi: <b>{data['title']}</b>\n\n"
        "Endi modullar qo'shing.\n1-modul nomini kiriting:"
    )


@router.message(CourseCreateState.waiting_module_title, F.text)
async def module_title(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("✅ Kurs saqlandi.")
        return

    data = await state.get_data()
    repo = CourseRepository(session)
    module_count = data.get("module_count", 0)
    module = await repo.create_module(data["course_id"], message.text, order=module_count + 1)

    await state.update_data(
        current_module_id=module.id,
        module_count=module_count + 1,
    )
    await state.set_state(CourseCreateState.waiting_lesson_title)
    await message.answer(f"📖 \"{message.text}\" moduliga dars qo'shing.\nDars nomini kiriting:")


@router.message(CourseCreateState.waiting_lesson_title, F.text)
async def lesson_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("✅ Kurs saqlandi.")
        return
    await state.update_data(lesson_title=message.text)
    await state.set_state(CourseCreateState.waiting_lesson_content)
    await message.answer("📝 Dars matnini kiriting (yoki '-'):")


@router.message(CourseCreateState.waiting_lesson_content, F.text)
async def lesson_content(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    content = message.text if message.text != "-" else None

    repo = CourseRepository(session)
    lesson_count = data.get("lesson_count", 0)
    await repo.create_lesson(
        module_id=data["current_module_id"],
        title=data["lesson_title"],
        content=content,
        order=lesson_count + 1,
    )
    await state.update_data(lesson_count=lesson_count + 1)
    await state.set_state(CourseCreateState.confirm_add_more_lessons)
    await message.answer("✅ Dars qo'shildi!\n\nYana dars qo'shasizmi? (ha/yo'q)")


@router.message(CourseCreateState.confirm_add_more_lessons, F.text)
async def more_lessons(message: Message, state: FSMContext):
    if message.text.lower() in ("ha", "yes", "da"):
        await state.set_state(CourseCreateState.waiting_lesson_title)
        await message.answer("Dars nomini kiriting:")
    else:
        await state.set_state(CourseCreateState.confirm_add_more_modules)
        await message.answer("Yana modul qo'shasizmi? (ha/yo'q)")


@router.message(CourseCreateState.confirm_add_more_modules, F.text)
async def more_modules(message: Message, state: FSMContext):
    if message.text.lower() in ("ha", "yes", "da"):
        data = await state.get_data()
        count = data.get("module_count", 0)
        await state.update_data(lesson_count=0)
        await state.set_state(CourseCreateState.waiting_module_title)
        await message.answer(f"{count + 1}-modul nomini kiriting:")
    else:
        data = await state.get_data()
        await state.clear()
        await message.answer(
            f"✅ Kurs muvaffaqiyatli yaratildi!\n"
            f"📚 {data.get('title')}\n"
            f"📖 Modullar: {data.get('module_count', 0)}"
        )
