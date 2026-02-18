"""Wallet and transfer endpoints."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DbSession, get_current_user, require_user_match
from app.schemas.wallet import SendRequest, SendResponse, SwapRequest
from app.services.wallet_service import send_karma, swap_karma_chiliz

router = APIRouter()


@router.post("/send", response_model=SendResponse)
def send(db: DbSession, req: SendRequest, current_user: dict = Depends(get_current_user)):
    """Send Karma from sender to recipient."""
    require_user_match(req.sender_id, current_user)
    result = send_karma(db, req)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    return SendResponse(message=result["message"])


@router.post("/swap")
def swap(db: DbSession, req: SwapRequest, current_user: dict = Depends(get_current_user)):
    """Swap Karma ↔ Chiliz 1:1."""
    require_user_match(req.user_id, current_user)
    result = swap_karma_chiliz(db, req.user_id, req.direction, req.amount)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    return {"message": result["message"]}
