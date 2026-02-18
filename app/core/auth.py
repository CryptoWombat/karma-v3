"""Telegram Mini App initData validation and JWT handling."""
import hashlib
import hmac
import time
from urllib.parse import parse_qs, unquote

from jose import JWTError, jwt


def validate_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict | None:
    """
    Validate Telegram WebApp initData and return parsed data if valid.
    Returns None if invalid or expired.
    """
    if not init_data or not bot_token:
        return None

    parsed: dict[str, str] = {}
    hash_value = ""
    for chunk in init_data.split("&"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        if key == "hash":
            hash_value = value
            continue
        parsed[key] = unquote(value)

    if not hash_value:
        return None

    data_check_str = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed.keys()))
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()
    computed = hmac.new(
        secret_key,
        data_check_str.encode(),
        hashlib.sha256,
    ).hexdigest()
    if computed != hash_value:
        return None

    if "auth_date" in parsed:
        try:
            auth_date = int(parsed["auth_date"])
            if time.time() - auth_date > max_age_seconds:
                return None
        except (ValueError, TypeError):
            return None

    return parsed


def create_jwt(telegram_user_id: str, username: str, secret: str, algorithm: str, expire_minutes: int) -> str:
    """Create JWT for authenticated user."""
    from datetime import datetime, timezone, timedelta

    exp = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": telegram_user_id,
        "username": username,
        "exp": exp,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm)


def decode_jwt(token: str, secret: str, algorithm: str) -> dict | None:
    """Decode and validate JWT. Returns payload or None."""
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError:
        return None
