from bot.repositories.base import BaseRepository
from bot.repositories.user_repo import UserRepository
from bot.repositories.test_repo import TestRepository
from bot.repositories.course_repo import CourseRepository
from bot.repositories.news_repo import NewsRepository
from bot.repositories.rating_repo import RatingRepository
from bot.repositories.certificate_repo import CertificateRepository
from bot.repositories.gamification_repo import GamificationRepository
from bot.repositories.notification_repo import NotificationRepository
from bot.repositories.audit_repo import AuditRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "TestRepository",
    "CourseRepository",
    "NewsRepository",
    "RatingRepository",
    "CertificateRepository",
    "GamificationRepository",
    "NotificationRepository",
    "AuditRepository",
]
