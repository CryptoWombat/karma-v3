"""Transaction model."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TransactionType(str, enum.Enum):
    """Transaction type enum per PRD."""

    MINT = "mint"
    SEND = "send"
    RECEIVE = "receive"
    STAKE_DEPOSIT = "stake_deposit"
    UNSTAKE_WITHDRAW = "unstake_withdraw"
    STAKE_REWARD = "stake_reward"
    REFERRAL_INVITE = "referral_invite"
    REFERRAL_BONUS = "referral_bonus"
    PROTOCOL_EMISSION = "protocol_emission"
    STAKERS_DISTRIBUTED = "stakers_distributed"
    SWAP = "swap"
    EVENT_WALLET_CREATED = "event_wallet_created"


class Transaction(Base):
    """Append-only transaction log."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    from_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount_karma: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)
    amount_chiliz: Mapped[Decimal | None] = mapped_column(Numeric(24, 6), nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    block_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
