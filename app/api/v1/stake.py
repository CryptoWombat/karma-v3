"""Stake and unstake endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Path

from app.core.dependencies import DbSession, get_current_user, require_user_match
from app.schemas.wallet import StakeRequest, UnstakeRequest, StakeInfoResponse
from app.services.wallet_service import stake_karma, unstake_karma, get_stake_info

router = APIRouter()

_USER_ID_PATH = Path(..., pattern=r"^\d+$", description="Telegram user ID")


@router.post("/stake")
def stake(db: DbSession, req: StakeRequest, current_user: dict = Depends(get_current_user)):
    """Stake Karma from liquid balance."""
    require_user_match(req.user_id, current_user)
    result = stake_karma(db, req.user_id, req.amount)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    return result


@router.post("/unstake")
def unstake(db: DbSession, req: UnstakeRequest, current_user: dict = Depends(get_current_user)):
    """Unstake Karma back to liquid balance."""
    require_user_match(req.user_id, current_user)
    result = unstake_karma(db, req.user_id, req.amount)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    return result


@router.get("/stake/info/{user_id}", response_model=StakeInfoResponse)
def stake_info(db: DbSession, user_id: str = _USER_ID_PATH, current_user: dict = Depends(get_current_user)):
    """Get stake info for user."""
    require_user_match(user_id, current_user)
    data = get_stake_info(db, user_id)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return StakeInfoResponse(**data)
