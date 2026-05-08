"""Health check script for Docker healthcheck."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def check_health():
    checks = {"database": False, "redis": False}

    try:
        from bot.models.base import async_engine
        from sqlalchemy import text
        async with async_engine.connect() as conn:
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

    all_ok = all(checks.values())
    status = "HEALTHY" if all_ok else "UNHEALTHY"
    print(f"Status: {status}")
    for name, ok in checks.items():
        print(f"  {name}: {'OK' if ok else 'FAIL'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    exit_code = asyncio.run(check_health())
    sys.exit(exit_code)
