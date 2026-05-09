"""Docker healthcheck. Verifies DB, Redis, and bot heartbeat freshness."""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HEARTBEAT_FILE = Path(os.environ.get("BOT_HEARTBEAT_FILE", "/tmp/bot_heartbeat"))
HEARTBEAT_MAX_AGE = int(os.environ.get("BOT_HEARTBEAT_MAX_AGE", "120"))


async def check_health() -> int:
    checks: dict[str, bool] = {
        "database": False,
        "redis": False,
        "heartbeat": False,
    }

    try:
        from bot.models.base import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        print(f"Database check failed: {e}")

    try:
        import redis.asyncio as aioredis
        from bot.config import settings
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = True
    except Exception as e:
        print(f"Redis check failed: {e}")

    try:
        if HEARTBEAT_FILE.exists():
            age = time.time() - HEARTBEAT_FILE.stat().st_mtime
            if age <= HEARTBEAT_MAX_AGE:
                checks["heartbeat"] = True
            else:
                print(f"Heartbeat stale: {age:.0f}s > {HEARTBEAT_MAX_AGE}s")
        else:
            print(f"Heartbeat file missing: {HEARTBEAT_FILE}")
    except Exception as e:
        print(f"Heartbeat check failed: {e}")

    all_ok = all(checks.values())
    status = "HEALTHY" if all_ok else "UNHEALTHY"
    print(f"Status: {status}")
    for name, ok in checks.items():
        print(f"  {name}: {'OK' if ok else 'FAIL'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    exit_code = asyncio.run(check_health())
    sys.exit(exit_code)
