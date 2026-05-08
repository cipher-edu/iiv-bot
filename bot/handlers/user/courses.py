from math import ceil

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.course_repo import CourseRepository, EnrollmentRepository
from bot.repositories.rating_repo import RatingRepository
from bot.keyboards.inline import paginated_keyboard, course_modules_keyboard
from bot.keyboards.user_reply import back_keyboard, main_menu_keyboard
from bot.core.enums import PointReason
from bot.config import settings

router = Router(name="courses")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "📚 Kurslar")
async def show_courses(message: Message, session: AsyncSession, db_user: TelegramUser):
    repo = CourseRepository(session)
    courses = await repo.get_active_courses(limit=50)

    if not courses:
        await message.answer("Hozircha kurslar mavjud emas.", reply_markup=back_keyboard())
        return

    items = [
        (f"📚 {c.title} ({c.total_lessons} dars)", f"course:view:{c.id}")
        for c in courses
    ]
    total_pages = ceil(len(items) / settings.pagination_size)
    page_items = items[: settings.pagination_size]

    await message.answer(
        "📚 <b>Mavjud kurslar:</b>",
        reply_markup=paginated_keyboard(
            page_items, page=1, total_pages=total_pages, prefix="courses"
        ),
    )


@router.callback_query(F.data.startswith("course:view:"))
async def view_course(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    course_id = int(callback.data.split(":")[-1])
    course_repo = CourseRepository(session)
    enroll_repo = EnrollmentRepository(session)

    course = await course_repo.get_with_modules(course_id)
    if not course:
        await callback.answer("Kurs topilmadi.", show_alert=True)
        return

    enrollment = await enroll_repo.get_user_enrollment(db_user.id, course_id)
    progress = enrollment.get_progress_percent() if enrollment else 0

    text = (
        f"📚 <b>{course.title}</b>\n\n"
        f"{course.description or ''}\n\n"
        f"📊 Modullar: {len(course.modules)}\n"
        f"📖 Jami darslar: {course.total_lessons}\n"
    )

    if enrollment:
        text += f"📈 Progress: {progress}%\n"
        if enrollment.is_completed:
            text += "✅ Tugatilgan!\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    if not enrollment:
        builder.button(
            text="📝 Yozilish", callback_data=f"course:enroll:{course_id}"
        )
    else:
        for module in course.modules:
            builder.button(
                text=f"📖 {module.title}",
                callback_data=f"course:module:{course_id}:{module.id}",
            )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="courses:list"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("course:enroll:"))
async def enroll_course(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    course_id = int(callback.data.split(":")[-1])
    enroll_repo = EnrollmentRepository(session)

    existing = await enroll_repo.get_user_enrollment(db_user.id, course_id)
    if existing:
        await callback.answer("Siz allaqachon yozilgansiz!", show_alert=True)
        return

    await enroll_repo.enroll_user(db_user.id, course_id)
    await callback.answer("✅ Kursga muvaffaqiyatli yozildingiz!", show_alert=True)
    await view_course(callback, session, db_user)


@router.callback_query(F.data.startswith("course:module:"))
async def view_module(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    parts = callback.data.split(":")
    course_id = int(parts[2])
    module_id = int(parts[3])

    course_repo = CourseRepository(session)
    enroll_repo = EnrollmentRepository(session)

    course = await course_repo.get_with_modules(course_id)
    enrollment = await enroll_repo.get_user_enrollment(db_user.id, course_id)

    if not course or not enrollment:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    module = next((m for m in course.modules if m.id == module_id), None)
    if not module:
        await callback.answer("Modul topilmadi.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    completed_ids = {p.lesson_id for p in enrollment.progress}

    for lesson in module.lessons:
        icon = "✅" if lesson.id in completed_ids else "📖"
        builder.button(
            text=f"{icon} {lesson.title}",
            callback_data=f"course:lesson:{course_id}:{enrollment.id}:{lesson.id}",
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga", callback_data=f"course:view:{course_id}"
        )
    )

    await callback.message.edit_text(
        f"📖 <b>{module.title}</b>\n\nDarslarni tanlang:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("course:lesson:"))
async def view_lesson(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    parts = callback.data.split(":")
    course_id = int(parts[2])
    enrollment_id = int(parts[3])
    lesson_id = int(parts[4])

    course_repo = CourseRepository(session)
    enroll_repo = EnrollmentRepository(session)

    course = await course_repo.get_with_modules(course_id)
    lesson = None
    for module in course.modules:
        for l in module.lessons:
            if l.id == lesson_id:
                lesson = l
                break

    if not lesson:
        await callback.answer("Dars topilmadi.", show_alert=True)
        return

    is_done = await enroll_repo.is_lesson_completed(enrollment_id, lesson_id)

    text = f"📖 <b>{lesson.title}</b>\n\n{lesson.content or 'Kontent mavjud emas.'}"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    if not is_done:
        builder.button(
            text="✅ Tugatdim",
            callback_data=f"course:complete:{course_id}:{enrollment_id}:{lesson_id}",
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga", callback_data=f"course:view:{course_id}"
        )
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("course:complete:"))
async def complete_lesson(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    parts = callback.data.split(":")
    course_id = int(parts[2])
    enrollment_id = int(parts[3])
    lesson_id = int(parts[4])

    enroll_repo = EnrollmentRepository(session)
    rating_repo = RatingRepository(session)

    is_done = await enroll_repo.is_lesson_completed(enrollment_id, lesson_id)
    if is_done:
        await callback.answer("Bu dars allaqachon tugatilgan.", show_alert=True)
        return

    await enroll_repo.complete_lesson(enrollment_id, lesson_id)

    enrollment = await enroll_repo.get_user_enrollment(db_user.id, course_id)
    progress = enrollment.get_progress_percent()

    if progress >= 100 and not enrollment.is_completed:
        await enroll_repo.mark_completed(enrollment_id)
        await rating_repo.add_points(
            db_user.id,
            settings.score_course_complete,
            PointReason.COURSE_COMPLETE,
            description=f"Kurs: {enrollment.course.title}",
            reference_id=course_id,
        )
        await callback.answer(
            f"🎉 Kursni tugatdingiz! +{settings.score_course_complete} ball",
            show_alert=True,
        )
    else:
        await callback.answer(f"✅ Dars tugatildi! Progress: {progress}%", show_alert=True)

    await view_course(callback, session, db_user)
