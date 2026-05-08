from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str
    bot_admin_ids: list[int] = Field(default_factory=list)
    bot_superadmin_ids: list[int] = Field(default_factory=list)

    # Database
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "iiv_bot"
    db_user: str = "iiv_admin"
    db_password: str
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str
    redis_db: int = 0
    redis_fsm_db: int = 1

    # AI
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ai_model: str = "claude-sonnet-4-6"
    ai_max_tokens: int = 1024
    ai_enabled: bool = True

    # MinIO
    minio_host: str = "minio"
    minio_port: int = 9000
    minio_user: str = "minioadmin"
    minio_password: str = ""
    minio_bucket: str = "iiv-bot-files"
    minio_secure: bool = False

    # Security
    secret_key: str
    encryption_key: str = ""
    jwt_secret: str = ""
    allowed_ips: list[str] = Field(default_factory=lambda: ["127.0.0.1"])
    rate_limit_user: int = 30
    rate_limit_admin: int = 60
    max_login_attempts: int = 5
    ban_duration_minutes: int = 15
    session_timeout_minutes: int = 30

    # Scheduler
    news_broadcast_hour: int = 9
    news_broadcast_minute: int = 0
    rating_calc_day: str = "mon"
    rating_calc_hour: int = 8
    certificate_check_day: int = 1
    certificate_check_hour: int = 10
    backup_hour: int = 3
    cleanup_hour: int = 4

    # Notification
    quiet_hours_start: int = 22
    quiet_hours_end: int = 7

    # Scoring
    score_excellent: int = 10
    score_good: int = 7
    score_satisfactory: int = 4
    score_participation: int = 1
    score_course_complete: int = 15
    score_streak_bonus: int = 5
    score_challenge_bonus: int = 3
    score_excellent_threshold: int = 85
    score_good_threshold: int = 70
    score_satisfactory_threshold: int = 50

    # General
    debug: bool = False
    log_level: str = "INFO"
    timezone: str = "Asia/Tashkent"
    default_language: str = "uz"
    pagination_size: int = 10
    max_file_size_mb: int = 50

    @field_validator("bot_admin_ids", "bot_superadmin_ids", mode="before")
    @classmethod
    def parse_int_list(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @field_validator("allowed_ips", mode="before")
    @classmethod
    def parse_str_list(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def redis_fsm_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_fsm_db}"


settings = Settings()
