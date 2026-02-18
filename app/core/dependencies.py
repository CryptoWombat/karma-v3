"""FastAPI dependencies."""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.auth import decode_jwt
from app.db.session import get_db


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    Require valid JWT and return payload (sub=user_id, username).
    Returns 401 if invalid or missing.
    """
    settings = get_settings()
    if getattr(settings, "jwt_required", True):
        token = (authorization or "").replace("Bearer ", "").strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        payload = decode_jwt(token, settings.jwt_secret, settings.jwt_algorithm)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return payload
    # Bypass for testing when jwt_required=False
    return {"sub": None, "username": "test"}


def require_admin(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Dependency: require valid admin API key."""
    settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API not configured",
        )
    token = (authorization or "").replace("Bearer ", "").strip()
    if token != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized",
        )


def require_validator(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
) -> None:
    """Dependency: require valid validator API key (from DB or env)."""
    from app.models.validator_key import ValidatorApiKey, hash_key

    token = (authorization or "").replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "code": "INVALID_VALIDATOR_KEY"},
        )
    key_hash = hash_key(token)
    db_key = db.query(ValidatorApiKey).filter(
        ValidatorApiKey.key_hash == key_hash,
        ValidatorApiKey.revoked_at.is_(None),
    ).first()
    if db_key:
        return
    settings = get_settings()
    if settings.validator_keys_set and token in settings.validator_keys_set:
        return
    has_any_keys = db.query(ValidatorApiKey).filter(ValidatorApiKey.revoked_at.is_(None)).count() > 0
    if not has_any_keys and not settings.validator_keys_set:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Validator API not configured",
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "unauthorized", "code": "INVALID_VALIDATOR_KEY"},
    )


def require_user_match(user_id: str, current_user: dict) -> None:
    """Raise 403 if JWT user_id doesn't match (when JWT is present)."""
    sub = current_user.get("sub")
    if sub is not None and str(sub) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID does not match authentication")


# Type aliases for injection
DbSession = Annotated[Session, Depends(get_db)]
