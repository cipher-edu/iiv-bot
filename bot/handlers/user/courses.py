from math import ceil

from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.course_repo import (
    CourseRepository,
    EnrollmentRepository,
    LessonRatingRepository,
)
from bot.repositories.rating_repo import RatingRepository
from bot.keyboards.inline import paginated_keyboard
from bot.keyboards.user_reply import back_keyboard
from bot.core.enums import (
    PointReason,
    AttachmentType,
    AttachmentStorage,
    CourseStatus,
)
from bot.config import settings

router = Router(name="courses")
router.message.filter(IsRegisteredFilter())


class LessonRateState(StatesGroup):
    waiting_stars = State()


def _stars_text(stars: int) -> str:
    return "⭐" * stars + "☆" * (5 - stars)


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
    total_pages = ceil(len(items) / settings.pagination_size) or 1
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
    if not course or course.status == CourseStatus.ARCHIVED:
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

    builder = InlineKeyboardBuilder()

    if course.syllabus_file_id or course.syllabus_url:
        builder.button(
            text="📄 Sillabus", callback_data=f"course:syllabus:{course_id}"
        )

    if not enrollment:
        prereqs = await course_repo.get_prerequisites(course_id)
        unmet = []
        for p in prereqs:
            req_enrollment = await enroll_repo.get_user_enrollment(
                db_user.id, p.required_course_id
            )
            if not req_enrollment or not req_enrollment.is_completed:
                unmet.append(p.required_course.title)
        if unmet:
            text += "\n🔒 <b>Talab qilingan kurslar:</b>\n" + "\n".join(
                f"  • {t}" for t in unmet
            )
        else:
            builder.button(text="📝 Yozilish", callback_data=f"course:enroll:{course_id}")
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


