"""Wallet and transfer service."""
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User, Wallet, Transaction, Referral
from app.models.transaction import TransactionType
from app.schemas.wallet import SendRequest


MIN_AMOUNT = Decimal("0.001")
DISPLAY_DECIMALS = 3


def round_karma(value: Decimal) -> Decimal:
    """Round to display precision."""
    return round(value, DISPLAY_DECIMALS)


def send_karma(db: Session, req: SendRequest) -> dict:
    """
    Transfer Karma from sender to recipient.
    Returns dict with success/error info.
    """
    sender = db.query(User).filter(User.telegram_user_id == int(req.sender_id)).first()
    recipient = db.query(User).filter(User.telegram_user_id == int(req.recipient_id)).first()

    if not sender or not recipient:
        return {"error": "User(s) not found", "status": 404}

    if not sender.wallet or not recipient.wallet:
        return {"error": "Wallet(s) not found", "status": 404}

    amount = Decimal(str(req.amount))
    if amount < MIN_AMOUNT:
        return {"error": "Minimum amount is 0.001 Karma", "status": 400}

    if sender.wallet.karma_balance < amount:
        return {"error": "Insufficient Karma balance", "status": 400}

    now = datetime.utcnow()

    # Debit sender
    sender.wallet.karma_balance -= amount
    sender.wallet.karma_balance = round_karma(sender.wallet.karma_balance)

    # Credit recipient
    recipient.wallet.karma_balance += amount
    recipient.wallet.karma_balance = round_karma(recipient.wallet.karma_balance)

    meta = {"note": req.note} if req.note else None

    # Record transaction (append-only, one row per transfer)
    tx = Transaction(
        type=TransactionType.SEND,
        actor_user_id=sender.id,
        from_user_id=sender.id,
        to_user_id=recipient.id,
        amount_karma=amount,
        meta=meta,
    )
    db.add(tx)

    # Referral bonus: if recipient was invited by sender, and not yet rewarded
    ref = db.query(Referral).filter(Referral.invitee_user_id == recipient.id).first()
    if ref and ref.inviter_user_id == sender.id and not ref.rewarded:
        bonus = Decimal("3")
        sender.wallet.karma_balance += bonus
        sender.wallet.karma_balance = round_karma(sender.wallet.karma_balance)
        ref.rewarded = True
        tx_bonus = Transaction(
            type=TransactionType.REFERRAL_BONUS,
            actor_user_id=sender.id,
            to_user_id=sender.id,
            amount_karma=bonus,
            meta={"invitee": str(recipient.telegram_user_id)},
        )
        db.add(tx_bonus)

    db.commit()
    return {"message": f"{req.amount} Karma sent from {req.sender_id} to {req.recipient_id}"}


def mint_karma(db: Session, user_id: str, amount: float) -> dict:
    """Admin: mint Karma to user."""
    user = db.query(User).filter(User.telegram_user_id == int(user_id)).first()
    if not user or not user.wallet:
        return {"error": "User not found", "status": 404}

    amt = Decimal(str(amount))
    if amt < MIN_AMOUNT:
        return {"error": "Minimum amount is 0.001 Karma", "status": 400}

    user.wallet.karma_balance += amt
    user.wallet.karma_balance = round_karma(user.wallet.karma_balance)

    tx = Transaction(
        type=TransactionType.MINT,
        actor_user_id=user.id,
        to_user_id=user.id,
        amount_karma=amt,
    )
    db.add(tx)
    db.commit()
    return {"message": f"Minted {amount} Karma to user {user_id}"}


