"""Telegram initData check and Web App session tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from bot.config import settings


def _secret() -> str:
    return settings.jwt_secret or settings.secret_key


def verify_init_data(init_data: str, max_age_seconds: int = 86400) -> dict:
    """Validate Telegram WebApp initData. Returns the parsed user dict."""
    if not init_data or not settings.bot_token:
        raise ValueError("Telegram ma'lumoti yoki bot token yo'q")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("initData imzosi yo'q")

    data_check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise ValueError("Telegram imzosi noto'g'ri")

    auth_date = int(pairs.get("auth_date") or 0)
    if auth_date and time.time() - auth_date > max_age_seconds:
        raise ValueError("Telegram sessiyasi eskirgan. Ilovani qayta oching")

    user_raw = pairs.get("user")
    if not user_raw:
        raise ValueError("Telegram foydalanuvchisi topilmadi")
    return json.loads(user_raw)


def issue_token(user_id: int) -> str:
    payload = {"uid": user_id, "exp": int(time.time()) + 14 * 24 * 3600}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def read_token(token: str) -> int:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Sessiya yaroqsiz") from exc
    expected = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Sessiya yaroqsiz")
    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    if int(payload.get("exp") or 0) < time.time():
        raise ValueError("Sessiya eskirgan")
    uid = payload.get("uid")
    if not uid:
        raise ValueError("Sessiya yaroqsiz")
    return int(uid)
