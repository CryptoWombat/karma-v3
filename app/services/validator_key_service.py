"""Validator API key management."""
import secrets
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.validator_key import ValidatorApiKey, hash_key


def create_validator_key(db: Session, name: str | None = None) -> dict:
    """
    Create a new validator API key.
    Returns plaintext key once (not retrievable later).
    """
    plain = f"vk_{secrets.token_urlsafe(32)}"
    key_hash = hash_key(plain)
    existing = db.query(ValidatorApiKey).filter(ValidatorApiKey.key_hash == key_hash).first()
    if existing:
        return create_validator_key(db, name)  # Retry on collision
    key = ValidatorApiKey(key_hash=key_hash, name=name or "")
    db.add(key)
    db.commit()
    return {
        "message": "Validator key created. Save the key securely - it cannot be retrieved again.",
        "key": plain,
        "id": str(key.id),
        "name": name or "",
        "created_at": key.created_at.isoformat() if key.created_at else None,
    }


def list_validator_keys(db: Session) -> list[dict]:
    """List validator keys (without plaintext)."""
    keys = db.query(ValidatorApiKey).order_by(ValidatorApiKey.created_at.desc()).all()
    return [
        {
            "id": str(k.id),
            "name": k.name or "",
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "revoked_at": k.revoked_at.isoformat() if k.revoked_at else None,
            "revoked": k.revoked_at is not None,
        }
        for k in keys
    ]


def revoke_validator_key(db: Session, key_id: str) -> dict:
    """Revoke a validator key by ID."""
    try:
        uid = UUID(key_id)
    except ValueError:
        return {"error": "Invalid key ID", "status": 400}
    key = db.query(ValidatorApiKey).filter(ValidatorApiKey.id == uid).first()
    if not key:
        return {"error": "Key not found", "status": 404}
    if key.revoked_at:
        return {"error": "Key already revoked", "status": 400}
    key.revoked_at = datetime.utcnow()
    db.commit()
    return {"message": "Validator key revoked"}
