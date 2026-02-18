"""Transaction history endpoints."""
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query

from app.core.dependencies import DbSession, get_current_user, require_user_match
from app.schemas.transaction import TransactionListResponse
from app.services.transaction_service import get_user_transactions

router = APIRouter()

_USER_ID_PATH = Path(..., pattern=r"^\d+$", description="Telegram user ID")


@router.get("/transactions", response_model=TransactionListResponse)
def list_transactions(
    db: DbSession,
    user_id: str = Query(..., pattern=r"^\d+$", description="Telegram user ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: Literal["asc", "desc"] = Query("desc"),
    current_user: dict = Depends(get_current_user),
):
    """Paginated transaction history for a user."""
    require_user_match(user_id, current_user)
    transactions, total = get_user_transactions(
        db, int(user_id), limit=limit, offset=offset, sort=sort
    )
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        limit=limit,
        offset=offset,
    )