def stake_karma(db: Session, user_id: str, amount: float) -> dict:
    """Stake Karma from liquid balance."""
    user = db.query(User).filter(User.telegram_user_id == int(user_id)).first()
    if not user or not user.wallet:
        return {"error": "User not found", "status": 404}

    amt = Decimal(str(amount))
    if amt < MIN_AMOUNT:
        return {"error": "Minimum amount is 0.001 Karma", "status": 400}

    if user.wallet.karma_balance < amt:
        return {"error": "Insufficient balance", "status": 400}

    user.wallet.karma_balance -= amt
    user.wallet.karma_balance = round_karma(user.wallet.karma_balance)
    user.wallet.staked_amount += amt
    user.wallet.staked_amount = round_karma(user.wallet.staked_amount)

    tx = Transaction(
        type=TransactionType.STAKE_DEPOSIT,
        actor_user_id=user.id,
        to_user_id=user.id,
        amount_karma=amt,
    )
    db.add(tx)
    db.commit()
    return {
        "message": f"✅ {amount} Karma deposited successfully.",
        "next_unlock_ts": None,
    }


def unstake_karma(db: Session, user_id: str, amount: float) -> dict:
    """Unstake Karma back to liquid balance."""
    user = db.query(User).filter(User.telegram_user_id == int(user_id)).first()
    if not user or not user.wallet:
        return {"error": "User not found", "status": 404}

    amt = Decimal(str(amount))
    if amt < MIN_AMOUNT:
        return {"error": "Minimum amount is 0.001 Karma", "status": 400}

    if user.wallet.staked_amount < amt:
        return {"error": "Not enough staked Karma", "status": 400}

    user.wallet.staked_amount -= amt
    user.wallet.staked_amount = round_karma(user.wallet.staked_amount)
    user.wallet.karma_balance += amt
    user.wallet.karma_balance = round_karma(user.wallet.karma_balance)

    tx = Transaction(
        type=TransactionType.UNSTAKE_WITHDRAW,
        actor_user_id=user.id,
        from_user_id=user.id,
        to_user_id=user.id,
        amount_karma=amt,
    )
    db.add(tx)
    db.commit()
    return {
        "message": f"Unstaked {amount} Karma successfully.",
        "unstaked_amount": float(round_karma(amt)),
        "remaining_staked": float(user.wallet.staked_amount),
    }


def swap_karma_chiliz(db: Session, user_id: str, direction: str, amount: float) -> dict:
    """Swap Karma ↔ Chiliz 1:1. direction: karma_to_chiliz | chiliz_to_karma."""
    user = db.query(User).filter(User.telegram_user_id == int(user_id)).first()
    if not user or not user.wallet:
        return {"error": "User not found", "status": 404}

    amt = Decimal(str(amount))
    if amt < MIN_AMOUNT:
        return {"error": "Minimum amount is 0.001", "status": 400}

    w = user.wallet
    if direction == "karma_to_chiliz":
        if w.karma_balance < amt:
            return {"error": "Insufficient Karma balance", "status": 400}
        w.karma_balance -= amt
        w.chiliz_balance += amt
        amount_karma = -amt
        amount_chiliz = amt
        msg = f"Swapped {amount} Karma to Chiliz."
    else:  # chiliz_to_karma
        if w.chiliz_balance < amt:
            return {"error": "Insufficient Chiliz balance", "status": 400}
        w.chiliz_balance -= amt
        w.karma_balance += amt
        amount_karma = amt
        amount_chiliz = -amt
        msg = f"Swapped {amount} Chiliz to Karma."

    w.karma_balance = round_karma(w.karma_balance)
    w.chiliz_balance = round_karma(w.chiliz_balance)

    tx = Transaction(
        type=TransactionType.SWAP,
        actor_user_id=user.id,
        to_user_id=user.id,
        amount_karma=amount_karma,
        amount_chiliz=amount_chiliz,
        meta={"direction": direction, "amount": str(amt)},
    )
    db.add(tx)
    db.commit()
    return {"message": msg}


def get_stake_info(db: Session, user_id: str) -> dict | None:
    """Get stake info for user."""
    user = db.query(User).filter(User.telegram_user_id == int(user_id)).first()
    if not user or not user.wallet:
        return None

    w = user.wallet
    total_staked = float(w.staked_amount)
    return {
        "total_staked": round(total_staked, DISPLAY_DECIMALS),
        "next_unlock_ts": None,
        "available_to_unstake": round(total_staked, DISPLAY_DECIMALS),
        "liquid_karma": round(float(w.karma_balance), DISPLAY_DECIMALS),
    }
