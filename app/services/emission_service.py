"""Protocol emission engine. Block-based reward distribution from usage score."""
from decimal import Decimal
from datetime import datetime
from math import sqrt

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User, Wallet, Transaction
from app.models.protocol import ProtocolState, ProtocolBlock
from app.models.transaction import TransactionType


# System bucket telegram_user_ids (reserved negative)
BUCKET_STAKERS = -100
BUCKET_DEVCO = -101
BUCKET_VALIDATORS = -102
BUCKET_FOUNDATION = -103
BUCKET_ELIGIBLE = -104

BUCKETS = [
    (BUCKET_STAKERS, "bucket_stakers"),
    (BUCKET_DEVCO, "bucket_devco"),
    (BUCKET_VALIDATORS, "bucket_validators"),
    (BUCKET_FOUNDATION, "bucket_foundation"),
    (BUCKET_ELIGIBLE, "bucket_eligible"),
]

SPLIT_STAKERS = Decimal("0.10")
SPLIT_DEVCO = Decimal("0.15")
SPLIT_VALIDATORS = Decimal("0.05")
SPLIT_FOUNDATION = Decimal("0.10")
SPLIT_ELIGIBLE = Decimal("0.60")


def _round_karma(v: Decimal) -> Decimal:
    return round(v, 3)


def _ensure_buckets_exist(db: Session) -> dict[int, User]:
    """Create system bucket users+wallets if missing. Returns tg_id -> User."""
    result = {}
    for tg_id, username in BUCKETS:
        u = db.query(User).filter(User.telegram_user_id == tg_id).first()
        if not u:
            u = User(
                telegram_user_id=tg_id,
                username=username,
                is_system_wallet=True,
                is_event_wallet=False,
            )
            db.add(u)
            db.flush()
            w = Wallet(user_id=u.id)
            db.add(w)
            db.flush()
        result[tg_id] = u
    return result


def _get_protocol_state(db: Session) -> ProtocolState:
    state = db.query(ProtocolState).first()
    if not state:
        state = ProtocolState()
        db.add(state)
        db.flush()
    return state


def _usage_score_and_eligible(db: Session, since: datetime) -> tuple[Decimal, list[tuple[User, Decimal]]]:
    """
    Compute total usage score S and eligible receivers (to_user_id from SEND).
    Per receiver: sum(amount_karma) * sqrt(tx_count)
    Returns (S, [(user, score), ...])
    """
    rows = (
        db.query(
            Transaction.to_user_id,
            func.coalesce(func.sum(Transaction.amount_karma), 0).label("total"),
            func.count(Transaction.id).label("cnt"),
        )
        .filter(Transaction.type == TransactionType.SEND)
        .filter(Transaction.created_at >= since)
        .filter(Transaction.to_user_id.isnot(None))
        .group_by(Transaction.to_user_id)
        .all()
    )
    total_s = Decimal("0")
    eligible: list[tuple[User, Decimal]] = []
    for to_user_id, total_amt, cnt in rows:
        if not to_user_id or cnt == 0:
            continue
        user = db.query(User).filter(User.id == to_user_id).first()
        if not user or user.is_system_wallet:
            continue
        total = Decimal(str(float(total_amt)))
        score = total * Decimal(str(sqrt(int(cnt))))
        total_s += score
        eligible.append((user, score))
    return total_s, eligible


