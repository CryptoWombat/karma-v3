"""Auth endpoints: Telegram initData validation and JWT issuance."""
from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.core.auth import validate_telegram_init_data, create_jwt
from app.schemas.auth import TelegramAuthRequest, TelegramAuthResponse

router = APIRouter()


@router.post("/auth/telegram", response_model=TelegramAuthResponse)
def auth_telegram(req: TelegramAuthRequest):
    """
    Verify Telegram WebApp initData and issue JWT.
    Requires TELEGRAM_BOT_TOKEN to be configured.
    """
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram auth not configured",
        )
    data = validate_telegram_init_data(req.init_data, settings.telegram_bot_token)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired initData",
        )
    user_str = data.get("user")
    if not user_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user in initData",
        )
    import json
    try:
        user = json.loads(user_str)
        user_id = str(user.get("id", ""))
        username = user.get("username", "") or user.get("first_name", "user")
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user in initData",
        )
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user id in initData",
        )

    token = create_jwt(
        telegram_user_id=user_id,
        username=username,
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_expire_minutes,
    )
    return TelegramAuthResponse(
        access_token=token,
        user_id=user_id,
        username=username,
    )
