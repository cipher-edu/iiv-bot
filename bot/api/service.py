"""Read and write helpers shared by the Web App API."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.config import settings
from bot.core.enums import (
    AuditAction,
    CourseStatus,
    PointReason,
    RegistrationStep,
    Role,
    UserCategory,
    UserStatus,
)
from bot.models.audit import AuditLog
from bot.models.certificate import Certificate
from bot.models.course import Course, CourseMaterial, CourseModule, Enrollment, Lesson, LessonProgress
from bot.models.gamification import Badge, UserBadge, UserStreak
from bot.models.rating import UserRating
from bot.models.test import AnswerOption, Question, Test, TestResult, TestSession, UserAnswer
from bot.models.user import TelegramUser
from bot.core.enums import TestSessionStatus
from bot.repositories.certificate_repo import CertificateRepository
from bot.repositories.course_repo import (
    CourseRepository,
    EnrollmentRepository,
    LessonRatingRepository,
)
from bot.repositories.gamification_repo import BadgeRepository
from bot.repositories.rating_repo import RatingRepository
from bot.repositories.test_repo import TestRepository, TestResultRepository
from bot.repositories.user_repo import UserRepository
from bot.services.streak_service import StreakService


def _naive(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def avatar_data_uri(name: str) -> str:
    letter = (name or "?").strip()[:1].upper() or "?"
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='80' height='80'>"
        f"<rect width='80' height='80' fill='#1d4ed8'/>"
        f"<text x='40' y='52' text-anchor='middle' font-size='36' "
        f"fill='white' font-family='sans-serif'>{letter}</text></svg>"
    )
    return "data:image/svg+xml," + quote(svg)


def web_role(user: TelegramUser) -> str:
    role = str(user.role)
    if role == Role.SUPERADMIN:
        return "superadmin"
    if role == Role.ADMIN:
        return "admin"
    if role == Role.MODERATOR:
        return "moderator"
    if str(user.category) == UserCategory.HODIM:
        return "officer"
    return "citizen"


def is_staff_role(role: str) -> bool:
    return role in {Role.ADMIN, Role.SUPERADMIN, Role.MODERATOR}


def is_superadmin_user(user: TelegramUser) -> bool:
    return str(user.role) == Role.SUPERADMIN or is_full_admin(user.telegram_id)


def is_full_admin(telegram_id: int) -> bool:
    return int(telegram_id) in set(settings.bot_superadmin_ids)


def promote_full_admin(user: TelegramUser) -> None:
    user.role = Role.SUPERADMIN
    user.status = UserStatus.ACTIVE
    user.registration_step = RegistrationStep.COMPLETED
    user.is_verified = True
    user.is_blocked = False
    user.blocked_until = None
    user.block_reason = None


def needs_category(user: TelegramUser) -> bool:
    if is_full_admin(user.telegram_id) or is_staff_role(str(user.role)):
        return False
    return not (user.is_registered and user.category)


def category_label(value: str) -> str:
    raw = (value or "").strip()
    if raw in {"", "beginner", "intermediate", "advanced"}:
        return "Umumiy"
    return raw


def _size_label(size_bytes: Optional[int]) -> Optional[str]:
    if not size_bytes:
        return None
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


async def audit(
    session: AsyncSession,
    user: TelegramUser,
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> None:
    session.add(
        AuditLog(
            user_id=user.id,
            telegram_id=user.telegram_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )
    await session.flush()


async def load_user(session: AsyncSession, user_id: int) -> Optional[TelegramUser]:
    stmt = (
        select(TelegramUser)
        .where(TelegramUser.id == user_id, TelegramUser.is_deleted == False)
        .options(selectinload(TelegramUser.organization))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def ensure_unblocked(session: AsyncSession, user: TelegramUser) -> bool:
    until = _naive(user.blocked_until)
    if user.is_blocked and until and until <= datetime.utcnow():
        user.is_blocked = False
        user.status = UserStatus.ACTIVE
        user.block_reason = None
        user.blocked_until = None
        await session.flush()
    return not user.is_blocked and str(user.status) != UserStatus.BLOCKED


async def user_profile(session: AsyncSession, user: TelegramUser) -> dict:
    rating = await RatingRepository(session).get_or_create(user.id)
    streak = await StreakService(session).get(user.id)
    completed = await EnrollmentRepository(session).count_completed(user.id)
    certs = await CertificateRepository(session).get_user_certificates(user.id, limit=100)
    place = await RatingRepository(session).get_user_rank(user.id)
    org = user.organization.name if user.organization else None
    return {
        "id": user.id,
        "telegramId": user.telegram_id,
        "fullName": user.display_name,
        "username": user.username,
        "phone": user.phone or "",
        "role": web_role(user),
        "organization": org,
        "position": user.position,
        "rank": user.position or "",
        "place": place or 0,
        "avatarUrl": avatar_data_uri(user.display_name),
        "streakDays": streak.current_streak or 0,
        "points": rating.total_points or 0,
        "completedCoursesCount": completed,
        "certificatesCount": len(certs),
        "isBanned": bool(user.is_blocked),
        "banUntil": user.blocked_until.isoformat() if user.blocked_until else None,
        "registered": user.is_registered,
        "category": str(user.category) if user.category else None,
    }


def lesson_dict(lesson: Lesson, done_ids: set[int]) -> dict:
    return {
        "id": str(lesson.id),
        "title": lesson.title,
        "order": lesson.order or 0,
        "durationMinutes": lesson.duration_minutes or 10,
        "content": lesson.content or "",
        "videoUrl": lesson.video_url,
        "isCompleted": lesson.id in done_ids,
        "attachments": [
            {
                "id": str(att.id),
                "title": att.title or "Material",
                "type": str(att.file_type) if str(att.file_type) in {"pdf", "video", "audio", "link"} else "pdf",
                "url": att.url or "",
                "size": _size_label(att.size_bytes),
            }
            for att in (lesson.attachments or [])
        ],
    }


def course_dict(
    course: Course,
    *,
    students: int = 0,
    rating: float = 0,
    reviews: int = 0,
    done_ids: Optional[set[int]] = None,
    progress: Optional[int] = None,
    with_content: bool = True,
) -> dict:
    done_ids = done_ids or set()
    modules = []
    lesson_count = 0
    for module in course.modules or []:
        lessons = []
        for lesson in module.lessons or []:
            lesson_count += 1
            if with_content:
                lessons.append(lesson_dict(lesson, done_ids))
            else:
                lessons.append({
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "order": lesson.order or 0,
                    "durationMinutes": lesson.duration_minutes or 10,
                    "content": "",
                    "isCompleted": lesson.id in done_ids,
                })
        modules.append({
            "id": str(module.id),
            "title": module.title,
            "order": module.order or 0,
            "lessons": lessons,
        })
    if progress is None and lesson_count:
        progress = int(len(done_ids) / lesson_count * 100)
    status = str(course.status or CourseStatus.PUBLISHED)
    if status not in {"published", "draft", "archived"}:
        status = "published"
    return {
        "id": str(course.id),
        "title": course.title,
        "category": category_label(str(course.difficulty or "")),
        "description": course.description or "",
        "coverImage": course.image_url or "",
        "instructor": course.syllabus_title or "IIV Akademiyasi",
        "syllabusFiles": [
            {
                "id": str(item.id),
                "title": item.title,
                "url": item.url,
                "type": item.file_type or "file",
            }
            for item in (course.materials or [])
            if not item.is_deleted
        ],
        "durationHours": course.estimated_hours or 0,
        "lessonsCount": lesson_count,
        "studentsCount": students,
        "rating": round(float(rating or 0), 1),
        "reviewsCount": reviews,
        "status": status,
        "progressPercentage": progress or 0,
        "modules": modules,
    }


async def _course_stats(session: AsyncSession) -> tuple[dict, dict, dict]:
    students_rows = (
        await session.execute(
            select(Enrollment.course_id, func.count(Enrollment.id))
            .where(Enrollment.is_deleted == False)
            .group_by(Enrollment.course_id)
        )
    ).all()
    students = {row[0]: row[1] for row in students_rows}

    from bot.models.course import LessonRating

    rating_rows = (
        await session.execute(
            select(
                CourseModule.course_id,
                func.avg(LessonRating.stars),
                func.count(LessonRating.id),
            )
            .join(Lesson, Lesson.module_id == CourseModule.id)
            .join(LessonRating, LessonRating.lesson_id == Lesson.id)
            .group_by(CourseModule.course_id)
        )
    ).all()
    ratings = {row[0]: row[1] for row in rating_rows}
    reviews = {row[0]: row[2] for row in rating_rows}
    return students, ratings, reviews


async def _done_map(session: AsyncSession, user_id: int) -> dict[int, set[int]]:
    rows = (
        await session.execute(
            select(Enrollment.course_id, LessonProgress.lesson_id)
            .join(LessonProgress, LessonProgress.enrollment_id == Enrollment.id)
            .where(
                Enrollment.user_id == user_id,
                Enrollment.is_deleted == False,
            )
        )
    ).all()
    grouped: dict[int, set[int]] = {}
    for course_id, lesson_id in rows:
        grouped.setdefault(course_id, set()).add(lesson_id)
    return grouped


async def list_courses(session: AsyncSession, user: TelegramUser, *, admin: bool = False) -> list[dict]:
    repo = CourseRepository(session)
    if admin:
        courses = await repo.get_all(limit=100, order_by=Course.order)
    else:
        courses = await repo.get_active_courses(limit=100)
    students, ratings, reviews = await _course_stats(session)
    done = await _done_map(session, user.id)
    return [
        course_dict(
            course,
            students=students.get(course.id, 0),
            rating=ratings.get(course.id, 0) or 0,
            reviews=reviews.get(course.id, 0) or 0,
            done_ids=done.get(course.id, set()),
            with_content=False,
        )
        for course in courses
    ]


async def get_course(session: AsyncSession, user: TelegramUser, course_id: int) -> Optional[dict]:
    course = await CourseRepository(session).get_with_modules(course_id)
    if not course:
        return None
    students, ratings, reviews = await _course_stats(session)
    done = await _done_map(session, user.id)
    return course_dict(
        course,
        students=students.get(course.id, 0),
        rating=ratings.get(course.id, 0) or 0,
        reviews=reviews.get(course.id, 0) or 0,
        done_ids=done.get(course.id, set()),
    )


async def complete_lesson(
    session: AsyncSession,
    user: TelegramUser,
    course_id: int,
    lesson_id: int,
    stars: int,
) -> dict:
    course = await CourseRepository(session).get_with_modules(course_id)
    if not course:
        raise ValueError("Kurs topilmadi")
    lesson_ids = {lesson.id for module in course.modules for lesson in module.lessons}
    if lesson_id not in lesson_ids:
        raise ValueError("Dars bu kursga tegishli emas")

    enrollments = EnrollmentRepository(session)
    enrollment = await enrollments.get_user_enrollment(user.id, course_id)
    if not enrollment:
        await enrollments.enroll_user(user.id, course_id)
        await session.flush()
        enrollment = await enrollments.get_user_enrollment(user.id, course_id)

    points = 0
    if not await enrollments.is_lesson_completed(enrollment.id, lesson_id):
        await enrollments.complete_lesson(enrollment.id, lesson_id)
        points = settings.score_participation
        await RatingRepository(session).add_points(
            user.id,
            points,
            PointReason.TEST_PARTICIPATION,
            description="Dars yakunlandi",
            reference_id=lesson_id,
        )

    if 1 <= stars <= 5:
        await LessonRatingRepository(session).upsert_rating(lesson_id, user.id, stars)

    await session.flush()
    done_count = (
        await session.execute(
            select(func.count(LessonProgress.id)).where(
                LessonProgress.enrollment_id == enrollment.id,
                LessonProgress.lesson_id.in_(lesson_ids),
            )
        )
    ).scalar_one()
    progress = int(done_count / len(lesson_ids) * 100) if lesson_ids else 0
    course_completed = False
    if progress >= 100 and enrollment and not enrollment.is_completed:
        await enrollments.mark_completed(enrollment.id)
        bonus = settings.score_course_complete
        points += bonus
        await RatingRepository(session).add_points(
            user.id,
            bonus,
            PointReason.COURSE_COMPLETE,
            description=course.title,
            reference_id=course.id,
        )
        course_completed = True
        if not await CertificateRepository(session).has_certificate(user.id, course.id):
            cert = await CertificateRepository(session).issue_certificate(
                user.id,
                course.id,
                title=course.title,
                score_percent=100,
            )
            cert.qr_code_data = cert.certificate_number

    await StreakService(session).record_activity(user.id)
    return {"pointsAwarded": points, "progress": progress, "courseCompleted": course_completed}


def test_summary(test: Test, best: Optional[int] = None, labels: Optional[dict] = None) -> dict:
    labels = labels or {}
    count = test.question_count
    minutes = max(1, round((test.time_per_question or 30) * max(count, 1) / 60))
    return {
        "id": str(test.id),
        "title": test.title,
        "description": test.description or "",
        "durationMinutes": minutes,
        "passPercentage": test.passing_score,
        "questionsCount": count,
        "totalAttemptsAllowed": test.max_attempts or 0,
        "userBestScore": best,
        "courseId": str(test.course_id or ""),
        "courseTitle": labels.get(("course", test.course_id), "") if test.course_id else "",
        "moduleTitle": labels.get(("module", test.module_id), "") if test.module_id else "",
        "lessonTitle": labels.get(("lesson", test.lesson_id), "") if test.lesson_id else "",
        "questions": [],
    }


async def _test_place_labels(session: AsyncSession, tests: list[Test]) -> dict:
    course_ids = {test.course_id for test in tests if test.course_id}
    module_ids = {test.module_id for test in tests if test.module_id}
    lesson_ids = {test.lesson_id for test in tests if test.lesson_id}
    labels: dict = {}
    if course_ids:
        rows = (
            await session.execute(select(Course.id, Course.title).where(Course.id.in_(course_ids)))
        ).all()
        labels.update({("course", row[0]): row[1] for row in rows})
    if module_ids:
        rows = (
            await session.execute(
                select(CourseModule.id, CourseModule.title).where(CourseModule.id.in_(module_ids))
            )
        ).all()
        labels.update({("module", row[0]): row[1] for row in rows})
    if lesson_ids:
        rows = (
            await session.execute(select(Lesson.id, Lesson.title).where(Lesson.id.in_(lesson_ids)))
        ).all()
        labels.update({("lesson", row[0]): row[1] for row in rows})
    return labels


async def _bind_test_target(session: AsyncSession, payload: dict) -> tuple[int, int, Optional[int]]:
    try:
        course_id = int(payload.get("courseId"))
        module_id = int(payload.get("moduleId"))
    except (TypeError, ValueError):
        raise ValueError("Kurs va modulni tanlang")
    scope = (payload.get("scope") or "lesson").strip()
    lesson_id = None
    if scope == "lesson":
        try:
            lesson_id = int(payload.get("lessonId"))
        except (TypeError, ValueError):
            raise ValueError("Darsni tanlang")
    elif scope != "module":
        raise ValueError("Test modul yoki darsga biriktiriladi")
    course = await session.get(Course, course_id)
    if not course or course.is_deleted:
        raise ValueError("Kurs topilmadi")
    module = await session.get(CourseModule, module_id)
    if not module or module.is_deleted or module.course_id != course_id:
        raise ValueError("Modul shu kursga tegishli emas")
    if lesson_id is not None:
        lesson = await session.get(Lesson, lesson_id)
        if not lesson or lesson.is_deleted or lesson.module_id != module_id:
            raise ValueError("Dars shu modulga tegishli emas")
    return course_id, module_id, lesson_id


def _clean_test_questions(raw: list) -> list[dict]:
    cleaned = []
    for item in raw or []:
        text = str(item.get("text") or "").strip()
        options = []
        for opt in item.get("options") or []:
            option_text = str(opt.get("text") or "").strip()
            if option_text:
                options.append({
                    "text": option_text[:1000],
                    "isCorrect": bool(opt.get("isCorrect")),
                })
        if len(text) < 3 or len(options) < 2:
            continue
        correct = [index for index, opt in enumerate(options) if opt["isCorrect"]]
        if len(correct) != 1:
            raise ValueError("Har bir savolda faqat bitta to'g'ri javob belgilang")
        cleaned.append({"text": text, "options": options})
    if not cleaned:
        raise ValueError("Kamida bitta to'liq savol kiriting")
    return cleaned


def test_player(test: Test, labels: Optional[dict] = None) -> dict:
    payload = test_summary(test, labels=labels)
    questions = []
    ordered = sorted(test.questions or [], key=lambda q: q.order or 0)
    for question in ordered:
        if not question.is_active:
            continue
        options = sorted(question.options or [], key=lambda o: o.order or 0)
        questions.append({
            "id": str(question.id),
            "text": question.text,
            "points": 1,
            "options": [{"id": str(opt.id), "text": opt.text, "isCorrect": False} for opt in options],
        })
    payload["questions"] = questions
    payload["questionsCount"] = len(questions)
    return payload


async def list_tests(session: AsyncSession, user: TelegramUser) -> list[dict]:
    tests = list(await TestRepository(session).get_active_tests(limit=100))
    labels = await _test_place_labels(session, tests)
    items = []
    for test in tests:
        best = await TestResultRepository(session).get_best_result(user.id, test.id)
        items.append(test_summary(test, best.score_percent if best else None, labels))
    return items


async def get_test(session: AsyncSession, test_id: int) -> Optional[dict]:
    test = await TestRepository(session).get_with_questions(test_id)
    if not test or not test.is_active:
        return None
    labels = await _test_place_labels(session, [test])
    return test_player(test, labels)


def _points_for_score(score: int) -> tuple[int, PointReason]:
    if score >= settings.score_excellent_threshold:
        return settings.score_excellent, PointReason.TEST_EXCELLENT
    if score >= settings.score_good_threshold:
        return settings.score_good, PointReason.TEST_GOOD
    if score >= settings.score_satisfactory_threshold:
        return settings.score_satisfactory, PointReason.TEST_SATISFACTORY
    return settings.score_participation, PointReason.TEST_PARTICIPATION


async def finish_test(session: AsyncSession, user: TelegramUser, test_id: int, answers: list[dict]) -> dict:
    test = await TestRepository(session).get_with_questions(test_id)
    if not test:
        raise ValueError("Test topilmadi")
    questions = [q for q in test.questions if q.is_active]
    if not questions:
        raise ValueError("Testda savol yo'q")

    chosen = {}
    for item in answers:
        try:
            chosen[int(item.get("questionId"))] = int(item.get("optionId"))
        except (TypeError, ValueError):
            continue

    correct = 0
    wrong = 0
    exam = TestSession(
        user_id=user.id,
        test_id=test.id,
        status=TestSessionStatus.FINISHED,
        question_order=[q.id for q in questions],
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        current_question_index=len(questions),
    )
    session.add(exam)
    await session.flush()

    for question in questions:
        option_ids = {opt.id: opt for opt in question.options}
        selected_id = chosen.get(question.id)
        selected = option_ids.get(selected_id) if selected_id else None
        is_ok = bool(selected and selected.is_correct)
        if is_ok:
            correct += 1
        else:
            wrong += 1
        session.add(
            UserAnswer(
                session_id=exam.id,
                question_id=question.id,
                selected_option_id=selected.id if selected else None,
                is_timeout=selected is None,
                answered_at=datetime.utcnow(),
            )
        )

    total = len(questions)
    score = round(correct / total * 100) if total else 0
    passed = score >= (test.passing_score or 0)
    points, reason = _points_for_score(score)
    result = TestResult(
        session_id=exam.id,
        user_id=user.id,
        test_id=test.id,
        correct_count=correct,
        wrong_count=wrong,
        timeout_count=0,
        total_questions=total,
        score_percent=score,
        is_passed=passed,
        points_awarded=points,
    )
    session.add(result)
    await RatingRepository(session).add_points(
        user.id, points, reason, description=test.title, reference_id=test.id
    )
    await RatingRepository(session).increment_tests(user.id, passed=passed)
    await StreakService(session).record_activity(user.id)
    return {
        "correctCount": correct,
        "percentage": score,
        "isPassed": passed,
        "pointsAwarded": points,
        "total": total,
    }


async def leaderboard(session: AsyncSession, limit: int = 20) -> list[dict]:
    ratings = await RatingRepository(session).get_leaderboard(limit=limit)
    if not ratings:
        return []
    user_ids = [row.user_id for row in ratings]
    users = (
        await session.execute(
            select(TelegramUser)
            .where(TelegramUser.id.in_(user_ids))
            .options(selectinload(TelegramUser.organization))
        )
    ).scalars().all()
    by_id = {u.id: u for u in users}
    streaks = (
        await session.execute(select(UserStreak).where(UserStreak.user_id.in_(user_ids)))
    ).scalars().all()
    streak_map = {s.user_id: s.current_streak for s in streaks}
    items = []
    for index, row in enumerate(ratings, start=1):
        person = by_id.get(row.user_id)
        name = person.display_name if person else f"#{row.user_id}"
        items.append({
            "rank": index,
            "id": row.user_id,
            "fullName": name,
            "organization": person.organization.name if person and person.organization else None,
            "points": row.total_points or 0,
            "streakDays": streak_map.get(row.user_id, 0) or 0,
            "avatarUrl": avatar_data_uri(name),
        })
    return items


async def badges_for(session: AsyncSession, user_id: int) -> list[dict]:
    catalog = (
        await session.execute(select(Badge).where(Badge.is_active == True, Badge.is_deleted == False))
    ).scalars().all()
    owned = await BadgeRepository(session).get_user_badges(user_id)
    owned_ids = {item.badge_id: item for item in owned}
    if not catalog and owned:
        catalog = [item.badge for item in owned if item.badge]
    return [
        {
            "id": str(badge.id),
            "name": badge.name,
            "description": badge.description,
            "icon": badge.icon or "🏅",
            "isUnlocked": badge.id in owned_ids,
            "unlockedAt": owned_ids[badge.id].earned_at.isoformat() if badge.id in owned_ids else None,
        }
        for badge in catalog
    ]


async def certificates_for(session: AsyncSession, user: TelegramUser) -> list[dict]:
    rows = await CertificateRepository(session).get_user_certificates(user.id, limit=50)
    course_ids = [row.course_id for row in rows if row.course_id]
    titles = {}
    if course_ids:
        found = (
            await session.execute(select(Course).where(Course.id.in_(course_ids)))
        ).scalars().all()
        titles = {c.id: c.title for c in found}
    return [
        {
            "id": str(row.id),
            "certificateNumber": row.certificate_number,
            "courseId": str(row.course_id or ""),
            "courseTitle": titles.get(row.course_id, row.title),
            "issueDate": row.issued_date.isoformat() if row.issued_date else "",
            "studentName": user.display_name,
            "organization": user.organization.name if user.organization else None,
            "scorePercentage": row.score_percent or 0,
            "qrCodeUrl": row.qr_code_data or row.certificate_number,
        }
        for row in rows
    ]


async def touch_user(session: AsyncSession, user: TelegramUser) -> None:
    await StreakService(session).record_activity(user.id)
    await UserRepository(session).update_activity(user.id)


async def upsert_from_telegram(session: AsyncSession, tg_user: dict) -> TelegramUser:
    telegram_id = int(tg_user["id"])
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)
    first = (tg_user.get("first_name") or "").strip()
    last = (tg_user.get("last_name") or "").strip()
    full_name = (f"{first} {last}").strip() or None
    username = tg_user.get("username")
    if not user:
        user = await repo.create_user(telegram_id, username)
    if full_name and not user.full_name:
        user.full_name = full_name
    if username:
        user.username = username
    if is_full_admin(telegram_id):
        promote_full_admin(user)
    await session.flush()
    loaded = await load_user(session, user.id)
    return loaded or user


async def account_on_start(session: AsyncSession, tg_user: dict) -> tuple[TelegramUser, str]:
    """Return the user and 'ready' or 'choose'. Existing category and role stay."""
    user = await upsert_from_telegram(session, tg_user)
    return user, "choose" if needs_category(user) else "ready"


_LOGIN_RE = re.compile(r"^[a-z0-9._]{3,32}$")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored or not stored.startswith("pbkdf2$"):
        return False
    try:
        _, salt, digest = stored.split("$", 2)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return hmac.compare_digest(check, digest)


def _clean_login(login: str) -> str:
    return (login or "").strip().lower()


async def find_by_login(session: AsyncSession, login: str) -> Optional[TelegramUser]:
    cleaned = _clean_login(login)
    if not cleaned:
        return None
    stmt = select(TelegramUser).where(
        TelegramUser.login == cleaned,
        TelegramUser.is_deleted == False,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def register_account(
    session: AsyncSession,
    *,
    full_name: str,
    phone: str,
    category: str,
    login: str,
    password: str,
    position: Optional[str] = None,
    telegram_user: Optional[dict] = None,
) -> TelegramUser:
    name = (full_name or "").strip()
    if len(name) < 3:
        raise ValueError("Ism-familiya kamida 3 ta belgi bo'lsin")
    cleaned_login = _clean_login(login)
    if not _LOGIN_RE.match(cleaned_login):
        raise ValueError("Login 3-32 belgi: lotin harfi, raqam, nuqta yoki pastki chiziq")
    if len(password or "") < 6:
        raise ValueError("Parol kamida 6 ta belgi bo'lsin")
    if category not in {"hodim", "fuqaro"}:
        raise ValueError("Toifa hodim yoki fuqaro bo'lishi kerak")
    phone_clean = (phone or "").strip()[:20]
    digits = phone_clean.replace("+", "").replace(" ", "").replace("-", "")
    if not digits.isdigit() or len(digits) < 9:
        raise ValueError("Telefon raqamni to'g'ri kiriting")
    if await find_by_login(session, cleaned_login):
        raise ValueError("Bu login band. Boshqa login tanlang")

    chosen = UserCategory.HODIM if category == "hodim" else UserCategory.FUQARO
    repo = UserRepository(session)
    user = None
    if telegram_user and telegram_user.get("id"):
        user = await upsert_from_telegram(session, telegram_user)
        if is_full_admin(user.telegram_id) or (user.is_registered and user.category):
            raise ValueError("Bu Telegram allaqachon ro'yxatdan o'tgan")
    if user is None:
        telegram_id = -int(uuid.uuid4().int % 9_000_000_000_000) - 1
        user = await repo.create_user(telegram_id, None)

    user.full_name = name
    user.phone = phone_clean
    user.category = chosen
    user.login = cleaned_login
    user.password_hash = hash_password(password)
    user.registration_step = RegistrationStep.COMPLETED
    user.status = UserStatus.ACTIVE
    user.is_verified = True
    if chosen == UserCategory.HODIM:
        user.position = (position or "").strip()[:255] or None
    else:
        user.position = None
        user.staff_role = None
        user.organization_id = None
    await session.flush()
    loaded = await load_user(session, user.id)
    return loaded or user


async def login_with_password(
    session: AsyncSession,
    login: str,
    password: str,
    telegram_user: Optional[dict] = None,
) -> TelegramUser:
    user = await find_by_login(session, login)
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Login yoki parol noto'g'ri")
    if user.is_blocked:
        raise ValueError("Hisob bloklangan")
    if telegram_user and telegram_user.get("id"):
        telegram_id = int(telegram_user["id"])
        current = await UserRepository(session).get_by_telegram_id(telegram_id)
        if current and current.id != user.id:
            if current.is_registered and (current.category or is_staff_role(str(current.role))):
                raise ValueError("Bu Telegram boshqa hisobga bog'langan")
            current.telegram_id = -int(current.id) - 10_000_000_000
            current.is_deleted = True
            await session.flush()
        user.telegram_id = telegram_id
        username = telegram_user.get("username")
        if username and not user.username:
            user.username = username
    await session.flush()
    loaded = await load_user(session, user.id)
    return loaded or user


async def finish_with_category(
    session: AsyncSession, user: TelegramUser, category: str
) -> TelegramUser:
    if is_full_admin(user.telegram_id):
        promote_full_admin(user)
    elif user.is_registered and user.category:
        pass
    else:
        chosen = UserCategory.HODIM if category == "hodim" else UserCategory.FUQARO
        user.category = chosen
        user.registration_step = RegistrationStep.COMPLETED
        user.status = UserStatus.ACTIVE
        user.is_verified = True
        if chosen == UserCategory.FUQARO:
            user.staff_role = None
            user.organization_id = None
            user.position = None
    await session.flush()
    loaded = await load_user(session, user.id)
    return loaded or user


async def create_local_user(
    session: AsyncSession, full_name: str, phone: str, category: str
) -> TelegramUser:
    repo = UserRepository(session)
    phone_clean = (phone or "").strip()[:20] or None
    chosen = UserCategory.HODIM if category == "hodim" else UserCategory.FUQARO
    existing = None
    if phone_clean:
        existing = (
            await session.execute(
                select(TelegramUser)
                .where(
                    TelegramUser.phone == phone_clean,
                    TelegramUser.telegram_id < 0,
                    TelegramUser.is_deleted == False,
                )
                .order_by(TelegramUser.id.desc())
                .limit(1)
            )
        ).scalars().first()
    if existing:
        existing.full_name = full_name.strip()
        existing.category = chosen
        existing.registration_step = RegistrationStep.COMPLETED
        existing.status = UserStatus.ACTIVE
        existing.is_verified = True
        await session.flush()
        loaded = await load_user(session, existing.id)
        return loaded or existing

    telegram_id = -int(uuid.uuid4().int % 9_000_000_000_000) - 1
    user = await repo.create_user(telegram_id, None)
    user.full_name = full_name.strip()
    user.phone = phone_clean
    user.category = chosen
    user.registration_step = RegistrationStep.COMPLETED
    user.status = UserStatus.ACTIVE
    user.is_verified = True
    await session.flush()
    loaded = await load_user(session, user.id)
    return loaded or user


def _role_label(user: TelegramUser) -> str:
    role = web_role(user)
    labels = {
        "citizen": "Fuqaro",
        "officer": "Xodim",
        "moderator": "Moderator",
        "admin": "Administrator",
        "superadmin": "Superadmin",
    }
    return labels.get(role, role)


async def admin_users(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(TelegramUser)
            .where(TelegramUser.is_deleted == False)
            .options(selectinload(TelegramUser.organization))
            .order_by(TelegramUser.created_at.desc())
            .limit(300)
        )
    ).scalars().all()
    if not rows:
        return []
    ids = [row.id for row in rows]
    ratings = (
        await session.execute(select(UserRating).where(UserRating.user_id.in_(ids)))
    ).scalars().all()
    points = {item.user_id: item.total_points for item in ratings}
    return [
        {
            "id": row.id,
            "telegramId": row.telegram_id,
            "fullName": row.display_name,
            "phone": row.phone or "",
            "role": web_role(row),
            "organization": row.organization.name if row.organization else "—",
            "rank": row.position or "",
            "points": points.get(row.id, 0) or 0,
            "isBanned": bool(row.is_blocked),
            "banReason": row.block_reason,
        }
        for row in rows
    ]


async def set_web_role(session: AsyncSession, actor: TelegramUser, user_id: int, role: str) -> None:
    target = await load_user(session, user_id)
    if not target:
        raise ValueError("Foydalanuvchi topilmadi")
    if role == "superadmin" and str(actor.role) != Role.SUPERADMIN:
        raise PermissionError("Superadmin rolini faqat superadmin beradi")
    if role == "citizen":
        target.role = Role.USER
        target.category = UserCategory.FUQARO
    elif role == "officer":
        target.role = Role.USER
        target.category = UserCategory.HODIM
    elif role == "moderator":
        target.role = Role.MODERATOR
    elif role == "admin":
        target.role = Role.ADMIN
    elif role == "superadmin":
        target.role = Role.SUPERADMIN
    else:
        raise ValueError("Noma'lum rol")
    await session.flush()
    await audit(session, actor, AuditAction.ROLE_CHANGE, "user", target.id, {"role": role})


_BAN_HOURS = {
    "1 soat": 1,
    "1 kun": 24,
    "7 kun": 24 * 7,
    "30 kun": 24 * 30,
}


async def block_web_user(
    session: AsyncSession, actor: TelegramUser, user_id: int, duration: str, reason: str
) -> None:
    target = await load_user(session, user_id)
    if not target:
        raise ValueError("Foydalanuvchi topilmadi")
    hours = _BAN_HOURS.get(duration)
    until = datetime.utcnow() + timedelta(hours=hours) if hours else None
    text = f"{duration}: {reason}".strip(": ")
    await UserRepository(session).block_user(target.id, text, blocked_until=until)
    await audit(session, actor, AuditAction.BLOCK, "user", target.id, {"reason": text})
    if target.telegram_id and target.telegram_id > 0 and settings.bot_token:
        await _telegram_message(
            target.telegram_id,
            f"Hisobingiz bloklandi.\nSabab: {text}",
        )


async def unblock_web_user(session: AsyncSession, actor: TelegramUser, user_id: int) -> None:
    target = await load_user(session, user_id)
    if not target:
        raise ValueError("Foydalanuvchi topilmadi")
    await UserRepository(session).unblock_user(target.id)
    await audit(session, actor, AuditAction.UNBLOCK, "user", target.id, {})


async def admin_overview(session: AsyncSession) -> dict:
    total = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(TelegramUser.is_deleted == False)
        )
    ).scalar_one()
    today = datetime.utcnow().date()
    active_today = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(
                TelegramUser.is_deleted == False,
                func.date(TelegramUser.last_activity) == today,
            )
        )
    ).scalar_one()
    enrolled = (
        await session.execute(
            select(func.count(Enrollment.id)).where(Enrollment.is_deleted == False)
        )
    ).scalar_one()
    finished = (
        await session.execute(
            select(func.count(Enrollment.id)).where(
                Enrollment.is_deleted == False, Enrollment.is_completed == True
            )
        )
    ).scalar_one()
    avg_score = (
        await session.execute(select(func.avg(TestResult.score_percent)))
    ).scalar_one()
    courses = await list_courses_admin_brief(session)
    recent_rows = (
        await session.execute(
            select(TelegramUser)
            .where(TelegramUser.is_deleted == False)
            .options(selectinload(TelegramUser.organization))
            .order_by(TelegramUser.created_at.desc())
            .limit(8)
        )
    ).scalars().all()
    recent = [
        {
            "id": row.id,
            "name": row.display_name,
            "role": _role_label(row),
            "org": row.organization.name if row.organization else "—",
            "date": _human_time(row.created_at),
        }
        for row in recent_rows
    ]
    dropoff = [
        {
            "title": course["title"],
            "note": f"{max(0, 100 - int(course['progressPercentage']))}% o'rtacha qolgan qism, {course['studentsCount']} o'quvchi",
        }
        for course in courses
        if course["studentsCount"] and course["progressPercentage"] < 100
    ][:3]
    return {
        "usersTotal": total or 0,
        "activeToday": active_today or 0,
        "completionRate": round((finished / enrolled) * 100, 1) if enrolled else 0,
        "avgScore": round(float(avg_score or 0), 1),
        "courses": courses,
        "recentUsers": recent,
        "dropoff": dropoff,
    }


async def list_courses_admin_brief(session: AsyncSession) -> list[dict]:
    courses = await CourseRepository(session).get_all(limit=100, order_by=Course.order)
    students, ratings, reviews = await _course_stats(session)
    completed_rows = (
        await session.execute(
            select(Enrollment.course_id, func.count(Enrollment.id))
            .where(Enrollment.is_deleted == False, Enrollment.is_completed == True)
            .group_by(Enrollment.course_id)
        )
    ).all()
    completed = {row[0]: row[1] for row in completed_rows}
    items = []
    for course in courses:
        count = students.get(course.id, 0)
        finished = completed.get(course.id, 0)
        percent = int(finished / count * 100) if count else 0
        items.append(
            course_dict(
                course,
                students=count,
                rating=ratings.get(course.id, 0) or 0,
                reviews=reviews.get(course.id, 0) or 0,
                progress=percent,
                with_content=False,
            )
        )
    return items


def _human_time(value: Optional[datetime]) -> str:
    moment = _naive(value)
    if not moment:
        return "—"
    delta = datetime.utcnow() - moment
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "hozir"
    if minutes < 60:
        return f"{minutes} daqiqa oldin"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} soat oldin"
    return moment.strftime("%d.%m.%Y")


async def create_course(session: AsyncSession, actor: TelegramUser, payload: dict) -> dict:
    title = (payload.get("title") or "").strip()
    if len(title) < 3:
        raise ValueError("Kurs nomi juda qisqa")
    status = payload.get("status") or CourseStatus.DRAFT
    if status not in {CourseStatus.DRAFT, CourseStatus.PUBLISHED, "draft", "published"}:
        status = CourseStatus.DRAFT
    course = Course(
        title=title,
        description=(payload.get("description") or "").strip() or None,
        image_url=(payload.get("coverUrl") or "").strip() or None,
        estimated_hours=int(payload.get("durationHours") or 0) or None,
        difficulty=((payload.get("category") or "Umumiy").strip() or "Umumiy")[:120],
        syllabus_title=(payload.get("instructor") or "").strip() or None,
        status=status,
        is_active=status == CourseStatus.PUBLISHED or status == "published",
    )
    session.add(course)
    await session.flush()
    for m_index, module in enumerate(payload.get("modules") or []):
        row = CourseModule(
            course_id=course.id,
            title=(module.get("title") or f"{m_index + 1}-modul").strip(),
            order=m_index,
        )
        session.add(row)
        await session.flush()
        for l_index, lesson in enumerate(module.get("lessons") or []):
            session.add(
                Lesson(
                    module_id=row.id,
                    title=(lesson.get("title") or f"Dars {l_index + 1}").strip(),
                    content=lesson.get("content") or "",
                    video_url=(lesson.get("videoUrl") or "").strip() or None,
                    duration_minutes=int(lesson.get("duration") or 10),
                    order=l_index,
                )
            )
    for f_index, item in enumerate(payload.get("syllabusFiles") or []):
        url = (item.get("url") or "").strip()
        if not url.startswith("/uploads/"):
            continue
        session.add(
            CourseMaterial(
                course_id=course.id,
                title=(item.get("title") or f"Silabus {f_index + 1}")[:255],
                url=url[:1000],
                file_type=(item.get("type") or "file")[:20],
                order=f_index,
            )
        )
    await session.flush()
    await audit(session, actor, AuditAction.CREATE, "course", course.id, {"title": title})
    fresh = await CourseRepository(session).get_with_modules(course.id)
    return course_dict(fresh)


async def delete_course(session: AsyncSession, actor: TelegramUser, course_id: int) -> None:
    ok = await CourseRepository(session).soft_delete(course_id)
    if not ok:
        raise ValueError("Kurs topilmadi")
    await audit(session, actor, AuditAction.DELETE, "course", course_id, {})


async def delete_test(session: AsyncSession, actor: TelegramUser, test_id: int) -> None:
    ok = await TestRepository(session).soft_delete(test_id)
    if not ok:
        raise ValueError("Test topilmadi")
    await audit(session, actor, AuditAction.DELETE, "test", test_id, {})


def _template_questions(text: str) -> list[dict]:
    chunks = [part.strip() for part in re.split(r"[.\n]", text) if len(part.strip()) > 20][:3]
    if not chunks:
        chunks = [text.strip()[:180] or "Dars matni"]
    questions = []
    decoys = [
        "Bu fikr dars matnida yo'q",
        "Faqat tashqi manbadan olingan taxmin",
        "Savol darsga aloqador emas",
    ]
    for chunk in chunks:
        questions.append({
            "text": "Qaysi mulohaza dars matniga mos?",
            "options": [
                {"text": chunk[:240], "isCorrect": True},
                {"text": decoys[0], "isCorrect": False},
                {"text": decoys[1], "isCorrect": False},
            ],
        })
    return questions


def _parse_questions(raw: str) -> Optional[list[dict]]:
    match = re.search(r"\[[\s\S]*\]", raw or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    cleaned = []
    for item in data:
        options = item.get("options") or []
        if not item.get("text") or len(options) < 2:
            continue
        cleaned.append({
            "text": str(item["text"]),
            "options": [
                {"text": str(opt.get("text") or ""), "isCorrect": bool(opt.get("isCorrect"))}
                for opt in options
                if opt.get("text")
            ],
        })
    return cleaned or None


async def generate_questions(session: AsyncSession, user: TelegramUser, text: str) -> dict:
    source = "template"
    questions = None
    if settings.ai_enabled and (settings.anthropic_api_key or settings.openai_api_key):
        from bot.services.ai_service import AIService

        prompt = (
            "Quyidagi dars matnidan 3 ta o'zbekcha test savoli tuz. "
            "Faqat JSON massiv qaytar: "
            "[{\"text\":\"savol\",\"options\":[{\"text\":\"variant\",\"isCorrect\":true}]}]. "
            "Har savolda 3 ta variant bo'lsin va faqat bittasi to'g'ri bo'lsin.\n\n"
            + text[:4000]
        )
        raw = await AIService(session).chat(user.id, prompt)
        questions = _parse_questions(raw)
        if questions:
            source = "ai"
    if not questions:
        questions = _template_questions(text)
    return {"questions": questions, "source": source}


async def save_generated_test(session: AsyncSession, actor: TelegramUser, payload: dict) -> dict:
    title = (payload.get("title") or "").strip()
    if len(title) < 3:
        raise ValueError("Test nomi kamida 3 ta belgi bo'lsin")
    questions = _clean_test_questions(payload.get("questions") or [])
    course_id, module_id, lesson_id = await _bind_test_target(session, payload)
    try:
        passing = int(payload.get("passPercentage") or 70)
        attempts = int(payload.get("totalAttemptsAllowed") or 3)
    except (TypeError, ValueError):
        raise ValueError("O'tish bali yoki urinishlar soni noto'g'ri")
    if passing < 0 or passing > 100:
        raise ValueError("O'tish bali 0 dan 100 gacha bo'lsin")
    if attempts < 1:
        raise ValueError("Urinishlar soni kamida 1 bo'lsin")
    test = Test(
        title=title,
        description=(payload.get("description") or "").strip() or None,
        time_per_question=30,
        passing_score=passing,
        is_active=True,
        max_attempts=attempts,
        course_id=course_id,
        module_id=module_id,
        lesson_id=lesson_id,
    )
    session.add(test)
    await session.flush()
    for index, item in enumerate(questions):
        question = Question(
            test_id=test.id,
            text=str(item.get("text") or f"Savol {index + 1}"),
            order=index,
            is_active=True,
        )
        session.add(question)
        await session.flush()
        for opt_index, opt in enumerate(item.get("options") or []):
            session.add(
                AnswerOption(
                    question_id=question.id,
                    text=str(opt.get("text") or "—"),
                    is_correct=bool(opt.get("isCorrect")),
                    order=opt_index,
                )
            )
    await session.flush()
    await audit(session, actor, AuditAction.CREATE, "test", test.id, {"title": title})
    fresh = await TestRepository(session).get_with_questions(test.id)
    saved = fresh or test
    labels = await _test_place_labels(session, [saved])
    return test_summary(saved, labels=labels)


async def audience_counts(session: AsyncSession) -> dict:
    base = TelegramUser.is_deleted == False
    all_count = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(base, TelegramUser.telegram_id > 0)
        )
    ).scalar_one()
    officers = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(
                base, TelegramUser.telegram_id > 0, TelegramUser.category == UserCategory.HODIM
            )
        )
    ).scalar_one()
    citizens = (
        await session.execute(
            select(func.count(TelegramUser.id)).where(
                base, TelegramUser.telegram_id > 0, TelegramUser.category == UserCategory.FUQARO
            )
        )
    ).scalar_one()
    active = (
        await session.execute(
            select(func.count(UserStreak.id))
            .join(TelegramUser, TelegramUser.id == UserStreak.user_id)
            .where(UserStreak.current_streak >= 5, TelegramUser.telegram_id > 0)
        )
    ).scalar_one()
    return {
        "all": all_count or 0,
        "officers": officers or 0,
        "citizens": citizens or 0,
        "active_streak": active or 0,
    }


async def _segment_ids(session: AsyncSession, segment: str) -> list[int]:
    stmt = select(TelegramUser.telegram_id).where(
        TelegramUser.is_deleted == False,
        TelegramUser.telegram_id > 0,
        TelegramUser.is_blocked == False,
    )
    if segment == "officers":
        stmt = stmt.where(TelegramUser.category == UserCategory.HODIM)
    elif segment == "citizens":
        stmt = stmt.where(TelegramUser.category == UserCategory.FUQARO)
    elif segment == "active_streak":
        stmt = stmt.join(UserStreak, UserStreak.user_id == TelegramUser.id).where(
            UserStreak.current_streak >= 5
        )
    rows = (await session.execute(stmt.limit(300))).scalars().all()
    return list(rows)


async def _telegram_message(chat_id: int, text: str, button_text: str = "", button_url: str = "") -> None:
    import aiohttp

    payload: dict = {"chat_id": chat_id, "text": text[:4000]}
    if button_text and button_url:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": button_text[:64], "url": button_url}]]
        }
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as http:
        async with http.post(url, json=payload) as response:
            if response.status >= 400:
                body = await response.text()
                raise RuntimeError(body[:200])


async def send_broadcast(session: AsyncSession, actor: TelegramUser, payload: dict) -> dict:
    text = (payload.get("message") or "").strip()
    if len(text) < 2:
        raise ValueError("Xabar matni bo'sh")
    if not settings.bot_token:
        raise ValueError("Bot token sozlanmagan")
    ids = await _segment_ids(session, payload.get("segment") or "all")
    sent = 0
    failed = 0
    import asyncio

    for chat_id in ids:
        try:
            await _telegram_message(
                chat_id,
                text,
                payload.get("buttonText") or "",
                payload.get("buttonUrl") or "",
            )
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await audit(
        session,
        actor,
        AuditAction.BROADCAST,
        "broadcast",
        None,
        {"segment": payload.get("segment"), "sent": sent, "failed": failed},
    )
    return {"sent": sent, "failed": failed, "targeted": len(ids)}


_ACTION_LABELS = {
    "login": "Kirish",
    "logout": "Chiqish",
    "create": "Yaratildi",
    "update": "Yangilandi",
    "delete": "O'chirildi",
    "block": "Bloklandi",
    "unblock": "Blokdan chiqarildi",
    "role_change": "Rol o'zgartirildi",
    "broadcast": "Xabarnoma yuborildi",
    "export": "Eksport",
    "backup": "Zaxira",
    "settings_change": "Sozlama",
    "failed_auth": "Muvaffaqiyatsiz kirish",
}


async def audit_feed(session: AsyncSession) -> dict:
    rows = (
        await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(40))
    ).scalars().all()
    user_ids = {row.user_id for row in rows if row.user_id}
    names = {}
    if user_ids:
        people = (
            await session.execute(select(TelegramUser).where(TelegramUser.id.in_(user_ids)))
        ).scalars().all()
        names = {person.id: person.display_name for person in people}
    events = []
    for row in rows:
        action = str(row.action)
        events.append({
            "id": row.id,
            "action": _ACTION_LABELS.get(action, action),
            "actor": names.get(row.user_id, "Tizim"),
            "details": json.dumps(row.details, ensure_ascii=False) if row.details else (row.entity_type or ""),
            "ip": row.ip_address or "—",
            "status": "Warning" if action in {"block", "failed_auth"} else "Success",
            "time": _human_time(row.created_at),
        })
    return {"events": events}


async def service_health() -> list[dict]:
    import socket

    async def probe(name: str, host: str, port: int) -> dict:
        started = datetime.utcnow()
        ok = False
        try:
            sock = socket.create_connection((host, port), timeout=1.5)
            sock.close()
            ok = True
        except OSError:
            ok = False
        latency = int((datetime.utcnow() - started).total_seconds() * 1000)
        return {
            "name": name,
            "status": "Operational" if ok else "Down",
            "latency": f"{latency} ms" if ok else "—",
            "port": port,
        }

    db_host = "127.0.0.1" if settings.db_host == "postgres" else settings.db_host
    redis_host = "127.0.0.1" if settings.redis_host == "redis" else settings.redis_host
    minio_host = "127.0.0.1" if settings.minio_host == "minio" else settings.minio_host
    try:
        socket.getaddrinfo(settings.db_host, settings.db_port)
        db_host = settings.db_host
    except OSError:
        db_host = "127.0.0.1"
    try:
        socket.getaddrinfo(settings.redis_host, settings.redis_port)
        redis_host = settings.redis_host
    except OSError:
        redis_host = "127.0.0.1"
    try:
        socket.getaddrinfo(settings.minio_host, settings.minio_port)
        minio_host = settings.minio_host
    except OSError:
        minio_host = "127.0.0.1"
    return [
        await probe("PostgreSQL", db_host, settings.db_port),
        await probe("Redis", redis_host, settings.redis_port),
        await probe("MinIO", minio_host, settings.minio_port),
    ]