def run_emission_once(db: Session) -> dict:
    """
    Run one protocol emission block.
    - Usage score from SEND txs since last_processed_ts
    - R = min(max(S/K, min_reward), max_reward)
    - Splits: stakers 10%, devco 15%, validators 5%, foundation 10%, eligible 60%
    - Distribute stakers pro-rata to stakers; eligible pro-rata by usage score
    """
    settings = get_settings()
    K = settings.protocol_k
    min_reward = Decimal(str(settings.protocol_min_reward))
    max_reward = Decimal(str(settings.protocol_max_reward))

    _ensure_buckets_exist(db)
    state = _get_protocol_state(db)
    since = state.last_processed_ts or datetime(1970, 1, 1)

    total_s, eligible = _usage_score_and_eligible(db, since)
    tx_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.type == TransactionType.SEND)
        .filter(Transaction.created_at >= since)
        .scalar()
        or 0
    )

    r_raw = total_s / K if K else Decimal("0")
    deferred = Decimal(str(float(state.deferred_rewards or 0)))
    if r_raw > max_reward:
        deferred += r_raw - max_reward
        r_raw = max_reward
    r = max(min(r_raw, max_reward), min_reward)

    if r <= 0:
        state.updated_at = datetime.utcnow()
        db.commit()
        return {
            "block_id": (state.last_emitted_block_id or 0) + 1,
            "reward_total": 0,
            "message": "No emission (zero usage or reward)",
            "processed_tx_count": tx_count,
        }

    block_id = (state.last_emitted_block_id or 0) + 1
    amt_stakers = r * SPLIT_STAKERS
    amt_devco = r * SPLIT_DEVCO
    amt_validators = r * SPLIT_VALIDATORS
    amt_foundation = r * SPLIT_FOUNDATION
    amt_eligible = r * SPLIT_ELIGIBLE

    buckets = _ensure_buckets_exist(db)
    now = datetime.utcnow()

    # Credit buckets (devco, validators, foundation hold; stakers & eligible distribute immediately)
    for tg_id, amt in [
        (BUCKET_DEVCO, amt_devco),
        (BUCKET_VALIDATORS, amt_validators),
        (BUCKET_FOUNDATION, amt_foundation),
    ]:
        u = buckets[tg_id]
        w = db.query(Wallet).filter(Wallet.user_id == u.id).first()
        if w:
            w.karma_balance += _round_karma(amt)
        tx = Transaction(
            type=TransactionType.PROTOCOL_EMISSION,
            to_user_id=u.id,
            amount_karma=_round_karma(amt),
            block_id=block_id,
            meta={"bucket": u.username},
        )
        db.add(tx)

    # Distribute stakers bucket pro-rata to stakers
    total_staked = (
        db.query(func.coalesce(func.sum(Wallet.staked_amount), 0))
        .join(User, Wallet.user_id == User.id)
        .filter(User.is_system_wallet == False)
        .filter(Wallet.staked_amount > 0)
        .scalar()
        or Decimal("0")
    )
    stakers_distributed = Decimal("0")
    if total_staked and total_staked > 0 and amt_stakers > 0:
        stakers = (
            db.query(User, Wallet)
            .join(Wallet, User.id == Wallet.user_id)
            .filter(User.is_system_wallet == False)
            .filter(Wallet.staked_amount > 0)
            .all()
        )
        for user, w in stakers:
            share = (w.staked_amount / total_staked) * amt_stakers
            share = _round_karma(share)
            if share <= 0:
                continue
            w.karma_balance += share
            w.rewards_earned += share
            stakers_distributed += share
            db.add(
                Transaction(
                    type=TransactionType.STAKE_REWARD,
                    to_user_id=user.id,
                    amount_karma=share,
                    block_id=block_id,
                    meta={"emission_block": block_id},
                )
            )

    # Distribute eligible bucket pro-rata by usage score
    eligible_distributed = Decimal("0")
    if total_s and total_s > 0 and amt_eligible > 0 and eligible:
        for user, score in eligible:
            share = (score / total_s) * amt_eligible
            share = _round_karma(share)
            if share <= 0:
                continue
            w = db.query(Wallet).filter(Wallet.user_id == user.id).first()
            if w:
                w.karma_balance += share
                w.rewards_earned += share
            eligible_distributed += share
            db.add(
                Transaction(
                    type=TransactionType.PROTOCOL_EMISSION,
                    to_user_id=user.id,
                    amount_karma=share,
                    block_id=block_id,
                    meta={"eligible_reward": True},
                )
            )

    # Update state
    state.last_processed_ts = now
    state.last_emitted_block_id = block_id
    state.deferred_rewards = deferred
    state.updated_at = now

    pb = ProtocolBlock(
        block_id=block_id,
        emitted_at=now,
        reward_total=float(r),
        splits_applied={
            "stakers": float(amt_stakers),
            "devco": float(amt_devco),
            "validators": float(amt_validators),
            "foundation": float(amt_foundation),
            "eligible": float(amt_eligible),
            "stakers_distributed": float(stakers_distributed),
            "eligible_distributed": float(eligible_distributed),
            "deferred": float(deferred),
        },
        processed_tx_count=tx_count,
    )
    db.add(pb)
    db.commit()

    return {
        "block_id": block_id,
        "reward_total": float(r),
        "usage_score": float(total_s),
        "splits": {
            "stakers": float(amt_stakers),
            "devco": float(amt_devco),
            "validators": float(amt_validators),
            "foundation": float(amt_foundation),
            "eligible": float(amt_eligible),
        },
        "stakers_distributed": float(stakers_distributed),
        "eligible_distributed": float(eligible_distributed),
        "deferred": float(deferred),
        "processed_tx_count": tx_count,
        "message": f"Emission block {block_id} completed",
    }
