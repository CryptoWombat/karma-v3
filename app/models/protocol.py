"""Protocol emission state models."""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.session import Base


class ProtocolState(Base):
    """Tracks protocol emission state across restarts."""

    __tablename__ = "protocol_state"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    last_processed_ts: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_emitted_block_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deferred_rewards: Mapped[float] = mapped_column(Numeric(24, 6), default=0, nullable=False)
    utilization_window: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    saturated_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ProtocolBlock(Base):
    """Record of each emission block."""

    __tablename__ = "protocol_blocks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    block_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    emitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reward_total: Mapped[float] = mapped_column(Numeric(24, 6), nullable=False)
    splits_applied: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_tx_count: Mapped[int] = mapped_column(default=0, nullable=False)
