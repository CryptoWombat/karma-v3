"""Referral service."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import User, Referral, Transaction
from app.models.transaction import TransactionType
from app.services.wallet_service import round_karma


def record_referral(db: Session, inviter_id: str, new_user_id: str) -> dict:
    """
    Record that new_user was referred by inviter.
    Gives 1 Karma to inviter. Idempotent if already referred.
    """
    if inviter_id == new_user_id:
        return {"error": "Cannot refer yourself", "status": 400}

    inviter = db.query(User).filter(User.telegram_user_id == int(inviter_id)).first()
    invitee = db.query(User).filter(User.telegram_user_id == int(new_user_id)).first()

    if not inviter or not invitee:
        return {"error": "User(s) not found", "status": 404}

    if not inviter.wallet or not invitee.wallet:
        return {"error": "Wallet(s) not found", "status": 404}

    existing = db.query(Referral).filter(Referral.invitee_user_id == invitee.id).first()
    if existing:
        return {"message": "User already referred."}

    ref = Referral(invitee_user_id=invitee.id, inviter_user_id=inviter.id)
    db.add(ref)

    bonus = Decimal("1")
    inviter.wallet.karma_balance += bonus
    inviter.wallet.karma_balance = round_karma(inviter.wallet.karma_balance)

    tx = Transaction(
        type=TransactionType.REFERRAL_INVITE,
        actor_user_id=inviter.id,
        to_user_id=inviter.id,
        amount_karma=bonus,
        meta={"invitee_telegram_id": new_user_id},
    )
    db.add(tx)
    db.commit()
    return {"message": f"Referral from {inviter_id} to {new_user_id} recorded."}


def get_referral_status(db: Session, user_id: str) -> dict:
    """Get referral status for user (invited_by, rewarded)."""
    user = db.query(User).filter(User.telegram_user_id == int(user_id)).first()
    if not user:
        return {"invited_by": None, "rewarded": False}

    ref = db.query(Referral).filter(Referral.invitee_user_id == user.id).first()
    if not ref:
        return {"invited_by": None, "rewarded": False}

    inviter = db.query(User).filter(User.id == ref.inviter_user_id).first()
    return {
        "invited_by": str(inviter.telegram_user_id) if inviter else None,
        "rewarded": ref.rewarded,
    }
