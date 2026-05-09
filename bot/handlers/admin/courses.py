from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.course_repo import CourseRepository
from bot.states.admin_states import CourseCreateState
from bot.keyboards.user_reply import cancel_keyboard
from bot.core.enums import AttachmentType, AttachmentStorage, CourseStatus

router = Router(name="admin_courses")


SKIP_TEXT = "⏭ O'tkazib yuborish"


class LessonAttachState(StatesGroup):
    waiting_file = State()
    waiting_link_url = State()
    waiting_link_title = State()


class SyllabusUploadState(StatesGroup):
    waiting_title = State()
    waiting_file = State()
    waiting_link_url = State()


@router.callback_query(F.data == "admin:courses")
async def admin_courses(callback: CallbackQuery, session: AsyncSession):
    repo = CourseRepository(session)
    courses = await repo.get_all(limit=50)

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi kurs", callback_data="admin:courses:create")
    builder.adjust(1)

    text = "📚 <b>Kurslar boshqaruvi</b>\n\n"
    for c in courses:
        status_icon = {
            CourseStatus.DRAFT: "📝",
            CourseStatus.PUBLISHED: "✅",
            CourseStatus.ARCHIVED: "📦",
        }.get(c.status, "❓")
        builder.row(
            InlineKeyboardButton(
                text=f"{status_icon} {c.title}",
                callback_data=f"admin:course:{c.id}",
            )
        )

    if not courses:
        text += "Kurslar yo'q."

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:course:"))
async def admin_course_view(callback: CallbackQuery, session: AsyncSession):
    course_id = int(callback.data.split(":")[-1])
    repo = CourseRepository(session)
    course = await repo.get_with_modules(course_id)
    if not course:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    text = (
        f"📚 <b>{course.title}</b>\n\n"
        f"{course.description or ''}\n\n"
        f"📊 Status: {course.status}\n"
        f"📖 Modullar: {len(course.modules)} | Darslar: {course.total_lessons}\n"
        f"📄 Sillabus: {'✅' if (course.syllabus_file_id or course.syllabus_url) else '—'}"
    )

    builder = InlineKeyboardBuilder()
    if course.status == CourseStatus.DRAFT:
        builder.button(
            text="🚀 E'lon qilish",
            callback_data=f"admin:course:publish:{course.id}",
        )
    elif course.status == CourseStatus.PUBLISHED:
        builder.button(
            text="📦 Arxivga olish",
            callback_data=f"admin:course:archive:{course.id}",
        )
    elif course.status == CourseStatus.ARCHIVED:
        builder.button(
            text="🚀 Qayta e'lon qilish",
            callback_data=f"admin:course:publish:{course.id}",
        )

    builder.button(
        text="📄 Sillabus yuklash",
        callback_data=f"admin:course:syllabus:{course.id}",
    )
    builder.button(
        text="📖 Modul/Dars qo'shish",
        callback_data=f"admin:course:addmod:{course.id}",
    )

    for m in course.modules:
        for lesson in m.lessons:
            builder.button(
                text=f"📎 {lesson.title} ({len(lesson.attachments)} mat.)",
                callback_data=f"admin:lesson:att:{lesson.id}",
            )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:courses"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:course:publish:"))
async def publish_course(callback: CallbackQuery, session: AsyncSession):
    course_id = int(callback.data.split(":")[-1])
    repo = CourseRepository(session)
    await repo.set_status(course_id, CourseStatus.PUBLISHED)
    await callback.answer("✅ Kurs e'lon qilindi.", show_alert=True)
    await admin_course_view(callback, session)


@router.callback_query(F.data.startswith("admin:course:archive:"))
async def archive_course(callback: CallbackQuery, session: AsyncSession):
    course_id = int(callback.data.split(":")[-1])
    repo = CourseRepository(session)
    await repo.set_status(course_id, CourseStatus.ARCHIVED)
    await callback.answer("📦 Kurs arxivlandi.", show_alert=True)
    await admin_course_view(callback, session)


# ───────────────── Sillabus yuklash ─────────────────


