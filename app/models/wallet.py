"""Wallet model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction


class Wallet(Base):
    """User wallet for Karma and Chiliz tokens."""

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    karma_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        default=Decimal("0"),
        nullable=False,
    )
    chiliz_balance: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        default=Decimal("0"),
        nullable=False,
    )
    staked_amount: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        default=Decimal("0"),
        nullable=False,
    )
    rewards_earned: Mapped[Decimal] = mapped_column(
        Numeric(24, 6),
        default=Decimal("0"),
        nullable=False,
    )
    next_unlock_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="wallet")

    def __repr__(self) -> str:
        return f"<Wallet user_id={self.user_id} karma={self.karma_balance}>"
