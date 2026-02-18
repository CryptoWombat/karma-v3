"""Referral model."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Referral(Base):
    """Referral link: invitee was invited by inviter."""

    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    invitee_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    inviter_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invitee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[invitee_user_id],
        back_populates="referrals_received",
    )
    inviter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[inviter_user_id],
        back_populates="referrals_made",
    )
