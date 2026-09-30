"""IIV EduBot Web App API.

Run from the project root:

    python -m bot.api.server
"""

from __future__ import annotations

import logging
import os
import socket
import uuid
from pathlib import Path

logger = logging.getLogger("iiv.webapi")


def _prefer_reachable_hosts() -> None:
    """On a developer machine the Compose hostnames do not resolve."""
    if os.environ.get("DB_HOST") not in (None, "", "postgres"):
        return
    try:
        socket.getaddrinfo("postgres", 5432)
    except OSError:
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ.setdefault("REDIS_HOST", "127.0.0.1")
        os.environ.setdefault("MINIO_HOST", "127.0.0.1")


_prefer_reachable_hosts()

from aiohttp import web  # noqa: E402

from bot.api.auth import issue_token, read_token, verify_init_data  # noqa: E402
from bot.api import service  # noqa: E402
from bot.models.base import async_session_factory  # noqa: E402

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
}

OPEN_PATHS = {
    "/health",
    "/api/v1/auth/telegram",
    "/api/v1/auth/local",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}


def json_error(message: str, status: int) -> web.Response:
    return web.json_response({"error": message}, status=status)


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=CORS)
    response = await handler(request)
    response.headers.update(CORS)
    return response


@web.middleware
async def db_middleware(request: web.Request, handler):
    if request.method == "OPTIONS" or request.path == "/health":
        return await handler(request)
    async with async_session_factory() as session:
        request["db"] = session
        try:
            response = await handler(request)
        except Exception:
            await session.rollback()
            raise
        if response.status >= 400:
            await session.rollback()
        else:
            await session.commit()
        return response


@web.middleware
async def auth_middleware(request: web.Request, handler):
    if request.method == "OPTIONS" or request.path in OPEN_PATHS:
        return await handler(request)
    header = request.headers.get("Authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if not token:
        return json_error("Sessiya yo'q", 401)
    try:
        user_id = read_token(token)
    except ValueError as exc:
        return json_error(str(exc), 401)
    user = await service.load_user(request["db"], user_id)
    if not user:
        return json_error("Foydalanuvchi topilmadi", 401)
    if not await service.ensure_unblocked(request["db"], user):
        return json_error("Hisob bloklangan", 403)
    request["user"] = user
    return await handler(request)


@web.middleware
async def error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as exc:
        logger.exception("Web API xatosi: %s %s", request.method, request.path)
        text = f"{type(exc).__name__} {exc}".lower()
        if any(word in text for word in ("connect", "refused", "1225", "timeout")):
            return json_error(
                "Ma'lumotlar bazasiga ulanib bo'lmadi. PostgreSQL ishga tushganini tekshiring.",
                503,
            )
        return json_error("Server xatosi", 500)


def _admin(request: web.Request):
    user = request["user"]
    if not service.is_superadmin_user(user):
        return None
    return user


async def health(_request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "iiv-webapp-api"})


async def auth_telegram(request: web.Request) -> web.Response:
    body = await request.json()
    try:
        tg_user = verify_init_data(body.get("initData") or "")
        user = await service.upsert_from_telegram(request["db"], tg_user)
    except ValueError as exc:
        return json_error(str(exc), 401)
    if not await service.ensure_unblocked(request["db"], user):
        return json_error("Hisob bloklangan", 403)
    await service.touch_user(request["db"], user)
    profile = await service.user_profile(request["db"], user)
    return web.json_response({"token": issue_token(user.id), "user": profile})


async def _optional_telegram(body: dict) -> dict | None:
    raw = body.get("initData") or ""
    if not raw:
        return None
    return verify_init_data(raw)


