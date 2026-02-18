"""Backup and restore service for admin."""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import User, Wallet, Transaction, Referral, ProtocolState, ProtocolBlock
from app.db.session import Base, engine


def export_backup(db: Session) -> dict:
    """Export full DB state as JSON-serializable dict."""
    users = []
    for u in db.query(User).all():
        users.append({
            "id": str(u.id),
            "telegram_user_id": u.telegram_user_id,
            "username": u.username,
            "is_system_wallet": u.is_system_wallet,
            "is_event_wallet": u.is_event_wallet,
        })
    wallets = []
    for w in db.query(Wallet).all():
        wallets.append({
            "user_id": str(w.user_id),
            "karma_balance": float(w.karma_balance),
            "chiliz_balance": float(w.chiliz_balance),
            "staked_amount": float(w.staked_amount),
            "rewards_earned": float(w.rewards_earned),
        })
    transactions = []
    for t in db.query(Transaction).all():
        transactions.append({
            "type": t.type.value,
            "actor_user_id": str(t.actor_user_id) if t.actor_user_id else None,
            "from_user_id": str(t.from_user_id) if t.from_user_id else None,
            "to_user_id": str(t.to_user_id) if t.to_user_id else None,
            "amount_karma": float(t.amount_karma) if t.amount_karma else None,
            "amount_chiliz": float(t.amount_chiliz) if t.amount_chiliz else None,
            "meta": t.meta,
        })
    referrals = []
    for r in db.query(Referral).all():
        referrals.append({
            "invitee_user_id": str(r.invitee_user_id),
            "inviter_user_id": str(r.inviter_user_id),
            "rewarded": r.rewarded,
        })
    protocol_state = None
    ps = db.query(ProtocolState).first()
    if ps:
        protocol_state = {
            "last_processed_ts": ps.last_processed_ts.isoformat() if ps.last_processed_ts else None,
            "last_emitted_block_id": ps.last_emitted_block_id,
            "deferred_rewards": float(ps.deferred_rewards or 0),
        }
    protocol_blocks = []
    for pb in db.query(ProtocolBlock).all():
        protocol_blocks.append({
            "block_id": pb.block_id,
            "emitted_at": pb.emitted_at.isoformat() if pb.emitted_at else None,
            "reward_total": float(pb.reward_total),
            "processed_tx_count": pb.processed_tx_count,
        })
    return {
        "users": users,
        "wallets": wallets,
        "transactions": transactions,
        "referrals": referrals,
        "protocol_state": protocol_state,
        "protocol_blocks": protocol_blocks,
    }


def restore_backup(db: Session, data: dict) -> dict:
    """
    Restore from backup. Replaces all data.
    Clears existing tables then inserts from backup.
    """
    db.query(Referral).delete()
    db.query(Transaction).delete()
    db.query(Wallet).delete()
    db.query(User).delete()
    db.query(ProtocolBlock).delete()
    # Reset protocol_state
    for ps in db.query(ProtocolState).all():
        ps.last_processed_ts = None
        ps.last_emitted_block_id = None
        ps.deferred_rewards = 0
    db.commit()
    db.expire_all()

    user_id_map = {}
    for u_data in data.get("users", []):
        u = User(
            id=UUID(u_data["id"]),
            telegram_user_id=u_data["telegram_user_id"],
            username=u_data["username"],
            is_system_wallet=u_data.get("is_system_wallet", False),
            is_event_wallet=u_data.get("is_event_wallet", False),
        )
        db.add(u)
        user_id_map[u_data["id"]] = u.id
    db.flush()

    for w_data in data.get("wallets", []):
        w = Wallet(
            user_id=UUID(w_data["user_id"]),
            karma_balance=Decimal(str(w_data["karma_balance"])),
            chiliz_balance=Decimal(str(w_data["chiliz_balance"])),
            staked_amount=Decimal(str(w_data["staked_amount"])),
            rewards_earned=Decimal(str(w_data["rewards_earned"])),
        )
        db.add(w)
    db.flush()

    for t_data in data.get("transactions", []):
        t = Transaction(
            type=t_data["type"],
            actor_user_id=UUID(t_data["actor_user_id"]) if t_data.get("actor_user_id") else None,
            from_user_id=UUID(t_data["from_user_id"]) if t_data.get("from_user_id") else None,
            to_user_id=UUID(t_data["to_user_id"]) if t_data.get("to_user_id") else None,
            amount_karma=Decimal(str(t_data["amount_karma"])) if t_data.get("amount_karma") is not None else None,
            amount_chiliz=Decimal(str(t_data["amount_chiliz"])) if t_data.get("amount_chiliz") is not None else None,
            meta=t_data.get("meta"),
        )
        db.add(t)
    db.flush()

    for r_data in data.get("referrals", []):
        r = Referral(
            invitee_user_id=UUID(r_data["invitee_user_id"]),
            inviter_user_id=UUID(r_data["inviter_user_id"]),
            rewarded=r_data.get("rewarded", False),
        )
        db.add(r)

    # Restore protocol state
    if data.get("protocol_state"):
        ps_data = data["protocol_state"]
        ps = db.query(ProtocolState).first()
        if ps:
            from datetime import datetime
            ps.last_processed_ts = datetime.fromisoformat(ps_data["last_processed_ts"]) if ps_data.get("last_processed_ts") else None
            ps.last_emitted_block_id = ps_data.get("last_emitted_block_id")
            ps.deferred_rewards = Decimal(str(ps_data.get("deferred_rewards", 0)))

    db.commit()
    return {"message": "Restore complete", "users": len(data.get("users", []))}
