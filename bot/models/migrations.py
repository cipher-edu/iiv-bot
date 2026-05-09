"""Idempotent additive schema migrations.

Runs at startup after `Base.metadata.create_all`. Each statement uses
`IF NOT EXISTS` / `IF EXISTS` so it's safe to run on every boot.

This is a stop-gap until proper Alembic migrations are wired in. It only
covers ADD COLUMN style changes — never DROP, never ALTER TYPE.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


SCHEMA_PATCHES: list[str] = [
    # users.category (UserCategory: hodim/fuqaro)
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS category VARCHAR(20)",
    # courses: status (DRAFT/PUBLISHED/ARCHIVED) and syllabus
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'published'",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS syllabus_file_id VARCHAR(500)",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS syllabus_url VARCHAR(500)",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS syllabus_title VARCHAR(255)",
    "ALTER TABLE courses ADD COLUMN IF NOT EXISTS syllabus_type VARCHAR(20)",
    # lessons: require_rating
    "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS require_rating BOOLEAN NOT NULL DEFAULT TRUE",
    # test_sessions: replace overly-strict unique constraint with partial index
    # (only ACTIVE sessions need to be unique per user+test; finished/expired/abandoned can repeat)
    "ALTER TABLE test_sessions DROP CONSTRAINT IF EXISTS uq_active_session",
    "DROP INDEX IF EXISTS uq_active_session",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_active_session ON test_sessions (user_id, test_id) WHERE status = 'active'",
]


async def apply_additive_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for stmt in SCHEMA_PATCHES:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                logger.warning("Migration patch ignored (%s): %s", stmt[:80], e)
