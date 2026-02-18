"""Transaction history service."""
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session

from app.models import User, Transaction
from app.models.transaction import TransactionType


def get_user_transactions(
    db: Session,
    telegram_user_id: int,
    limit: int = 50,
    offset: int = 0,
    sort: str = "desc",
) -> tuple[list[dict], int]:
    """
    Get paginated transactions for a user.
    Returns (transactions, total_count).
    User is included if they are actor, from, or to.
    """
    user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
    if not user:
        return [], 0

    q = db.query(Transaction).filter(
        or_(
            Transaction.actor_user_id == user.id,
            Transaction.from_user_id == user.id,
            Transaction.to_user_id == user.id,
        )
    )
    total = q.count()

    order_fn = desc if sort == "desc" else asc
    rows = (
        q.order_by(order_fn(Transaction.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )

    # Resolve telegram_user_id for actor, from, to
    telegram_map: dict[str, str] = {}
    for tx in rows:
        for uid in (tx.actor_user_id, tx.from_user_id, tx.to_user_id):
            if uid and str(uid) not in telegram_map:
                u = db.query(User).filter(User.id == uid).first()
                telegram_map[str(uid)] = str(u.telegram_user_id) if u else str(uid)

    transactions = []
    for tx in rows:
        transactions.append({
            "id": str(tx.id),
            "created_at": tx.created_at,
            "type": tx.type.value,
            "actor_user_id": telegram_map.get(str(tx.actor_user_id)) if tx.actor_user_id else None,
            "from_user_id": telegram_map.get(str(tx.from_user_id)) if tx.from_user_id else None,
            "to_user_id": telegram_map.get(str(tx.to_user_id)) if tx.to_user_id else None,
            "amount_karma": float(tx.amount_karma) if tx.amount_karma is not None else None,
            "amount_chiliz": float(tx.amount_chiliz) if tx.amount_chiliz is not None else None,
            "meta": tx.meta,
        })
    return transactions, total
