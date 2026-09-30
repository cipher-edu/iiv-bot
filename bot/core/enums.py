from enum import Enum


class ValueEnum(str, Enum):
    """Keep str() equal to the stored database value on Python 3.14."""

    def __str__(self) -> str:
        return self.value


class Role(ValueEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"

    @property
    def level(self) -> int:
        levels = {
            self.SUPERADMIN: 100,
            self.ADMIN: 80,
            self.MODERATOR: 60,
            self.USER: 40,
            self.GUEST: 0,
        }
        return levels[self]

    def has_permission(self, required: "Role") -> bool:
        return self.level >= required.level


class UserStatus(ValueEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    PENDING = "pending"
    INACTIVE = "inactive"


class RegistrationStep(ValueEnum):
    PHONE = "phone"
    FULL_NAME = "full_name"
    CATEGORY = "category"
    POSITION = "position"
    COMPLETED = "completed"
    # legacy steps preserved for backwards compatibility with existing rows
    ROLE = "role"
    ORGANIZATION = "organization"


class TestSessionStatus(ValueEnum):
    ACTIVE = "active"
    FINISHED = "finished"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class OrganizationType(ValueEnum):
    DEPARTMENT = "bolim"
    FACULTY = "fakultet"
    CHAIR = "kafedra"


class StaffRole(ValueEnum):
    WORKER = "ishchi_hodim"
    DECANATE = "dekanat"
    PROFESSOR = "professor"


class UserCategory(ValueEnum):
    HODIM = "hodim"
    FUQARO = "fuqaro"


class AttachmentType(ValueEnum):
    VIDEO = "video"
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    LINK = "link"


class AttachmentStorage(ValueEnum):
    TELEGRAM = "telegram"
    MINIO = "minio"
    URL = "url"


class CourseStatus(ValueEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Language(ValueEnum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class NotificationType(ValueEnum):
    SYSTEM = "system"
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    REMINDER = "reminder"


class AuditAction(ValueEnum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BLOCK = "block"
    UNBLOCK = "unblock"
    ROLE_CHANGE = "role_change"
    BROADCAST = "broadcast"
    EXPORT = "export"
    BACKUP = "backup"
    SETTINGS_CHANGE = "settings_change"
    FAILED_AUTH = "failed_auth"


class BadgeType(ValueEnum):
    FIRST_TEST = "first_test"
    TEN_TESTS = "ten_tests"
    PERFECT_SCORE = "perfect_score"
    FIRST_COURSE = "first_course"
    FIVE_COURSES = "five_courses"
    STREAK_7 = "streak_7"
    STREAK_30 = "streak_30"
    TOP_WEEKLY = "top_weekly"
    HELPER = "helper"
    EARLY_BIRD = "early_bird"


class PointReason(ValueEnum):
    TEST_EXCELLENT = "test_excellent"
    TEST_GOOD = "test_good"
    TEST_SATISFACTORY = "test_satisfactory"
    TEST_PARTICIPATION = "test_participation"
    COURSE_COMPLETE = "course_complete"
    STREAK_BONUS = "streak_bonus"
    CHALLENGE_BONUS = "challenge_bonus"
    ADMIN_BONUS = "admin_bonus"
    DUEL_WIN = "duel_win"