@router.callback_query(F.data.startswith("admin:course:syllabus:"))
async def syllabus_start(
    callback: CallbackQuery, state: FSMContext
):
    course_id = int(callback.data.split(":")[-1])
    await state.set_state(SyllabusUploadState.waiting_title)
    await state.update_data(course_id=course_id)
    await callback.message.answer(
        "📄 Sillabus nomini kiriting (yoki '-' qoldirish uchun):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SyllabusUploadState.waiting_title, F.text)
async def syllabus_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    title = message.text.strip()
    if title == "-":
        title = "Sillabus"
    await state.update_data(title=title)
    await state.set_state(SyllabusUploadState.waiting_file)
    await message.answer(
        "📤 Endi sillabus faylini yuboring (PDF/rasm/video/dokument)\n"
        "yoki tashqi havola bo'lsa /url kiriting."
    )


@router.message(SyllabusUploadState.waiting_file, F.text == "/url")
async def syllabus_url_prompt(message: Message, state: FSMContext):
    await state.set_state(SyllabusUploadState.waiting_link_url)
    await message.answer("🔗 Sillabus havolasini yuboring:")


@router.message(SyllabusUploadState.waiting_link_url, F.text)
async def syllabus_url_save(
    message: Message, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    repo = CourseRepository(session)
    await repo.set_syllabus(
        course_id=data["course_id"],
        title=data.get("title", "Sillabus"),
        file_type=AttachmentType.LINK,
        url=message.text.strip(),
    )
    await state.clear()
    await message.answer("✅ Sillabus saqlandi.")


@router.message(SyllabusUploadState.waiting_file)
async def syllabus_file_save(
    message: Message, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    file_id, file_type = _detect_file(message)
    if not file_id:
        await message.answer("❌ Fayl turini aniqlay olmadim. Qayta yuboring.")
        return

    repo = CourseRepository(session)
    await repo.set_syllabus(
        course_id=data["course_id"],
        title=data.get("title", "Sillabus"),
        file_type=file_type,
        file_id=file_id,
    )
    await state.clear()
    await message.answer("✅ Sillabus saqlandi.")


# ───────────────── Lesson attachments ─────────────────


@router.callback_query(F.data.startswith("admin:lesson:att:"))
async def lesson_attachments_view(
    callback: CallbackQuery, session: AsyncSession
):
    lesson_id = int(callback.data.split(":")[-1])
    repo = CourseRepository(session)
    lesson = await repo.get_lesson(lesson_id)
    if not lesson:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    text = f"📖 <b>{lesson.title}</b>\n\n📎 Materiallar: {len(lesson.attachments)}\n\n"
    for a in lesson.attachments:
        text += f"• [{a.file_type}] {a.title or '—'}\n"

    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Material qo'shish",
        callback_data=f"admin:lesson:addatt:{lesson_id}",
    )
    builder.button(
        text="🤖 AI savol generatsiya",
        callback_data=f"admin:lesson:aigen:{lesson_id}",
    )
    for a in lesson.attachments:
        builder.button(
            text=f"🗑 {a.title or a.file_type}",
            callback_data=f"admin:lesson:delatt:{a.id}:{lesson_id}",
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:courses"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:lesson:addatt:"))
async def lesson_addatt_start(
    callback: CallbackQuery, state: FSMContext
):
    lesson_id = int(callback.data.split(":")[-1])
    await state.set_state(LessonAttachState.waiting_file)
    await state.update_data(lesson_id=lesson_id)
    await callback.message.answer(
        "📤 Materialni yuboring (video/rasm/PDF/dokument/audio)\n"
        "yoki tashqi havola uchun /url kiriting.",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(LessonAttachState.waiting_file, F.text == "/url")
async def lesson_attach_url_prompt(message: Message, state: FSMContext):
    await state.set_state(LessonAttachState.waiting_link_url)
    await message.answer("🔗 Havolani yuboring:")


@router.message(LessonAttachState.waiting_link_url, F.text)
async def lesson_attach_url(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(url=message.text.strip())
    await state.set_state(LessonAttachState.waiting_link_title)
    await message.answer("📝 Material nomini kiriting (yoki '-'):")


@router.message(LessonAttachState.waiting_link_title, F.text)
async def lesson_attach_save_url(
    message: Message, state: FSMContext, session: AsyncSession
):
    data = await state.get_data()
    title = message.text.strip()
    if title == "-":
        title = None
    repo = CourseRepository(session)
    await repo.add_attachment(
        lesson_id=data["lesson_id"],
        file_type=AttachmentType.LINK,
        storage=AttachmentStorage.URL,
        title=title,
        url=data["url"],
    )
    await state.clear()
    await message.answer("✅ Material qo'shildi.")


@router.message(LessonAttachState.waiting_file)
async def lesson_attach_save_file(
    message: Message, state: FSMContext, session: AsyncSession
):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    data = await state.get_data()
    file_id, file_type = _detect_file(message)
    if not file_id:
        await message.answer("❌ Fayl turini aniqlay olmadim. Qayta yuboring.")
        return

    title = (
        message.caption.strip()
        if message.caption
        else (message.document.file_name if message.document else None)
    )

    repo = CourseRepository(session)
    await repo.add_attachment(
        lesson_id=data["lesson_id"],
        file_type=file_type,
        storage=AttachmentStorage.TELEGRAM,
        title=title,
        file_id=file_id,
        mime_type=getattr(message.document, "mime_type", None) if message.document else None,
        size_bytes=getattr(message.document, "file_size", None) if message.document else None,
    )
    await state.clear()
    await message.answer("✅ Material qo'shildi.")


@router.callback_query(F.data.startswith("admin:lesson:delatt:"))
async def lesson_delete_attachment(
    callback: CallbackQuery, session: AsyncSession
):
    parts = callback.data.split(":")
    attachment_id = int(parts[3])
    lesson_id = int(parts[4])

    repo = CourseRepository(session)
    await repo.delete_attachment(attachment_id)
    await callback.answer("🗑 O'chirildi.")
    callback.data = f"admin:lesson:att:{lesson_id}"
    await lesson_attachments_view(callback, session)


def _detect_file(message: Message) -> tuple[str | None, AttachmentType]:
    if message.video:
        return message.video.file_id, AttachmentType.VIDEO
    if message.audio:
        return message.audio.file_id, AttachmentType.AUDIO
    if message.voice:
        return message.voice.file_id, AttachmentType.AUDIO
    if message.photo:
        return message.photo[-1].file_id, AttachmentType.IMAGE
    if message.document:
        mime = (message.document.mime_type or "").lower()
        if "pdf" in mime:
            return message.document.file_id, AttachmentType.PDF
        if mime.startswith("image/"):
            return message.document.file_id, AttachmentType.IMAGE
        if mime.startswith("video/"):
            return message.document.file_id, AttachmentType.VIDEO
        if mime.startswith("audio/"):
            return message.document.file_id, AttachmentType.AUDIO
        return message.document.file_id, AttachmentType.DOCUMENT
    return None, AttachmentType.DOCUMENT


# ───────────────── Yangi kurs yaratish (Draft holatida) ─────────────────


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
    course = await repo.create(
        title=data["title"],
        description=desc,
        status=CourseStatus.DRAFT,
    )

    await state.update_data(course_id=course.id, description=desc)
    await state.set_state(CourseCreateState.waiting_module_title)
    await message.answer(
        f"✅ Kurs (qoralama) yaratildi: <b>{data['title']}</b>\n\n"
        "Endi modullar qo'shing.\n1-modul nomini kiriting:"
    )


@router.message(CourseCreateState.waiting_module_title, F.text)
async def module_title(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("✅ Kurs saqlandi (qoralama). Admin panelidan e'lon qiling.")
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
        await message.answer("✅ Kurs saqlandi (qoralama).")
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
    lesson = await repo.create_lesson(
        module_id=data["current_module_id"],
        title=data["lesson_title"],
        content=content,
        order=lesson_count + 1,
    )
    await state.update_data(lesson_count=lesson_count + 1, last_lesson_id=lesson.id)
    await state.set_state(CourseCreateState.confirm_add_more_lessons)
    await message.answer(
        "✅ Dars qo'shildi!\n\n"
        "Materiallarni keyinroq dars sozlamalaridan qo'shasiz.\n"
        "Yana dars qo'shasizmi? (ha/yo'q)"
    )


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
            f"✅ Kurs (qoralama) saqlandi!\n"
            f"📚 {data.get('title')}\n"
            f"📖 Modullar: {data.get('module_count', 0)}\n\n"
            f"⚠️ Foydalanuvchilarga ko'rinishi uchun admin panelidan <b>e'lon qiling</b>."
        )
