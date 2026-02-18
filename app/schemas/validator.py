"""Validator admin schemas."""
from pydantic import BaseModel, Field


class CreateValidatorKeyRequest(BaseModel):
    """Request to create validator API key."""

    name: str | None = Field(None, max_length=255)


class RevokeValidatorKeyRequest(BaseModel):
    """Request to revoke validator key."""

    key_id: str
