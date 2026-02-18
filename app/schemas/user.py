"""User schemas."""
from pydantic import BaseModel, Field

from app.schemas.common import TelegramUserId


class RegisterRequest(BaseModel):
    """Request to register a user."""

    user_id: TelegramUserId
    username: str = Field(..., min_length=1, max_length=255)


class RegisterResponse(BaseModel):
    """Response after registration."""

    message: str
    status: str | None = None  # "created" | "exists" for register_if_needed


class UserListItem(BaseModel):
    """User in admin list."""

    user_id: str
    username: str
    created_at: int | None
    karma_balance: float
    chiliz_balance: float
    staked: float


class UserListResponse(BaseModel):
    """Paginated user list."""

    users: list[UserListItem]
    total: int
    limit: int
    offset: int


class CreateEventWalletRequest(BaseModel):
    """Admin request to create event wallet."""

    name: str = Field(..., min_length=1, max_length=255)


class UnregisterRequest(BaseModel):
    """Admin request to unregister a user."""

    user_id: TelegramUserId


class SelfUnregisterRequest(BaseModel):
    """User self-unregister (user_id only for test mode when JWT not required)."""

    user_id: TelegramUserId | None = None


class BalanceResponse(BaseModel):
    """Wallet balance response."""

    user_id: str
    balance: float
    staked: float
    rewards: float
    chiliz: float
    created_at: int | None = None