@router.callback_query(F.data.startswith("course:syllabus:"))
async def send_syllabus(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    course_id = int(callback.data.split(":")[-1])
    repo = CourseRepository(session)
    course = await repo.get_by_id(course_id)
    if not course or (not course.syllabus_file_id and not course.syllabus_url):
        await callback.answer("Sillabus topilmadi.", show_alert=True)
        return

    caption = f"📄 <b>{course.syllabus_title or course.title}</b>"

    try:
        if course.syllabus_file_id:
            ftype = course.syllabus_type
            if ftype == AttachmentType.IMAGE:
                await bot.send_photo(
                    callback.from_user.id, course.syllabus_file_id, caption=caption
                )
            elif ftype == AttachmentType.VIDEO:
                await bot.send_video(
                    callback.from_user.id, course.syllabus_file_id, caption=caption
                )
            elif ftype == AttachmentType.AUDIO:
                await bot.send_audio(
                    callback.from_user.id, course.syllabus_file_id, caption=caption
                )
            else:
                await bot.send_document(
                    callback.from_user.id, course.syllabus_file_id, caption=caption
                )
        else:
            await bot.send_message(
                callback.from_user.id,
                f"{caption}\n\n🔗 {course.syllabus_url}",
                disable_web_page_preview=False,
            )
        await callback.answer()
    except Exception:
        await callback.answer("Sillabusni yuborib bo'lmadi.", show_alert=True)


@router.callback_query(F.data.startswith("course:enroll:"))
async def enroll_course(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    course_id = int(callback.data.split(":")[-1])
    course_repo = CourseRepository(session)
    enroll_repo = EnrollmentRepository(session)

    existing = await enroll_repo.get_user_enrollment(db_user.id, course_id)
    if existing:
        await callback.answer("Siz allaqachon yozilgansiz!", show_alert=True)
        return

    prereqs = await course_repo.get_prerequisites(course_id)
    for p in prereqs:
        req_enrollment = await enroll_repo.get_user_enrollment(
            db_user.id, p.required_course_id
        )
        if not req_enrollment or not req_enrollment.is_completed:
            await callback.answer(
                f"🔒 Avval kurs '{p.required_course.title}' ni tugating.",
                show_alert=True,
            )
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


async def _send_attachment(bot: Bot, chat_id: int, attachment) -> None:
    file_type = attachment.file_type
    caption = attachment.title or ""
    try:
        if attachment.storage == AttachmentStorage.URL or attachment.url:
            await bot.send_message(
                chat_id, f"{caption}\n🔗 {attachment.url}".strip()
            )
            return

        file_ref = attachment.file_id
        if not file_ref:
            return
        if file_type == AttachmentType.VIDEO:
            await bot.send_video(chat_id, file_ref, caption=caption or None)
        elif file_type == AttachmentType.IMAGE:
            await bot.send_photo(chat_id, file_ref, caption=caption or None)
        elif file_type == AttachmentType.AUDIO:
            await bot.send_audio(chat_id, file_ref, caption=caption or None)
        else:
            await bot.send_document(chat_id, file_ref, caption=caption or None)
    except Exception:
        pass


@router.callback_query(F.data.startswith("course:lesson:"))
async def view_lesson(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    parts = callback.data.split(":")
    course_id = int(parts[2])
    enrollment_id = int(parts[3])
    lesson_id = int(parts[4])

    course_repo = CourseRepository(session)
    enroll_repo = EnrollmentRepository(session)
    rating_repo = LessonRatingRepository(session)

    lesson = await course_repo.get_lesson(lesson_id)
    if not lesson:
        await callback.answer("Dars topilmadi.", show_alert=True)
        return

    is_done = await enroll_repo.is_lesson_completed(enrollment_id, lesson_id)
    user_rating = await rating_repo.get_user_rating(lesson_id, db_user.id)
    avg, count = await rating_repo.get_lesson_stats(lesson_id)

    text = f"📖 <b>{lesson.title}</b>\n\n{lesson.content or 'Kontent mavjud emas.'}"
    if count > 0:
        text += f"\n\n⭐ O'rtacha baho: {avg:.1f} ({count} ovoz)"
    if user_rating:
        text += f"\n👤 Sizning bahoyingiz: {_stars_text(user_rating.stars)}"

    builder = InlineKeyboardBuilder()
    if lesson.attachments:
        builder.button(
            text=f"📎 Materiallar ({len(lesson.attachments)})",
            callback_data=f"course:materials:{course_id}:{enrollment_id}:{lesson_id}",
        )
    if not is_done:
        builder.button(
            text="✅ Tugatdim",
            callback_data=f"course:complete:{course_id}:{enrollment_id}:{lesson_id}",
        )
    elif lesson.require_rating and not user_rating:
        builder.button(
            text="⭐ Baholash",
            callback_data=f"course:rate:{course_id}:{enrollment_id}:{lesson_id}",
        )
    builder.button(
        text="🔖 Saqlash", callback_data=f"save:lesson:{lesson_id}"
    )
    builder.button(
        text="💬 Savol-Javob", callback_data=f"qa:list:{lesson_id}"
    )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga", callback_data=f"course:view:{course_id}"
        )
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("course:materials:"))
async def send_lesson_materials(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
):
    parts = callback.data.split(":")
    lesson_id = int(parts[4])

    repo = CourseRepository(session)
    lesson = await repo.get_lesson(lesson_id)
    if not lesson or not lesson.attachments:
        await callback.answer("Materiallar yo'q.", show_alert=True)
        return

    await callback.answer("📎 Materiallar yuborilmoqda...")
    for att in lesson.attachments:
        await _send_attachment(bot, callback.from_user.id, att)


@router.callback_query(F.data.startswith("course:complete:"))
async def complete_lesson(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    parts = callback.data.split(":")
    course_id = int(parts[2])
    enrollment_id = int(parts[3])
    lesson_id = int(parts[4])

    enroll_repo = EnrollmentRepository(session)
    rating_repo = LessonRatingRepository(session)
    course_repo = CourseRepository(session)

    is_done = await enroll_repo.is_lesson_completed(enrollment_id, lesson_id)
    if is_done:
        await callback.answer("Bu dars allaqachon tugatilgan.", show_alert=True)
        return

    await enroll_repo.complete_lesson(enrollment_id, lesson_id)

    try:
        from datetime import datetime, timedelta
        from bot.models.repetition import SpacedRepetition
        spaced = SpacedRepetition(
            user_id=db_user.id,
            lesson_id=lesson_id,
            interval_days=7,
            next_review_at=datetime.utcnow() + timedelta(days=7),
        )
        session.add(spaced)
        await session.flush()
    except Exception:
        pass

    lesson = await course_repo.get_lesson(lesson_id)
    user_rating = await rating_repo.get_user_rating(lesson_id, db_user.id)

    if lesson and lesson.require_rating and not user_rating:
        await state.set_state(LessonRateState.waiting_stars)
        await state.update_data(
            lesson_id=lesson_id,
            course_id=course_id,
            enrollment_id=enrollment_id,
        )

        builder = InlineKeyboardBuilder()
        for s in range(1, 6):
            builder.button(text=_stars_text(s), callback_data=f"rate:set:{s}")
        builder.adjust(1)

        await callback.message.answer(
            "⭐ <b>Iltimos, ushbu darsni baholang (majburiy):</b>\n\n"
            "Sizning bahoyingiz boshqalarga yordam beradi.",
            reply_markup=builder.as_markup(),
        )
        await callback.answer("✅ Dars tugatildi! Endi bahoni tanlang.")
        return

    enrollment = await enroll_repo.get_user_enrollment(db_user.id, course_id)
    progress = enrollment.get_progress_percent()
    if progress >= 100 and not enrollment.is_completed:
        await enroll_repo.mark_completed(enrollment_id)
        rating_total_repo = RatingRepository(session)
        await rating_total_repo.add_points(
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


@router.callback_query(F.data.startswith("course:rate:"))
async def rate_lesson_start(
    callback: CallbackQuery, state: FSMContext
):
    parts = callback.data.split(":")
    course_id = int(parts[2])
    enrollment_id = int(parts[3])
    lesson_id = int(parts[4])

    await state.set_state(LessonRateState.waiting_stars)
    await state.update_data(
        lesson_id=lesson_id,
        course_id=course_id,
        enrollment_id=enrollment_id,
    )

    builder = InlineKeyboardBuilder()
    for s in range(1, 6):
        builder.button(text=_stars_text(s), callback_data=f"rate:set:{s}")
    builder.adjust(1)

    await callback.message.answer(
        "⭐ Bahoni tanlang:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(LessonRateState.waiting_stars, F.data.startswith("rate:set:"))
async def rate_lesson_set(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    stars = int(callback.data.split(":")[-1])
    if stars < 1 or stars > 5:
        await callback.answer("Noto'g'ri baho.", show_alert=True)
        return

    data = await state.get_data()
    lesson_id = data["lesson_id"]
    course_id = data["course_id"]
    enrollment_id = data["enrollment_id"]

    rating_repo = LessonRatingRepository(session)
    await rating_repo.upsert_rating(lesson_id, db_user.id, stars)

    enroll_repo = EnrollmentRepository(session)
    enrollment = await enroll_repo.get_user_enrollment(db_user.id, course_id)
    progress = enrollment.get_progress_percent() if enrollment else 0

    if enrollment and progress >= 100 and not enrollment.is_completed:
        await enroll_repo.mark_completed(enrollment_id)
        rating_total_repo = RatingRepository(session)
        await rating_total_repo.add_points(
            db_user.id,
            settings.score_course_complete,
            PointReason.COURSE_COMPLETE,
            description=f"Kurs: {enrollment.course.title}",
            reference_id=course_id,
        )
        await callback.message.answer(
            f"🎉 Baho qabul qilindi: {_stars_text(stars)}\n\n"
            f"Kursni tugatdingiz! +{settings.score_course_complete} ball"
        )
    else:
        await callback.message.answer(
            f"✅ Baho qabul qilindi: {_stars_text(stars)}\nProgress: {progress}%"
        )

    await state.clear()
    await callback.answer()
