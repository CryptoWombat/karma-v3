"""Shared schema types and constraints."""
from typing import Annotated

from pydantic import Field

# Telegram user IDs must be numeric strings
TelegramUserId = Annotated[str, Field(pattern=r"^\d+$", description="Telegram user ID")]
