"""Public stats endpoint."""
from fastapi import APIRouter
from sqlalchemy import func

from app.core.dependencies import DbSession
from app.models import User, Wallet, Transaction
from app.models.transaction import TransactionType
from app.services.emission_service import BUCKET_FOUNDATION

router = APIRouter()


@router.get("/stats")
def public_stats(db: DbSession):
    """Public network stats (no auth required)."""
    from app.models.protocol import ProtocolBlock

    user_count = db.query(User).filter(User.is_system_wallet == False).count()
    total_minted = (
        db.query(func.coalesce(func.sum(Transaction.amount_karma), 0))
        .filter(Transaction.type == TransactionType.MINT)
        .scalar()
        or 0
    )
    total_transferred = (
        db.query(func.coalesce(func.sum(Transaction.amount_karma), 0))
        .filter(Transaction.type == TransactionType.SEND)
        .scalar()
        or 0
    )
    tx_count = db.query(Transaction).filter(Transaction.type == TransactionType.SEND).count()

    total_karma = (
        db.query(func.coalesce(func.sum(Wallet.karma_balance), 0)).scalar() or 0
    )
    total_staked = (
        db.query(func.coalesce(func.sum(Wallet.staked_amount), 0)).scalar() or 0
    )
    total_rewards = (
        db.query(func.coalesce(func.sum(Wallet.rewards_earned), 0)).scalar() or 0
    )

    # Last protocol block
    last_block = db.query(ProtocolBlock).order_by(ProtocolBlock.emitted_at.desc()).first()
    last_block_id = last_block.block_id if last_block else None
    last_block_at = last_block.emitted_at.isoformat().replace("+00:00", "Z") if last_block and last_block.emitted_at else None

    # Foundation bucket balance
    foundation_user = db.query(User).filter(User.telegram_user_id == BUCKET_FOUNDATION).first()
    foundation_balance = 0.0
    if foundation_user:
        w = db.query(Wallet).filter(Wallet.user_id == foundation_user.id).first()
        if w:
            foundation_balance = float(w.karma_balance)

    return {
        "network_status": "operational",
        "users": user_count,
        "transactions": tx_count,
        "minted": float(total_minted),
        "transferred": float(total_transferred),
        "total_in_circulation": float(total_karma) + float(total_staked) + float(total_rewards),
        "available": float(total_karma),
        "savings": float(total_staked),
        "rewards_earned": float(total_rewards),
        "last_block_id": last_block_id,
        "last_block_at": last_block_at,
        "foundation_balance": foundation_balance,
    }
