"""Validator API data service - aggregates for external validators."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User, Wallet, Transaction
from app.models.transaction import TransactionType


def _utc_now() -> datetime:
    """UTC now (timezone-aware for consistency)."""
    return datetime.now(timezone.utc)


def _window_start(now: datetime, hours: int) -> datetime:
    """Start of window N hours ago."""
    return (now - timedelta(hours=hours)).replace(tzinfo=timezone.utc) if now.tzinfo else now - timedelta(hours=hours)


def _window_start_days(now: datetime, days: int) -> datetime:
    """Start of window N days ago."""
    return (now - timedelta(days=days)).replace(tzinfo=timezone.utc) if now.tzinfo else now - timedelta(days=days)


def get_validator_snapshot(
    db: Session,
    include_top: int = 10,
    timestamp: datetime | None = None,
) -> dict:
    """Build full validator snapshot with users, balances, transactions, inflation, top wallets."""
    now = timestamp or _utc_now()
    # Use naive datetime for SQLite compatibility if needed
    now_naive = now.replace(tzinfo=None) if now.tzinfo else now
    w1h = _window_start_days(now_naive, 0) - timedelta(hours=1)
    w24h = _window_start_days(now_naive, 1)
    w7d = _window_start_days(now_naive, 7)
    w30d = _window_start_days(now_naive, 30)

    # Users & wallets
    user_count = db.query(User).filter(User.is_system_wallet == False).count()
    wallet_count = (
        db.query(Wallet)
        .join(User, Wallet.user_id == User.id)
        .filter(User.is_system_wallet == False)
        .filter(
            (Wallet.karma_balance > 0)
            | (Wallet.staked_amount > 0)
            | (Wallet.chiliz_balance > 0)
            | (Wallet.rewards_earned > 0)
        )
        .count()
    )
    active_24h = (
        db.query(Transaction.actor_user_id)
        .filter(Transaction.created_at >= w24h)
        .filter(Transaction.type.in_([TransactionType.SEND, TransactionType.RECEIVE]))
        .distinct()
        .count()
    )

    # Balances
    total_karma = (
        db.query(func.coalesce(func.sum(Wallet.karma_balance), 0)).scalar() or Decimal("0")
    )
    total_chiliz = (
        db.query(func.coalesce(func.sum(Wallet.chiliz_balance), 0)).scalar() or Decimal("0")
    )
    total_staked = (
        db.query(func.coalesce(func.sum(Wallet.staked_amount), 0)).scalar() or Decimal("0")
    )
    total_rewards = (
        db.query(func.coalesce(func.sum(Wallet.rewards_earned), 0)).scalar() or Decimal("0")
    )

    # Transaction metrics (SEND + RECEIVE volume)
    tx_types = [TransactionType.SEND, TransactionType.RECEIVE]
    tx_24h = _tx_metrics(db, w24h, now_naive, tx_types)
    tx_7d = _tx_metrics(db, w7d, now_naive, tx_types)
    tx_30d = _tx_metrics(db, w30d, now_naive, tx_types)

    # Inflation (minted Karma by type)
    mint_types = [
        TransactionType.MINT,
        TransactionType.PROTOCOL_EMISSION,
        TransactionType.STAKERS_DISTRIBUTED,
        TransactionType.REFERRAL_INVITE,
        TransactionType.REFERRAL_BONUS,
    ]
    inf_1h = _inflation_breakdown(db, w1h, now_naive, mint_types)
    inf_24h = _inflation_breakdown(db, w24h, now_naive, mint_types)
    inf_7d = _inflation_breakdown(db, w7d, now_naive, mint_types)
    inf_30d = _inflation_breakdown(db, w30d, now_naive, mint_types)

    # Top wallets (exclude system)
    top = _top_wallets(db, limit=include_top)

    windows = {
        "1h": {"start": _iso(w1h), "end": _iso(now_naive)},
        "24h": {"start": _iso(w24h), "end": _iso(now_naive)},
        "7d": {"start": _iso(w7d), "end": _iso(now_naive)},
        "30d": {"start": _iso(w30d), "end": _iso(now_naive)},
    }

    return {
        "snapshot_at": _iso(now_naive),
        "windows": windows,
        "users": {
            "user_count": user_count,
            "wallet_count": wallet_count,
            "active_wallets_24h": active_24h,
        },
        "balances": {
            "total_karma_balance": round(float(total_karma), 2),
            "total_chiliz_balance": round(float(total_chiliz), 2),
            "total_staked": round(float(total_staked), 2),
            "total_rewards_earned": round(float(total_rewards), 2),
        },
        "transactions": {
            "24h": tx_24h,
            "7d": tx_7d,
            "30d": tx_30d,
        },
        "inflation": {
            "1h": inf_1h,
            "24h": inf_24h,
            "7d": inf_7d,
            "30d": inf_30d,
        },
        "top_wallets": top,
    }


def get_inflation_only(db: Session, timestamp: datetime | None = None) -> dict:
    """Inflation data and windows only."""
    now = timestamp or _utc_now()
    now_naive = now.replace(tzinfo=None) if now.tzinfo else now
    w1h = now_naive - timedelta(hours=1)
    w24h = now_naive - timedelta(days=1)
    w7d = now_naive - timedelta(days=7)
    w30d = now_naive - timedelta(days=30)

    mint_types = [
        TransactionType.MINT,
        TransactionType.PROTOCOL_EMISSION,
        TransactionType.STAKERS_DISTRIBUTED,
        TransactionType.REFERRAL_INVITE,
        TransactionType.REFERRAL_BONUS,
    ]
    return {
        "snapshot_at": _iso(now_naive),
        "windows": {
            "1h": {"start": _iso(w1h), "end": _iso(now_naive)},
            "24h": {"start": _iso(w24h), "end": _iso(now_naive)},
            "7d": {"start": _iso(w7d), "end": _iso(now_naive)},
            "30d": {"start": _iso(w30d), "end": _iso(now_naive)},
        },
        "inflation": {
            "1h": _inflation_breakdown(db, w1h, now_naive, mint_types),
            "24h": _inflation_breakdown(db, w24h, now_naive, mint_types),
            "7d": _inflation_breakdown(db, w7d, now_naive, mint_types),
            "30d": _inflation_breakdown(db, w30d, now_naive, mint_types),
        },
    }


def get_transactions_only(db: Session, timestamp: datetime | None = None) -> dict:
    """Transaction metrics and windows only."""
    now = timestamp or _utc_now()
    now_naive = now.replace(tzinfo=None) if now.tzinfo else now
    w24h = now_naive - timedelta(days=1)
    w7d = now_naive - timedelta(days=7)
    w30d = now_naive - timedelta(days=30)

    tx_types = [TransactionType.SEND, TransactionType.RECEIVE]
    return {
        "snapshot_at": _iso(now_naive),
        "windows": {
            "24h": {"start": _iso(w24h), "end": _iso(now_naive)},
            "7d": {"start": _iso(w7d), "end": _iso(now_naive)},
            "30d": {"start": _iso(w30d), "end": _iso(now_naive)},
        },
        "transactions": {
            "24h": _tx_metrics(db, w24h, now_naive, tx_types),
            "7d": _tx_metrics(db, w7d, now_naive, tx_types),
            "30d": _tx_metrics(db, w30d, now_naive, tx_types),
        },
    }


def get_leaderboard(db: Session, limit: int = 10, sort_by: str = "total") -> dict:
    """Top wallets by balance + staked."""
    top = _top_wallets(db, limit=limit, sort_by=sort_by)
    return {
        "generated_at": _iso(_utc_now().replace(tzinfo=None) if _utc_now().tzinfo else _utc_now()),
        "top_wallets": top,
    }


def _tx_metrics(
    db: Session,
    start: datetime,
    end: datetime,
    types: list[TransactionType],
) -> dict:
    """Transaction count and volumes for SEND/RECEIVE in window."""
    q = db.query(
        func.count(Transaction.id).label("count"),
        func.coalesce(func.sum(Transaction.amount_karma), 0).label("karma"),
        func.coalesce(func.sum(Transaction.amount_chiliz), 0).label("chiliz"),
    ).filter(Transaction.created_at >= start, Transaction.created_at <= end)
    if types:
        q = q.filter(Transaction.type.in_(types))
    row = q.first()
    return {
        "count": row.count or 0,
        "volume_karma": round(float(row.karma or 0), 2),
        "volume_chiliz": round(float(row.chiliz or 0), 2),
    }


def _inflation_breakdown(
    db: Session,
    start: datetime,
    end: datetime,
    types: list[TransactionType],
) -> dict:
    """Karma minted by type in window."""
    # Sum by type
    by_type = (
        db.query(Transaction.type, func.coalesce(func.sum(Transaction.amount_karma), 0))
        .filter(Transaction.created_at >= start, Transaction.created_at <= end)
        .filter(Transaction.type.in_(types))
        .group_by(Transaction.type)
        .all()
    )
    breakdown = {
        "mint_admin": 0.0,
        "protocol_emission": 0.0,
        "stake_rewards": 0.0,
        "referral_rewards": 0.0,
    }
    total = 0.0
    for tx_type, amt in by_type:
        v = float(amt)
        total += v
        if tx_type == TransactionType.MINT:
            breakdown["mint_admin"] += v
        elif tx_type == TransactionType.PROTOCOL_EMISSION:
            breakdown["protocol_emission"] += v
        elif tx_type == TransactionType.STAKERS_DISTRIBUTED:
            breakdown["stake_rewards"] += v
        elif tx_type in (TransactionType.REFERRAL_INVITE, TransactionType.REFERRAL_BONUS):
            breakdown["referral_rewards"] += v

    return {
        "karma_minted": round(total, 2),
        "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
    }


def _top_wallets(db: Session, limit: int = 10, sort_by: str = "total") -> list[dict]:
    """Top wallets sorted by total (balance + staked) or balance only."""
    q = (
        db.query(User, Wallet)
        .join(Wallet, User.id == Wallet.user_id)
        .filter(User.is_system_wallet == False)
    )
    rows = q.all()
    combined = [
        {
            "user_id": str(u.telegram_user_id),
            "username": u.username,
            "karma_balance": round(float(w.karma_balance), 2),
            "staked": round(float(w.staked_amount), 2),
            "total": round(float(w.karma_balance) + float(w.staked_amount), 2),
        }
        for u, w in rows
    ]
    if sort_by == "balance":
        combined.sort(key=lambda x: x["karma_balance"], reverse=True)
    else:
        combined.sort(key=lambda x: x["total"], reverse=True)
    for i, item in enumerate(combined[:limit], 1):
        item["rank"] = i
    return combined[:limit]


def _iso(dt: datetime) -> str:
    """ISO 8601 string (UTC)."""
    s = dt.isoformat()
    if "+" not in s and "Z" not in s:
        s += "Z"
    return s.replace("+00:00", "Z")
