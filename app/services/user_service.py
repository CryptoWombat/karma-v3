"""User and wallet service."""
from sqlalchemy.orm import Session

from app.models import User, Wallet
from app.schemas.user import RegisterRequest


def get_user_by_telegram_id(db: Session, telegram_user_id: int) -> User | None:
    """Get user by Telegram ID."""
    return db.query(User).filter(User.telegram_user_id == telegram_user_id).first()


def register_user(db: Session, req: RegisterRequest) -> tuple[User, Wallet, bool]:
    """
    Register a user (idempotent).
    Returns (user, wallet, created) where created=True if new user.
    """
    telegram_id = int(req.user_id)
    existing = get_user_by_telegram_id(db, telegram_id)

    if existing:
        if not existing.username or existing.username != req.username:
            existing.username = req.username
            db.commit()
            db.refresh(existing)
        wallet = existing.wallet
        if not wallet:
            wallet = Wallet(user_id=existing.id)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        return existing, wallet, False

    user = User(
        telegram_user_id=telegram_id,
        username=req.username,
    )
    db.add(user)
    db.flush()

    wallet = Wallet(user_id=user.id)
    db.add(wallet)
    db.commit()
    db.refresh(user)
    db.refresh(wallet)

    return user, wallet, True


def search_users(db: Session, q: str, limit: int = 10, exclude_user_id: int | None = None) -> list[dict]:
    """Search users by username or telegram user_id. Excludes system/event wallets."""
    if not q or len(q.strip()) < 2:
        return []
    q_clean = q.strip().lower()
    query = (
        db.query(User)
        .filter(User.is_system_wallet == False, User.is_event_wallet == False)
        .filter(User.username.ilike(f"%{q_clean}%"))
    )
    if exclude_user_id is not None:
        query = query.filter(User.telegram_user_id != exclude_user_id)
    users = query.limit(limit).all()
    results = [{"user_id": str(u.telegram_user_id), "username": u.username or ""} for u in users]
    # Also match user_id if q is numeric
    if q_clean.isdigit() and len(results) < limit:
        by_id = (
            db.query(User)
            .filter(User.is_system_wallet == False, User.is_event_wallet == False)
            .filter(User.telegram_user_id == int(q_clean))
        )
        if exclude_user_id is not None:
            by_id = by_id.filter(User.telegram_user_id != exclude_user_id)
        extra = by_id.first()
        if extra and not any(r["user_id"] == str(extra.telegram_user_id) for r in results):
            results.insert(0, {"user_id": str(extra.telegram_user_id), "username": extra.username or ""})
    return results[:limit]


def list_users(db: Session, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
    """List users with wallets (paginated). Excludes system wallets. Returns (users, total)."""
    q = db.query(User, Wallet).join(Wallet, User.id == Wallet.user_id).filter(User.is_system_wallet == False)
    total = q.count()
    rows = q.order_by(User.created_at.desc()).limit(limit).offset(offset).all()
    users = []
    for u, w in rows:
        users.append({
            "user_id": str(u.telegram_user_id),
            "username": u.username,
            "created_at": int(u.created_at.timestamp()) if u.created_at else None,
            "karma_balance": round(float(w.karma_balance), 3),
            "chiliz_balance": round(float(w.chiliz_balance), 3),
            "staked": round(float(w.staked_amount), 3),
        })
    return users, total


def create_event_wallet(db: Session, name: str) -> dict:
    """Admin: create event wallet user. Uses negative telegram_user_id for uniqueness."""
    next_id = db.query(User).filter(User.telegram_user_id < 0).count()
    telegram_id = -(next_id + 1)  # -1, -2, -3, ...
    existing = get_user_by_telegram_id(db, telegram_id)
    if existing:
        return {"error": "Event wallet already exists", "status": 400}
    user = User(
        telegram_user_id=telegram_id,
        username=name,
        is_event_wallet=True,
    )
    db.add(user)
    db.flush()
    wallet = Wallet(user_id=user.id)
    db.add(wallet)
    db.commit()
    db.refresh(user)
    return {
        "message": f"Event wallet '{name}' created",
        "user_id": str(telegram_id),
        "username": name,
    }


def unregister_user_admin(db: Session, telegram_user_id: int) -> dict:
    """Admin: delete user and cascade (wallet, referrals). Transactions keep with nulled user refs."""
    user = get_user_by_telegram_id(db, telegram_user_id)
    if not user:
        return {"error": "User not found", "status": 404}
    if user.is_system_wallet or user.is_event_wallet:
        return {"error": "Cannot unregister system or event wallet", "status": 400}
    db.delete(user)
    db.commit()
    return {"message": f"User {telegram_user_id} unregistered"}


def get_wallet_balance(db: Session, telegram_user_id: int) -> dict | None:
    """Get balance info for user, or None if not found."""
    user = get_user_by_telegram_id(db, telegram_user_id)
    if not user or not user.wallet:
        return None

    w = user.wallet
    return {
        "user_id": str(telegram_user_id),
        "balance": round(float(w.karma_balance), 3),
        "staked": round(float(w.staked_amount), 3),
        "rewards": round(float(w.rewards_earned), 6),
        "chiliz": round(float(w.chiliz_balance), 3),
        "created_at": int(user.created_at.timestamp()) if user.created_at else None,
    }
