"""User model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.wallet import Wallet
    from app.models.referral import Referral


class User(Base):
    """User account (Telegram user)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_system_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    is_event_wallet: Mapped[bool] = mapped_column(Boolean, default=False)

    wallet: Mapped["Wallet"] = relationship(
        "Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    referrals_made: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.inviter_user_id",
        back_populates="inviter",
        cascade="all, delete-orphan",
    )
    referrals_received: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.invitee_user_id",
        back_populates="invitee",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.telegram_user_id} ({self.username})>"