async def auth_login(request: web.Request) -> web.Response:
    body = await request.json()
    try:
        tg_user = await _optional_telegram(body)
        user = await service.login_with_password(
            request["db"],
            body.get("login") or "",
            body.get("password") or "",
            tg_user,
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    if not await service.ensure_unblocked(request["db"], user):
        return json_error("Hisob bloklangan", 403)
    await service.touch_user(request["db"], user)
    profile = await service.user_profile(request["db"], user)
    return web.json_response({"token": issue_token(user.id), "user": profile})


async def auth_register(request: web.Request) -> web.Response:
    body = await request.json()
    try:
        tg_user = await _optional_telegram(body)
        user = await service.register_account(
            request["db"],
            full_name=body.get("fullName") or "",
            phone=body.get("phone") or "",
            category=body.get("category") or "",
            login=body.get("login") or "",
            password=body.get("password") or "",
            position=body.get("position") or "",
            telegram_user=tg_user,
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    await service.touch_user(request["db"], user)
    profile = await service.user_profile(request["db"], user)
    return web.json_response({"token": issue_token(user.id), "user": profile})


async def auth_local(request: web.Request) -> web.Response:
    body = await request.json()
    full_name = (body.get("fullName") or "").strip()
    phone = (body.get("phone") or "").strip()[:20]
    category = body.get("category") or "fuqaro"
    if len(full_name) < 3:
        return json_error("Ism-familiya kamida 3 ta belgi bo'lsin", 400)
    if category not in {"hodim", "fuqaro"}:
        category = "fuqaro"
    user = await service.create_local_user(request["db"], full_name, phone, category)
    await service.touch_user(request["db"], user)
    profile = await service.user_profile(request["db"], user)
    return web.json_response({"token": issue_token(user.id), "user": profile})


async def me(request: web.Request) -> web.Response:
    await service.touch_user(request["db"], request["user"])
    return web.json_response(await service.user_profile(request["db"], request["user"]))


async def set_category(request: web.Request) -> web.Response:
    body = await request.json()
    category = body.get("category") or ""
    if category not in {"hodim", "fuqaro"}:
        return json_error("Toifa hodim yoki fuqaro bo'lishi kerak", 400)
    user = await service.finish_with_category(request["db"], request["user"], category)
    request["user"] = user
    return web.json_response(await service.user_profile(request["db"], user))


async def bootstrap(request: web.Request) -> web.Response:
    user = request["user"]
    await service.touch_user(request["db"], user)
    db = request["db"]
    return web.json_response({
        "user": await service.user_profile(db, user),
        "courses": await service.list_courses(db, user),
        "tests": await service.list_tests(db, user),
        "leaderboard": await service.leaderboard(db),
        "badges": await service.badges_for(db, user.id),
        "certificates": await service.certificates_for(db, user),
    })


async def courses(request: web.Request) -> web.Response:
    return web.json_response(await service.list_courses(request["db"], request["user"]))


async def course_detail(request: web.Request) -> web.Response:
    try:
        course_id = int(request.match_info["course_id"])
    except ValueError:
        return json_error("Kurs identifikatori noto'g'ri", 400)
    payload = await service.get_course(request["db"], request["user"], course_id)
    if not payload:
        return json_error("Kurs topilmadi", 404)
    return web.json_response(payload)


async def lesson_complete(request: web.Request) -> web.Response:
    body = await request.json()
    try:
        course_id = int(request.match_info["course_id"])
        lesson_id = int(request.match_info["lesson_id"])
        stars = int(body.get("stars") or 0)
    except ValueError:
        return json_error("Identifikator noto'g'ri", 400)
    try:
        result = await service.complete_lesson(
            request["db"], request["user"], course_id, lesson_id, stars
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response(result)


async def tests(request: web.Request) -> web.Response:
    return web.json_response(await service.list_tests(request["db"], request["user"]))


async def test_detail(request: web.Request) -> web.Response:
    try:
        test_id = int(request.match_info["test_id"])
    except ValueError:
        return json_error("Test identifikatori noto'g'ri", 400)
    payload = await service.get_test(request["db"], test_id)
    if not payload:
        return json_error("Test topilmadi", 404)
    return web.json_response(payload)


async def test_finish(request: web.Request) -> web.Response:
    body = await request.json()
    try:
        test_id = int(request.match_info["test_id"])
    except ValueError:
        return json_error("Test identifikatori noto'g'ri", 400)
    try:
        result = await service.finish_test(
            request["db"], request["user"], test_id, body.get("answers") or []
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response(result)


async def ai_chat(request: web.Request) -> web.Response:
    body = await request.json()
    message = (body.get("message") or "").strip()
    if not message:
        return json_error("Savol yozilmagan", 400)
    from bot.services.ai_service import AIService

    reply = await AIService(request["db"]).chat(request["user"].id, message[:2000])
    return web.json_response({"reply": reply})


async def admin_overview(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    return web.json_response(await service.admin_overview(request["db"]))


async def admin_users(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    return web.json_response(await service.admin_users(request["db"]))


async def admin_set_role(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    body = await request.json()
    try:
        await service.set_web_role(
            request["db"], actor, int(request.match_info["user_id"]), body.get("role") or ""
        )
    except PermissionError as exc:
        return json_error(str(exc), 403)
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response({"ok": True})


async def admin_block(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    body = await request.json()
    try:
        await service.block_web_user(
            request["db"],
            actor,
            int(request.match_info["user_id"]),
            body.get("duration") or "Muddatsiz",
            (body.get("reason") or "Qoidabuzarlik").strip(),
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response({"ok": True})


async def admin_unblock(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    try:
        await service.unblock_web_user(
            request["db"], actor, int(request.match_info["user_id"])
        )
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response({"ok": True})


async def admin_courses(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    return web.json_response(
        await service.list_courses(request["db"], request["user"], admin=True)
    )


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "webapp" / "public" / "uploads"
UPLOAD_TYPES = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".txt", ".zip", ".mp4", ".mp3",
}


async def admin_upload(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    reader = await request.multipart()
    field = await reader.next()
    filename = getattr(field, "filename", None) if field else None
    if not filename:
        return json_error("Fayl tanlanmagan", 400)
    suffix = Path(filename).suffix.lower()
    if suffix not in UPLOAD_TYPES:
        return json_error("Bu fayl turi qabul qilinmaydi", 400)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_DIR / stored
    size = 0
    with dest.open("wb") as handle:
        while True:
            chunk = await field.read_chunk(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > 20 * 1024 * 1024:
                handle.close()
                dest.unlink(missing_ok=True)
                return json_error("Fayl 20 MB dan katta", 400)
            handle.write(chunk)
    kind = "image" if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"} else "file"
    return web.json_response({
        "url": f"/uploads/{stored}",
        "title": Path(filename).name[:255],
        "type": kind,
    })


async def admin_create_course(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    try:
        course = await service.create_course(request["db"], actor, await request.json())
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response(course)


async def admin_delete_course(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    try:
        await service.delete_course(request["db"], actor, int(request.match_info["course_id"]))
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response({"ok": True})


async def admin_tests(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    return web.json_response(await service.list_tests(request["db"], request["user"]))


async def admin_generate(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if len(text) < 10:
        return json_error("Dars matni juda qisqa", 400)
    return web.json_response(await service.generate_questions(request["db"], actor, text))


async def admin_save_test(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    try:
        test = await service.save_generated_test(request["db"], actor, await request.json())
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response(test)


async def admin_delete_test(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    try:
        await service.delete_test(request["db"], actor, int(request.match_info["test_id"]))
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response({"ok": True})


async def admin_audiences(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    return web.json_response(await service.audience_counts(request["db"]))


async def admin_broadcast(request: web.Request) -> web.Response:
    actor = _admin(request)
    if not actor:
        return json_error("Ruxsat yo'q", 403)
    try:
        result = await service.send_broadcast(request["db"], actor, await request.json())
    except ValueError as exc:
        return json_error(str(exc), 400)
    return web.json_response(result)


async def admin_audit(request: web.Request) -> web.Response:
    if not _admin(request):
        return json_error("Ruxsat yo'q", 403)
    feed = await service.audit_feed(request["db"])
    feed["services"] = await service.service_health()
    return web.json_response(feed)


async def _prepare_schema(_app: web.Application) -> None:
    """Create tables the same way the bot does, so the web app can run alone."""
    import bot.models  # noqa: F401
    from bot.models.base import Base, engine
    from bot.models.migrations import apply_additive_migrations

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await apply_additive_migrations(engine)
        logger.info("Database jadvallar tayyor")
    except Exception:
        logger.exception("Jadvallarni yaratib bo'lmadi. PostgreSQL ni tekshiring.")


def create_app() -> web.Application:
    app = web.Application(
        middlewares=[cors_middleware, error_middleware, db_middleware, auth_middleware],
        client_max_size=32 * 1024 * 1024,
    )
    app.on_startup.append(_prepare_schema)
    app.router.add_get("/health", health)
    app.router.add_post("/api/v1/auth/telegram", auth_telegram)
    app.router.add_post("/api/v1/auth/local", auth_local)
    app.router.add_post("/api/v1/auth/login", auth_login)
    app.router.add_post("/api/v1/auth/register", auth_register)
    app.router.add_get("/api/v1/me", me)
    app.router.add_post("/api/v1/me/category", set_category)
    app.router.add_get("/api/v1/bootstrap", bootstrap)
    app.router.add_get("/api/v1/courses", courses)
    app.router.add_get("/api/v1/courses/{course_id}", course_detail)
    app.router.add_post("/api/v1/courses/{course_id}/lessons/{lesson_id}/complete", lesson_complete)
    app.router.add_get("/api/v1/tests", tests)
    app.router.add_get("/api/v1/tests/{test_id}", test_detail)
    app.router.add_post("/api/v1/tests/{test_id}/finish", test_finish)
    app.router.add_post("/api/v1/ai/chat", ai_chat)
    app.router.add_get("/api/v1/admin/overview", admin_overview)
    app.router.add_get("/api/v1/admin/users", admin_users)
    app.router.add_post("/api/v1/admin/users/{user_id}/role", admin_set_role)
    app.router.add_post("/api/v1/admin/users/{user_id}/block", admin_block)
    app.router.add_post("/api/v1/admin/users/{user_id}/unblock", admin_unblock)
    app.router.add_get("/api/v1/admin/courses", admin_courses)
    app.router.add_post("/api/v1/admin/uploads", admin_upload)
    app.router.add_post("/api/v1/admin/courses", admin_create_course)
    app.router.add_delete("/api/v1/admin/courses/{course_id}", admin_delete_course)
    app.router.add_get("/api/v1/admin/tests", admin_tests)
    app.router.add_post("/api/v1/admin/tests/generate", admin_generate)
    app.router.add_post("/api/v1/admin/tests", admin_save_test)
    app.router.add_delete("/api/v1/admin/tests/{test_id}", admin_delete_test)
    app.router.add_get("/api/v1/admin/audiences", admin_audiences)
    app.router.add_post("/api/v1/admin/broadcast", admin_broadcast)
    app.router.add_get("/api/v1/admin/audit", admin_audit)
    return app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    port = int(os.environ.get("WEB_API_PORT", "8081"))
    logger.info("Web App API: http://0.0.0.0:%s", port)
    web.run_app(create_app(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
