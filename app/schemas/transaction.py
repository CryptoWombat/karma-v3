"""Transaction schemas."""
from datetime import datetime

from pydantic import BaseModel


class TransactionResponse(BaseModel):
    """Single transaction in history."""

    id: str
    created_at: datetime
    type: str
    actor_user_id: str | None
    from_user_id: str | None
    to_user_id: str | None
    amount_karma: float | None
    amount_chiliz: float | None
    meta: dict | None


class TransactionListResponse(BaseModel):
    """Paginated transaction list."""

    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int
