"""Seed database with initial data for development."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.models.base import engine, Base, async_session_factory
from bot.models.user import TelegramUser, Organization
from bot.models.test import Test, Question, AnswerOption
from bot.models.course import Course, CourseModule, Lesson
from bot.models.news import News
from bot.models.library import FileCategory
from bot.models.gamification import Badge
from bot.core.enums import Role, UserStatus, BadgeType


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        async with session.begin():
            org = Organization(name="Bosh boshqarma", org_type="department")
            session.add(org)
            await session.flush()

            org2 = Organization(
                name="AT bo'limi", org_type="department", parent_id=org.id
            )
            session.add(org2)

            cat1 = FileCategory(name="Qonunchilik", icon="📜", order=1)
            cat2 = FileCategory(name="Yo'riqnomalar", icon="📋", order=2)
            cat3 = FileCategory(name="AT materiallari", icon="💻", order=3)
            session.add_all([cat1, cat2, cat3])

            for bt in BadgeType:
                badge = Badge(
                    badge_type=bt.value,
                    name=bt.value.replace("_", " ").title(),
                    description=f"{bt.value} badge",
                    icon="🏅",
                )
                session.add(badge)

            test = Test(
                title="Kiberxavfsizlik asoslari",
                description="Kiberxavfsizlik bo'yicha asosiy bilimlarni tekshirish",
                time_per_question=30,
                passing_score=60,
                max_attempts=3,
            )
            session.add(test)
            await session.flush()

            q1 = Question(
                test_id=test.id,
                text="Fishing hujumi nima?",
                order=1,
            )
            session.add(q1)
            await session.flush()

            session.add_all([
                AnswerOption(question_id=q1.id, text="Virus turi", is_correct=False, order=1),
                AnswerOption(question_id=q1.id, text="Ijtimoiy muhandislik hujumi", is_correct=True, order=2),
                AnswerOption(question_id=q1.id, text="DDoS hujumi", is_correct=False, order=3),
                AnswerOption(question_id=q1.id, text="Brute force hujumi", is_correct=False, order=4),
            ])

            course = Course(
                title="Axborot xavfsizligi kursi",
                description="IIV xodimlari uchun axborot xavfsizligi asoslari",
            )
            session.add(course)
            await session.flush()

            module = CourseModule(
                course_id=course.id,
                title="Kirish",
                order=1,
            )
            session.add(module)
            await session.flush()

            session.add_all([
                Lesson(module_id=module.id, title="Axborot xavfsizligi nima?", content="Axborot xavfsizligi — ...", order=1),
                Lesson(module_id=module.id, title="Tahdidlar turlari", content="Asosiy tahdidlar: ...", order=2),
            ])

            news = News(
                title="Tizim ishga tushirildi",
                content="IIV Ta'lim Platformasi muvaffaqiyatli ishga tushirildi!",
                author_id=None,
            )
            session.add(news)

        await session.commit()

    print("Seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
