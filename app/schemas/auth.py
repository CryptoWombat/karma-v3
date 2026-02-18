"""Auth schemas."""
from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    """Request to authenticate via Telegram initData."""

    init_data: str = Field(..., min_length=1, description="Telegram WebApp initData query string")


class TelegramAuthResponse(BaseModel):
    """Response with JWT token."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
