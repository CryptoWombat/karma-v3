"""User endpoints."""
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from app.config import get_settings
from app.core.dependencies import DbSession, get_current_user
from app.schemas.user import RegisterRequest, RegisterResponse, BalanceResponse, SelfUnregisterRequest
from app.services.user_service import register_user, get_wallet_balance, unregister_user_admin, search_users, get_user_by_telegram_id

router = APIRouter()

_USER_ID_PATH = Path(..., pattern=r"^\d+$", description="Telegram user ID")


@router.get("/me")
def users_me(db: DbSession, current_user: dict = Depends(get_current_user)):
    """
    Get current user profile and balance (requires JWT).
    Returns user_id, username, balance, staked, rewards, chiliz, created_at.
    """
    settings = get_settings()
    user_id = current_user.get("sub")
    if not user_id and settings.jwt_required:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")
    user = get_user_by_telegram_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    data = get_wallet_balance(db, int(user_id))
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {
        "user_id": str(user_id),
        "username": user.username or "",
        **data,
    }


@router.post("/register", response_model=RegisterResponse)
def register(db: DbSession, req: RegisterRequest):
    """Register a new user (idempotent)."""
    _, _, created = register_user(db, req)
    return RegisterResponse(
        message=f"User {req.username} registered",
        status="created" if created else "exists",
    )


@router.post("/unregister")
def self_unregister(db: DbSession, current_user: dict = Depends(get_current_user), req: SelfUnregisterRequest = Body(default=SelfUnregisterRequest())):
    """User unregisters themselves. Requires JWT; deletes own account and data."""
    from app.config import get_settings
    user_id = current_user.get("sub")
    if not user_id and get_settings().jwt_required:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not user_id and req and req.user_id:
        user_id = req.user_id  # Test mode: allow user_id in body when JWT not required
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id required")
    result = unregister_user_admin(db, int(user_id))
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    return result


@router.get("/search")
def user_search(db: DbSession, q: str = Query(..., min_length=2), current_user: dict = Depends(get_current_user)):
    """Search users by username or ID. Returns users who have used the app (for recipient autocomplete)."""
    exclude_id = current_user.get("sub")
    exclude_int = int(exclude_id) if exclude_id else None
    return {"users": search_users(db, q, limit=10, exclude_user_id=exclude_int)}


@router.get("/balance/{user_id}", response_model=BalanceResponse)
def balance(db: DbSession, user_id: str = _USER_ID_PATH, current_user: dict = Depends(get_current_user)):
    """Get user balance. When JWT required, user_id must match token."""
    if current_user.get("sub") and str(current_user["sub"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another user's balance")
    data = get_wallet_balance(db, int(user_id))
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return BalanceResponse(**data)
