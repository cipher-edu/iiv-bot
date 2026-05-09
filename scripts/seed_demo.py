"""Demo data seeder. Idempotent: skips creating new rows if a category already
has >= MIN_PER_TABLE entries. Counts every table at the end so we can verify."""
import asyncio
import logging
import sys
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func, text

from bot.models.base import async_session_factory, engine
from bot.models import (
    Organization,
    TelegramUser,
    Test,
    Question,
    AnswerOption,
    TestSession,
    UserAnswer,
    TestResult,
    Course,
    CourseModule,
    Lesson,
    LessonAttachment,
    LessonRating,
    CoursePrerequisite,
    Enrollment,
    LessonProgress,
    News,
    BroadcastLog,
    UserRating,
    PointTransaction,
    WeeklyLeaderboard,
    Certificate,
    CertificateTemplate,
    Badge,
    UserBadge,
    UserStreak,
    UserLevel,
    Challenge,
    ChallengeParticipation,
    Notification,
    NotificationPreference,
    AuditLog,
    SecurityEvent,
    FileItem,
    FileCategory,
    Bookmark,
    Task,
    TaskAssignment,
    Survey,
    SurveyQuestion,
    SurveyResponse,
    AIConversation,
    AIMessage,
    SavedItem,
    Suggestion,
    LearningPath,
    PathCourse,
    UserPathEnrollment,
    LessonQuestion,
    LessonAnswer,
    QAUpvote,
    UserGoal,
    SpacedRepetition,
    LessonHistory,
)
from bot.core.enums import (
    Role,
    UserStatus,
    RegistrationStep,
    UserCategory,
    OrganizationType,
    StaffRole,
    TestSessionStatus,
    AuditAction,
    AttachmentType,
    AttachmentStorage,
    CourseStatus,
    BadgeType,
    NotificationType,
    PointReason,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("seeder")

MIN_PER_TABLE = 10
SUPERADMIN_TG_ID = 1062838548


async def _count(session, model) -> int:
    stmt = select(func.count()).select_from(model)
    return (await session.execute(stmt)).scalar_one()


async def seed_organizations(session) -> list[Organization]:
    if await _count(session, Organization) >= MIN_PER_TABLE:
        return list((await session.execute(select(Organization))).scalars().all())

    items = [
        ("IIV Bosh boshqarmasi", OrganizationType.DEPARTMENT),
        ("Toshkent shahar IIV", OrganizationType.DEPARTMENT),
        ("Samarqand viloyat IIV", OrganizationType.DEPARTMENT),
        ("Akademiya fakulteti", OrganizationType.FACULTY),
        ("Yuridik fakultet", OrganizationType.FACULTY),
        ("Texnologiyalar fakulteti", OrganizationType.FACULTY),
        ("Jinoiy huquq kafedrasi", OrganizationType.CHAIR),
        ("Fuqarolik huquqi kafedrasi", OrganizationType.CHAIR),
        ("Kompyuter fanlari kafedrasi", OrganizationType.CHAIR),
        ("Tillar kafedrasi", OrganizationType.CHAIR),
    ]
    orgs = []
    for name, otype in items:
        org = Organization(name=name, org_type=otype, is_active=True)
        session.add(org)
        orgs.append(org)
    await session.flush()
    logger.info("Organizations: +%d", len(orgs))
    return orgs


async def seed_users(session, orgs) -> list[TelegramUser]:
    existing = list((await session.execute(select(TelegramUser))).scalars().all())
    if len(existing) >= MIN_PER_TABLE:
        return existing

    needed = MIN_PER_TABLE - len(existing)
    new_users = []
    base_id = 200_000_000
    for i in range(needed):
        cat = UserCategory.HODIM if i % 2 == 0 else UserCategory.FUQARO
        u = TelegramUser(
            telegram_id=base_id + i,
            username=f"demo_user_{i+1}",
            full_name=f"Demo Foydalanuvchi #{i+1}",
            phone=f"+99890123{4500+i}",
            category=cat,
            position=("Mutaxassis" if cat == UserCategory.HODIM else None),
            organization_id=(
                orgs[i % len(orgs)].id if cat == UserCategory.HODIM else None
            ),
            role=Role.USER if i > 0 else Role.ADMIN,
            status=UserStatus.ACTIVE,
            registration_step=RegistrationStep.COMPLETED,
            is_verified=True,
        )
        session.add(u)
        new_users.append(u)
    await session.flush()
    logger.info("Users: +%d", len(new_users))
    return existing + new_users


async def seed_certificate_templates(session):
    if await _count(session, CertificateTemplate) >= MIN_PER_TABLE:
        return
    needed = MIN_PER_TABLE - await _count(session, CertificateTemplate)
    for i in range(needed):
        session.add(CertificateTemplate(
            name=f"Shablon #{i+1}",
            font_name="Helvetica",
            text_color="#1a237e",
            is_default=(i == 0),
        ))
    await session.flush()
    logger.info("CertificateTemplates: +%d", needed)


async def seed_courses(session) -> list[Course]:
    existing = list((await session.execute(select(Course))).scalars().all())
    if len(existing) >= MIN_PER_TABLE:
        return existing

    titles = [
        ("Yangi xodimlar uchun kirish kursi", "beginner", 4),
        ("Jinoyat huquqi asoslari", "intermediate", 12),
        ("Fuqarolik kodeksi sharhi", "intermediate", 10),
        ("Internet va kiber xavfsizlik", "beginner", 6),
        ("Tergov asoslari", "advanced", 20),
        ("Hujjat yuritish", "beginner", 4),
        ("Davlat xizmati etikasi", "beginner", 3),
        ("Korrupsiyaga qarshi kurash", "intermediate", 8),
        ("Telegram bot orqali ish yuritish", "beginner", 2),
        ("AI va rivojlanayotgan texnologiyalar", "advanced", 15),
    ]
    courses = []
    for i, (title, diff, hours) in enumerate(titles):
        c = Course(
            title=title,
            description=f"Demo kurs: {title}. Uzbekistan IIV ta'lim platformasi.",
            difficulty=diff,
            estimated_hours=hours,
            min_points=20 + i * 10,
            order=i,
            status=CourseStatus.PUBLISHED if i < 8 else CourseStatus.DRAFT,
            is_active=True,
        )
        session.add(c)
        courses.append(c)
    await session.flush()
    logger.info("Courses: +%d", len(courses))
    return courses


async def seed_modules_lessons(session, courses) -> tuple[list[CourseModule], list[Lesson]]:
    existing_lessons = list((await session.execute(select(Lesson))).scalars().all())
    existing_modules = list((await session.execute(select(CourseModule))).scalars().all())
    if len(existing_lessons) >= MIN_PER_TABLE and len(existing_modules) >= MIN_PER_TABLE:
        return existing_modules, existing_lessons

    new_modules = []
    new_lessons = []
    for c in courses[:5]:
        for m_idx in range(2):
            mod = CourseModule(course_id=c.id, title=f"{c.title} — Modul {m_idx+1}", order=m_idx)
            session.add(mod)
            await session.flush()
            new_modules.append(mod)
            for l_idx in range(2):
                lesson = Lesson(
                    module_id=mod.id,
                    title=f"Dars {l_idx+1}: {c.title}",
                    content=f"Dars matni — {c.title}, modul {m_idx+1}, dars {l_idx+1}.\n\nNamuna kontent.",
                    order=l_idx,
                    duration_minutes=15 + l_idx * 5,
                    require_rating=True,
                )
                session.add(lesson)
                new_lessons.append(lesson)
    await session.flush()
    logger.info("Modules: +%d, Lessons: +%d", len(new_modules), len(new_lessons))
    return existing_modules + new_modules, existing_lessons + new_lessons


async def seed_lesson_attachments(session, lessons):
    if await _count(session, LessonAttachment) >= MIN_PER_TABLE:
        return
    types = [
        (AttachmentType.PDF, "Lecture notes.pdf", "BAACAGEDemoFileId1"),
        (AttachmentType.VIDEO, "Intro video", "BAACAGEDemoFileId2"),
        (AttachmentType.IMAGE, "Diagram", "AgACAGEDemoFileId3"),
        (AttachmentType.LINK, None, None),
    ]
    for i, lesson in enumerate(lessons[:MIN_PER_TABLE]):
        ftype, title, fid = types[i % len(types)]
        if ftype == AttachmentType.LINK:
            session.add(LessonAttachment(
                lesson_id=lesson.id,
                file_type=ftype,
                storage=AttachmentStorage.URL,
                title=f"Demo havola {i+1}",
                url=f"https://example.com/demo-{i}",
                order=0,
            ))
        else:
            session.add(LessonAttachment(
                lesson_id=lesson.id,
                file_type=ftype,
                storage=AttachmentStorage.TELEGRAM,
                title=title,
                file_id=fid,
                order=0,
            ))
    await session.flush()
    logger.info("LessonAttachments: +%d", min(MIN_PER_TABLE, len(lessons)))


async def seed_enrollments(session, users, courses) -> list[Enrollment]:
    existing = list((await session.execute(select(Enrollment))).scalars().all())
    if len(existing) >= MIN_PER_TABLE:
        return existing

    new = []
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        c = courses[i % len(courses)]
        # check uniqueness
        dup = (await session.execute(
            select(Enrollment).where(
                Enrollment.user_id == u.id, Enrollment.course_id == c.id
            )
        )).scalar_one_or_none()
        if dup:
            continue
        e = Enrollment(
            user_id=u.id,
            course_id=c.id,
            is_completed=(i % 3 == 0),
            completed_at=(datetime.utcnow() if i % 3 == 0 else None),
        )
        session.add(e)
        new.append(e)
    await session.flush()
    logger.info("Enrollments: +%d", len(new))
    return existing + new


async def seed_lesson_progress(session, enrollments, lessons):
    if await _count(session, LessonProgress) >= MIN_PER_TABLE:
        return
    for i in range(MIN_PER_TABLE):
        e = enrollments[i % len(enrollments)]
        l = lessons[i % len(lessons)]
        dup = (await session.execute(
            select(LessonProgress).where(
                LessonProgress.enrollment_id == e.id,
                LessonProgress.lesson_id == l.id,
            )
        )).scalar_one_or_none()
        if dup:
            continue
        session.add(LessonProgress(enrollment_id=e.id, lesson_id=l.id))
    await session.flush()
    logger.info("LessonProgress: seeded")


async def seed_lesson_ratings(session, lessons, users):
    if await _count(session, LessonRating) >= MIN_PER_TABLE:
        return
    for i in range(MIN_PER_TABLE):
        l = lessons[i % len(lessons)]
        u = users[i % len(users)]
        dup = (await session.execute(
            select(LessonRating).where(
                LessonRating.lesson_id == l.id,
                LessonRating.user_id == u.id,
            )
        )).scalar_one_or_none()
        if dup:
            continue
        session.add(LessonRating(
            lesson_id=l.id, user_id=u.id,
            stars=random.randint(3, 5),
            comment=f"Demo izoh {i+1}" if i % 2 == 0 else None,
        ))
    await session.flush()
    logger.info("LessonRatings: seeded")


async def seed_course_prerequisites(session, courses):
    if await _count(session, CoursePrerequisite) >= MIN_PER_TABLE:
        return
    for i in range(min(MIN_PER_TABLE, len(courses) - 1)):
        a = courses[i]
        b = courses[(i + 1) % len(courses)]
        if a.id == b.id:
            continue
        dup = (await session.execute(
            select(CoursePrerequisite).where(
                CoursePrerequisite.course_id == b.id,
                CoursePrerequisite.required_course_id == a.id,
            )
        )).scalar_one_or_none()
        if dup:
            continue
        session.add(CoursePrerequisite(course_id=b.id, required_course_id=a.id))
    await session.flush()
    logger.info("CoursePrerequisites: seeded")


async def seed_tests(session) -> list[Test]:
    existing = list((await session.execute(select(Test))).scalars().all())
    if len(existing) >= MIN_PER_TABLE:
        return existing

    tests = []
    for i in range(MIN_PER_TABLE):
        t = Test(
            title=f"Demo test #{i+1}",
            description=f"Sinov tavsifi {i+1}",
            time_per_question=30,
            passing_score=70,
            is_active=True,
        )
        session.add(t)
        tests.append(t)
    await session.flush()
    logger.info("Tests: +%d", len(tests))
    return tests


async def seed_questions_options(session, tests) -> tuple[list[Question], list[AnswerOption]]:
    existing_q = list((await session.execute(select(Question))).scalars().all())
    if len(existing_q) >= MIN_PER_TABLE:
        existing_o = list((await session.execute(select(AnswerOption))).scalars().all())
        return existing_q, existing_o

    new_q = []
    new_o = []
    for i, t in enumerate(tests[:MIN_PER_TABLE]):
        q = Question(
            test_id=t.id,
            text=f"Test {t.id} — Savol {i+1}: 2+{i}=?",
            order=0,
            is_active=True,
        )
        session.add(q)
        await session.flush()
        new_q.append(q)
        for j in range(4):
            o = AnswerOption(
                question_id=q.id,
                text=str(2 + i + j - 1),
                is_correct=(j == 1),
                order=j,
            )
            session.add(o)
            new_o.append(o)
    await session.flush()
    logger.info("Questions: +%d, AnswerOptions: +%d", len(new_q), len(new_o))
    return new_q, new_o


async def seed_test_sessions(session, users, tests, questions, options):
    if await _count(session, TestSession) >= MIN_PER_TABLE:
        return

    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        t = tests[i % len(tests)]
        ts = TestSession(
            user_id=u.id,
            test_id=t.id,
            status=TestSessionStatus.FINISHED,
            current_question_index=1,
            started_at=datetime.utcnow() - timedelta(hours=i + 1),
            finished_at=datetime.utcnow() - timedelta(hours=i),
        )
        session.add(ts)
        await session.flush()

        # one answer per session
        q = next((qq for qq in questions if qq.test_id == t.id), None)
        if q:
            opt = next((oo for oo in options if oo.question_id == q.id and oo.is_correct), None)
            if opt:
                session.add(UserAnswer(
                    session_id=ts.id,
                    question_id=q.id,
                    selected_option_id=opt.id,
                    is_timeout=False,
                    answered_at=datetime.utcnow(),
                ))
                session.add(TestResult(
                    session_id=ts.id,
                    user_id=u.id,
                    test_id=t.id,
                    correct_count=1,
                    wrong_count=0,
                    timeout_count=0,
                    total_questions=1,
                    score_percent=100,
                    is_passed=True,
                    points_awarded=10,
                ))
    await session.flush()
    logger.info("TestSessions+UserAnswers+TestResults: seeded")


async def seed_news(session, users):
    if await _count(session, News) >= MIN_PER_TABLE:
        return
    author = users[0]
    for i in range(MIN_PER_TABLE):
        n = News(
            title=f"Yangilik #{i+1}",
            content=f"Demo yangilik matni {i+1}. IIV ta'lim platformasi yangiliklari.",
            is_active=True,
            is_broadcast=(i % 3 == 0),
            author_id=author.id,
            views_count=random.randint(0, 200),
        )
        session.add(n)
    await session.flush()
    logger.info("News: seeded")


async def seed_broadcast_logs(session):
    if await _count(session, BroadcastLog) >= MIN_PER_TABLE:
        return
    news_items = list((await session.execute(select(News).limit(3))).scalars().all())
    if not news_items:
        return
    for i in range(MIN_PER_TABLE):
        session.add(BroadcastLog(
            news_id=news_items[i % len(news_items)].id,
            telegram_id=200_000_000 + i,
            is_delivered=True,
            delivered_at=datetime.utcnow(),
        ))
    await session.flush()
    logger.info("BroadcastLogs: seeded")


async def seed_ratings(session, users):
    if await _count(session, UserRating) >= MIN_PER_TABLE:
        return
    for i, u in enumerate(users[:MIN_PER_TABLE]):
        dup = (await session.execute(
            select(UserRating).where(UserRating.user_id == u.id)
        )).scalar_one_or_none()
        if dup:
            continue
        pts = random.randint(20, 500)
        session.add(UserRating(
            user_id=u.id,
            total_points=pts,
            weekly_points=random.randint(0, 50),
            monthly_points=random.randint(0, 200),
            tests_taken=random.randint(0, 30),
            tests_passed=random.randint(0, 25),
            courses_completed=random.randint(0, 5),
        ))
    await session.flush()
    logger.info("UserRatings: seeded")


async def seed_point_transactions(session, users):
    if await _count(session, PointTransaction) >= MIN_PER_TABLE:
        return
    ratings = {r.user_id: r for r in (await session.execute(select(UserRating))).scalars().all()}
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        rating = ratings.get(u.id)
        if not rating:
            continue
        session.add(PointTransaction(
            user_id=u.id,
            rating_id=rating.id,
            points=random.choice([1, 4, 7, 10, 15]),
            reason=PointReason.TEST_GOOD,
            description=f"Demo tranzaksiya {i+1}",
        ))
    await session.flush()
    logger.info("PointTransactions: seeded")


async def seed_weekly_leaderboard(session):
    if await _count(session, WeeklyLeaderboard) >= MIN_PER_TABLE:
        return
    today = date.today()
    for i in range(MIN_PER_TABLE):
        ws = today - timedelta(weeks=i + 1)
        we = ws + timedelta(days=6)
        dup = (await session.execute(
            select(WeeklyLeaderboard).where(
                WeeklyLeaderboard.week_start == ws,
                WeeklyLeaderboard.week_end == we,
            )
        )).scalar_one_or_none()
        if dup:
            continue
        session.add(WeeklyLeaderboard(
            week_start=ws,
            week_end=we,
            rankings=[{"position": 1, "user_id": 1, "name": "Demo", "points": 100}],
            is_announced=True,
            total_participants=random.randint(5, 30),
        ))
    await session.flush()
    logger.info("WeeklyLeaderboards: seeded")


async def seed_certificates(session, users, courses):
    if await _count(session, Certificate) >= MIN_PER_TABLE:
        return
    import uuid
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        c = courses[i % len(courses)]
        session.add(Certificate(
            user_id=u.id,
            course_id=c.id,
            title=f"{c.title} sertifikati",
            certificate_number=f"IIV-2025-DEMO{uuid.uuid4().hex[:6].upper()}",
            issued_date=date.today() - timedelta(days=i),
            score_percent=random.randint(70, 100),
            is_valid=True,
        ))
    await session.flush()
    logger.info("Certificates: seeded")


async def seed_badges(session, users):
    if await _count(session, Badge) >= MIN_PER_TABLE:
        return
    types = list(BadgeType)[:MIN_PER_TABLE]
    badges = []
    for i, bt in enumerate(types):
        b = Badge(
            badge_type=bt,
            name=bt.value.replace("_", " ").title(),
            description=f"Demo badge: {bt.value}",
            icon="🏅",
            points_reward=10 + i,
            is_active=True,
        )
        session.add(b)
        badges.append(b)
    await session.flush()

    if await _count(session, UserBadge) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            b = badges[i % len(badges)]
            dup = (await session.execute(
                select(UserBadge).where(
                    UserBadge.user_id == u.id,
                    UserBadge.badge_id == b.id,
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(UserBadge(
                user_id=u.id, badge_id=b.id, earned_at=datetime.utcnow()
            ))
        await session.flush()
    logger.info("Badges + UserBadges: seeded")


async def seed_streaks_levels(session, users):
    if await _count(session, UserStreak) < MIN_PER_TABLE:
        for u in users[:MIN_PER_TABLE]:
            dup = (await session.execute(
                select(UserStreak).where(UserStreak.user_id == u.id)
            )).scalar_one_or_none()
            if dup:
                continue
            cs = random.randint(1, 30)
            session.add(UserStreak(
                user_id=u.id,
                current_streak=cs,
                longest_streak=cs + random.randint(0, 30),
                last_activity_date=date.today(),
                streak_start_date=date.today() - timedelta(days=cs),
            ))
        await session.flush()

    if await _count(session, UserLevel) < MIN_PER_TABLE:
        for i, u in enumerate(users[:MIN_PER_TABLE]):
            dup = (await session.execute(
                select(UserLevel).where(UserLevel.user_id == u.id)
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(UserLevel(
                user_id=u.id,
                level=1 + i // 2,
                level_name=f"Daraja {1 + i // 2}",
                experience=random.randint(0, 500),
            ))
        await session.flush()
    logger.info("Streaks + Levels: seeded")


async def seed_challenges(session, users):
    if await _count(session, Challenge) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            session.add(Challenge(
                title=f"Challenge #{i+1}",
                description="Demo challenge",
                challenge_type=random.choice(["weekly_tests", "course_complete"]),
                target_value=random.randint(3, 10),
                reward_points=random.randint(5, 30),
                start_date=date.today() - timedelta(days=7),
                end_date=date.today() + timedelta(days=7),
                is_active=True,
            ))
        await session.flush()

    if await _count(session, ChallengeParticipation) < MIN_PER_TABLE:
        challenges = list((await session.execute(select(Challenge))).scalars().all())
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            ch = challenges[i % len(challenges)]
            dup = (await session.execute(
                select(ChallengeParticipation).where(
                    ChallengeParticipation.user_id == u.id,
                    ChallengeParticipation.challenge_id == ch.id,
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(ChallengeParticipation(
                user_id=u.id,
                challenge_id=ch.id,
                current_value=random.randint(0, ch.target_value),
                is_completed=(i % 4 == 0),
            ))
        await session.flush()
    logger.info("Challenges + Participations: seeded")


async def seed_notifications(session, users):
    if await _count(session, Notification) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            session.add(Notification(
                user_id=u.id,
                title=f"Bildirishnoma #{i+1}",
                message=f"Demo bildirishnoma matni {i+1}",
                notification_type=random.choice(list(NotificationType)),
                is_read=(i % 2 == 0),
            ))
        await session.flush()

    if await _count(session, NotificationPreference) < MIN_PER_TABLE:
        for u in users[:MIN_PER_TABLE]:
            dup = (await session.execute(
                select(NotificationPreference).where(NotificationPreference.user_id == u.id)
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(NotificationPreference(user_id=u.id))
        await session.flush()
    logger.info("Notifications + Preferences: seeded")


async def seed_audit_security(session, users):
    if await _count(session, AuditLog) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            session.add(AuditLog(
                user_id=u.id,
                telegram_id=u.telegram_id,
                action=random.choice([AuditAction.LOGIN, AuditAction.UPDATE, AuditAction.CREATE]),
                entity_type="user",
                entity_id=u.id,
                details={"demo": i},
            ))
        await session.flush()

    if await _count(session, SecurityEvent) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            session.add(SecurityEvent(
                event_type="failed_login",
                severity=random.choice(["low", "medium", "high"]),
                telegram_id=200_000_000 + i,
                description=f"Demo security event #{i+1}",
                is_resolved=(i % 3 == 0),
            ))
        await session.flush()
    logger.info("AuditLogs + SecurityEvents: seeded")


async def seed_library(session, users):
    if await _count(session, FileCategory) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            session.add(FileCategory(
                name=f"Kategoriya #{i+1}",
                description=f"Demo kategoriya {i+1}",
                icon="📁",
                order=i,
                is_active=True,
            ))
        await session.flush()

    cats = list((await session.execute(select(FileCategory))).scalars().all())
    if await _count(session, FileItem) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            session.add(FileItem(
                title=f"Demo fayl #{i+1}",
                description=f"Demo fayl tavsifi {i+1}",
                file_path=f"/demo/file_{i+1}.pdf",
                file_type="pdf",
                file_size=random.randint(1000, 5_000_000),
                mime_type="application/pdf",
                category_id=cats[i % len(cats)].id,
                uploaded_by=u.id,
                tags=["demo", "iiv"],
                is_active=True,
            ))
        await session.flush()

    files = list((await session.execute(select(FileItem))).scalars().all())
    if await _count(session, Bookmark) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            f = files[i % len(files)]
            dup = (await session.execute(
                select(Bookmark).where(
                    Bookmark.user_id == u.id, Bookmark.file_id == f.id
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(Bookmark(user_id=u.id, file_id=f.id, note=f"Demo {i+1}"))
        await session.flush()
    logger.info("FileCategories + FileItems + Bookmarks: seeded")


async def seed_tasks(session, users, orgs):
    if await _count(session, Task) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            session.add(Task(
                title=f"Vazifa #{i+1}",
                description=f"Demo vazifa {i+1}",
                created_by=users[0].id,
                priority=random.choice(["low", "medium", "high"]),
                status=random.choice(["pending", "in_progress", "completed"]),
                deadline=datetime.utcnow() + timedelta(days=random.randint(1, 30)),
                target_organization_id=orgs[i % len(orgs)].id,
                is_active=True,
            ))
        await session.flush()

    if await _count(session, TaskAssignment) < MIN_PER_TABLE:
        tasks = list((await session.execute(select(Task))).scalars().all())
        for i in range(MIN_PER_TABLE):
            session.add(TaskAssignment(
                task_id=tasks[i % len(tasks)].id,
                user_id=users[i % len(users)].id,
                status=random.choice(["assigned", "in_progress", "completed"]),
                started_at=datetime.utcnow() - timedelta(days=i),
            ))
        await session.flush()
    logger.info("Tasks + TaskAssignments: seeded")


async def seed_surveys(session, users):
    if await _count(session, Survey) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            session.add(Survey(
                title=f"So'rovnoma #{i+1}",
                description=f"Demo so'rovnoma {i+1}",
                is_anonymous=(i % 2 == 0),
                is_active=True,
                created_by=users[0].id,
                starts_at=datetime.utcnow() - timedelta(days=1),
                ends_at=datetime.utcnow() + timedelta(days=7),
                total_responses=0,
            ))
        await session.flush()

    surveys = list((await session.execute(select(Survey))).scalars().all())
    if await _count(session, SurveyQuestion) < MIN_PER_TABLE:
        for i, s in enumerate(surveys[:MIN_PER_TABLE]):
            session.add(SurveyQuestion(
                survey_id=s.id,
                text=f"Savol {i+1}",
                question_type="single_choice",
                options=["A", "B", "C"],
                is_required=True,
                order=0,
            ))
        await session.flush()

    if await _count(session, SurveyResponse) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            s = surveys[i % len(surveys)]
            dup = (await session.execute(
                select(SurveyResponse).where(
                    SurveyResponse.survey_id == s.id,
                    SurveyResponse.user_id == u.id,
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(SurveyResponse(
                survey_id=s.id,
                user_id=u.id,
                answers={"q1": "A"},
                submitted_at=datetime.utcnow(),
            ))
        await session.flush()
    logger.info("Surveys + Questions + Responses: seeded")


async def seed_ai(session, users):
    if await _count(session, AIConversation) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            session.add(AIConversation(
                user_id=u.id,
                title=f"Suhbat #{i+1}",
                model_used="claude-sonnet-4-6",
                total_tokens=random.randint(100, 1000),
                message_count=random.randint(2, 10),
                is_active=True,
            ))
        await session.flush()

    convs = list((await session.execute(select(AIConversation))).scalars().all())
    if await _count(session, AIMessage) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            c = convs[i % len(convs)]
            session.add(AIMessage(
                conversation_id=c.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Demo xabar {i+1}",
                tokens_used=random.randint(20, 200),
            ))
        await session.flush()
    logger.info("AIConversations + AIMessages: seeded")


async def seed_saved_items(session, users, lessons, courses):
    if await _count(session, SavedItem) >= MIN_PER_TABLE:
        return
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        if i % 2 == 0 and lessons:
            l = lessons[i % len(lessons)]
            entity_type, entity_id, title = "lesson", l.id, l.title
        elif courses:
            c = courses[i % len(courses)]
            entity_type, entity_id, title = "course", c.id, c.title
        else:
            continue
        dup = (await session.execute(
            select(SavedItem).where(
                SavedItem.user_id == u.id,
                SavedItem.entity_type == entity_type,
                SavedItem.entity_id == entity_id,
            )
        )).scalar_one_or_none()
        if dup:
            continue
        session.add(SavedItem(
            user_id=u.id,
            entity_type=entity_type,
            entity_id=entity_id,
            title_cache=title,
        ))
    await session.flush()
    logger.info("SavedItems: seeded")


async def seed_suggestions(session, users):
    if await _count(session, Suggestion) >= MIN_PER_TABLE:
        return
    for i in range(MIN_PER_TABLE):
        anon = (i % 2 == 0)
        session.add(Suggestion(
            user_id=None if anon else users[i % len(users)].id,
            is_anonymous=anon,
            text=f"Demo taklif {i+1}: Iltimos, bu funksiyani yaxshilang.",
            category="other",
            status=random.choice(["new", "responded", "closed"]),
        ))
    await session.flush()
    logger.info("Suggestions: seeded")


async def seed_learning_paths(session, courses, users):
    if await _count(session, LearningPath) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            session.add(LearningPath(
                title=f"O'qish yo'li #{i+1}",
                description=f"Demo yo'l {i+1}",
                icon="🎯",
                is_active=True,
            ))
        await session.flush()

    paths = list((await session.execute(select(LearningPath))).scalars().all())
    if await _count(session, PathCourse) < MIN_PER_TABLE:
        for i, p in enumerate(paths[:MIN_PER_TABLE]):
            c = courses[i % len(courses)]
            dup = (await session.execute(
                select(PathCourse).where(
                    PathCourse.path_id == p.id, PathCourse.course_id == c.id
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(PathCourse(path_id=p.id, course_id=c.id, order=0))
        await session.flush()

    if await _count(session, UserPathEnrollment) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            p = paths[i % len(paths)]
            dup = (await session.execute(
                select(UserPathEnrollment).where(
                    UserPathEnrollment.user_id == u.id,
                    UserPathEnrollment.path_id == p.id,
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(UserPathEnrollment(user_id=u.id, path_id=p.id))
        await session.flush()
    logger.info("LearningPaths + PathCourses + Enrollments: seeded")


async def seed_qa(session, users, lessons):
    if await _count(session, LessonQuestion) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            l = lessons[i % len(lessons)]
            session.add(LessonQuestion(
                lesson_id=l.id,
                user_id=u.id,
                question=f"Demo savol {i+1}: bu nima degani?",
                upvotes=random.randint(0, 10),
            ))
        await session.flush()

    qs = list((await session.execute(select(LessonQuestion))).scalars().all())
    if await _count(session, LessonAnswer) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            q = qs[i % len(qs)]
            u = users[i % len(users)]
            session.add(LessonAnswer(
                question_id=q.id,
                user_id=u.id,
                answer=f"Demo javob {i+1}",
                is_official=(i % 3 == 0),
                upvotes=random.randint(0, 5),
            ))
        await session.flush()

    if await _count(session, QAUpvote) < MIN_PER_TABLE:
        for i in range(MIN_PER_TABLE):
            u = users[i % len(users)]
            entity_id = qs[i % len(qs)].id
            dup = (await session.execute(
                select(QAUpvote).where(
                    QAUpvote.user_id == u.id,
                    QAUpvote.entity_type == "question",
                    QAUpvote.entity_id == entity_id,
                )
            )).scalar_one_or_none()
            if dup:
                continue
            session.add(QAUpvote(
                user_id=u.id,
                entity_type="question",
                entity_id=entity_id,
            ))
        await session.flush()
    logger.info("LessonQuestions + Answers + Upvotes: seeded")


async def seed_goals(session, users):
    if await _count(session, UserGoal) >= MIN_PER_TABLE:
        return
    today = date.today()
    end = today + timedelta(days=30)
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        session.add(UserGoal(
            user_id=u.id,
            goal_type=random.choice(["courses", "tests", "lessons", "points"]),
            target=random.randint(3, 20),
            progress=random.randint(0, 5),
            period="month",
            period_start=today,
            period_end=end,
        ))
    await session.flush()
    logger.info("UserGoals: seeded")


async def seed_spaced_repetition(session, users, lessons):
    if await _count(session, SpacedRepetition) >= MIN_PER_TABLE:
        return
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        l = lessons[i % len(lessons)]
        session.add(SpacedRepetition(
            user_id=u.id,
            lesson_id=l.id,
            interval_days=7 * (i + 1),
            review_count=i,
            next_review_at=datetime.utcnow() + timedelta(days=7 * (i + 1)),
            is_active=True,
        ))
    await session.flush()
    logger.info("SpacedRepetition: seeded")


async def seed_lesson_history(session, users, lessons):
    if await _count(session, LessonHistory) >= MIN_PER_TABLE:
        return
    for i in range(MIN_PER_TABLE):
        u = users[i % len(users)]
        l = lessons[i % len(lessons)]
        session.add(LessonHistory(
            lesson_id=l.id,
            version=i + 1,
            title=f"Eski versiya {i+1}: {l.title}",
            content=f"Eski matn versiyasi {i+1}",
            changed_by_user_id=u.id,
            change_note=f"Demo versiya {i+1}",
        ))
    await session.flush()
    logger.info("LessonHistory: seeded")


async def main():
    async with async_session_factory() as session:
        async with session.begin():
            orgs = await seed_organizations(session)
            users = await seed_users(session, orgs)
            await seed_certificate_templates(session)

            courses = await seed_courses(session)
            modules, lessons = await seed_modules_lessons(session, courses)
            await seed_lesson_attachments(session, lessons)
            enrollments = await seed_enrollments(session, users, courses)
            await seed_lesson_progress(session, enrollments, lessons)
            await seed_lesson_ratings(session, lessons, users)
            await seed_course_prerequisites(session, courses)

            tests = await seed_tests(session)
            questions, options = await seed_questions_options(session, tests)
            await seed_test_sessions(session, users, tests, questions, options)

            await seed_news(session, users)
            await seed_broadcast_logs(session)

            await seed_ratings(session, users)
            await seed_point_transactions(session, users)
            await seed_weekly_leaderboard(session)

            await seed_certificates(session, users, courses)
            await seed_badges(session, users)
            await seed_streaks_levels(session, users)
            await seed_challenges(session, users)
            await seed_notifications(session, users)
            await seed_audit_security(session, users)

            await seed_library(session, users)
            await seed_tasks(session, users, orgs)
            await seed_surveys(session, users)
            await seed_ai(session, users)

            await seed_saved_items(session, users, lessons, courses)
            await seed_suggestions(session, users)
            await seed_learning_paths(session, courses, users)
            await seed_qa(session, users, lessons)
            await seed_goals(session, users)
            await seed_spaced_repetition(session, users, lessons)
            await seed_lesson_history(session, users, lessons)

    # final counts
    async with async_session_factory() as session:
        tables = [
            "organizations", "users",
            "courses", "course_modules", "lessons",
            "lesson_attachments", "lesson_ratings", "course_prerequisites",
            "enrollments", "lesson_progress",
            "tests", "questions", "answer_options",
            "test_sessions", "user_answers", "test_results",
            "news", "broadcast_logs",
            "user_ratings", "point_transactions", "weekly_leaderboards",
            "certificates", "certificate_templates",
            "badges", "user_badges", "user_streaks", "user_levels",
            "challenges", "challenge_participations",
            "notifications", "notification_preferences",
            "audit_logs", "security_events",
            "file_categories", "file_items", "bookmarks",
            "tasks", "task_assignments",
            "surveys", "survey_questions", "survey_responses",
            "ai_conversations", "ai_messages",
            "saved_items", "suggestions",
            "learning_paths", "path_courses", "user_path_enrollments",
            "lesson_questions", "lesson_answers", "qa_upvotes",
            "user_goals", "spaced_repetition", "lesson_history",
        ]
        print("\n========== TABLE COUNTS ==========")
        ok = 0
        bad = 0
        for tbl in tables:
            try:
                cnt = (await session.execute(text(f"SELECT COUNT(*) FROM {tbl}"))).scalar_one()
                marker = "✓" if cnt >= MIN_PER_TABLE else "✗"
                if cnt >= MIN_PER_TABLE:
                    ok += 1
                else:
                    bad += 1
                print(f"  {marker} {tbl:35s} {cnt}")
            except Exception as e:
                bad += 1
                print(f"  ! {tbl:35s} ERROR: {e}")
        print(f"\nOK: {ok} / {len(tables)}, NEEDS MORE: {bad}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
