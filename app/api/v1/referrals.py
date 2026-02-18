"""Referral endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Path

from app.core.dependencies import DbSession, get_current_user, require_user_match
from app.schemas.referral import ReferralRequest, ReferralStatusResponse
from app.services.referral_service import record_referral, get_referral_status

router = APIRouter()

_USER_ID_PATH = Path(..., pattern=r"^\d+$", description="Telegram user ID")


@router.post("/referrals")
def create_referral(db: DbSession, req: ReferralRequest, current_user: dict = Depends(get_current_user)):
    """Record referral: new_user was invited by inviter. Gives 1 Karma to inviter."""
    require_user_match(req.inviter_id, current_user)
    result = record_referral(db, req.inviter_id, req.new_user_id)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    return result


@router.get("/referrals/status/{user_id}", response_model=ReferralStatusResponse)
def referral_status(db: DbSession, user_id: str = _USER_ID_PATH, current_user: dict = Depends(get_current_user)):
    """Get referral status for user."""
    require_user_match(user_id, current_user)
    return ReferralStatusResponse(**get_referral_status(db, user_id))
