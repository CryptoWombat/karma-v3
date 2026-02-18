"""Validator API key model."""
import hashlib
import secrets
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def hash_key(plain: str) -> str:
    """SHA-256 hash of key for storage."""
    return hashlib.sha256(plain.encode()).hexdigest()


class ValidatorApiKey(Base):
    """Validator API key (hash stored, plaintext returned once on create)."""

    __tablename__ = "validator_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
