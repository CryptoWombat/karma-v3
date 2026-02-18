"""Wallet and transaction schemas."""
from pydantic import BaseModel, Field

from app.schemas.common import TelegramUserId


class StakeRequest(BaseModel):
    """Request to stake Karma."""

    user_id: TelegramUserId
    amount: float = Field(..., gt=0, ge=0.001)


class UnstakeRequest(BaseModel):
    """Request to unstake Karma."""

    user_id: TelegramUserId
    amount: float = Field(..., gt=0, ge=0.001)


class StakeInfoResponse(BaseModel):
    """Stake info response."""

    total_staked: float
    next_unlock_ts: int | None
    available_to_unstake: float
    liquid_karma: float


class SendRequest(BaseModel):
    """Request to send Karma."""

    sender_id: TelegramUserId
    recipient_id: TelegramUserId
    amount: float = Field(..., gt=0, ge=0.001, description="Amount of Karma (min 0.001)")
    note: str | None = Field(None, max_length=30)


class SendResponse(BaseModel):
    """Response after send."""

    message: str


class SwapRequest(BaseModel):
    """Request to swap Karma ↔ Chiliz (1:1)."""

    user_id: TelegramUserId
    direction: str = Field(..., pattern=r"^(karma_to_chiliz|chiliz_to_karma)$")
    amount: float = Field(..., gt=0, ge=0.001)


class MintRequest(BaseModel):
    """Admin request to mint Karma."""

    user_id: TelegramUserId
    amount: float = Field(..., gt=0, ge=0.001)
