from bot.models.base import Base, async_session_factory, engine
from bot.models.user import TelegramUser, Organization
from bot.models.test import Test, Question, AnswerOption, TestSession, UserAnswer, TestResult
from bot.models.course import Course, CourseModule, Lesson, Enrollment, LessonProgress
from bot.models.news import News, BroadcastLog
from bot.models.rating import UserRating, PointTransaction, WeeklyLeaderboard
from bot.models.certificate import Certificate, CertificateTemplate
from bot.models.gamification import Badge, UserBadge, UserStreak, UserLevel, Challenge, ChallengeParticipation
from bot.models.notification import Notification, NotificationPreference
from bot.models.audit import AuditLog, SecurityEvent
from bot.models.library import FileItem, FileCategory, Bookmark
from bot.models.task import Task, TaskAssignment
from bot.models.survey import Survey, SurveyQuestion, SurveyResponse
from bot.models.ai_history import AIConversation, AIMessage
from bot.models.bookmark import SavedItem
from bot.models.suggestion import Suggestion
from bot.models.learning_path import LearningPath, PathCourse, UserPathEnrollment
from bot.models.qa import LessonQuestion, LessonAnswer, QAUpvote
from bot.models.goal import UserGoal
from bot.models.repetition import SpacedRepetition
from bot.models.content_version import LessonHistory
from bot.models.course import (
    LessonAttachment,
    LessonRating,
    CoursePrerequisite,
)

__all__ = [
    "Base",
    "async_session_factory",
    "engine",
    "TelegramUser",
    "Organization",
    "Test",
    "Question",
    "AnswerOption",
    "TestSession",
    "UserAnswer",
    "TestResult",
    "Course",
    "CourseModule",
    "Lesson",
    "Enrollment",
    "LessonProgress",
    "News",
    "BroadcastLog",
    "UserRating",
    "PointTransaction",
    "WeeklyLeaderboard",
    "Certificate",
    "CertificateTemplate",
    "Badge",
    "UserBadge",
    "UserStreak",
    "UserLevel",
    "Challenge",
    "ChallengeParticipation",
    "Notification",
    "NotificationPreference",
    "AuditLog",
    "SecurityEvent",
    "FileItem",
    "FileCategory",
    "Bookmark",
    "Task",
    "TaskAssignment",
    "Survey",
    "SurveyQuestion",
    "SurveyResponse",
    "AIConversation",
    "AIMessage",
    "SavedItem",
    "Suggestion",
    "LearningPath",
    "PathCourse",
    "UserPathEnrollment",
    "LessonQuestion",
    "LessonAnswer",
    "QAUpvote",
    "UserGoal",
    "SpacedRepetition",
    "LessonHistory",
    "LessonAttachment",
    "LessonRating",
    "CoursePrerequisite",
]
