"""Referral schemas."""
from pydantic import BaseModel, Field

from app.schemas.common import TelegramUserId


class ReferralRequest(BaseModel):
    """Request to record referral."""

    inviter_id: TelegramUserId
    new_user_id: TelegramUserId


class ReferralStatusResponse(BaseModel):
    """Referral status response."""

    invited_by: str | None
    rewarded: bool
