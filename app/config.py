"""Application configuration."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite:///./karma.db"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_required: bool = True  # Set False for testing / backward compat

    # Telegram
    telegram_bot_token: Optional[str] = None

    # Admin
    admin_api_key: Optional[str] = None

    # Validator (comma-separated for multiple keys; VALIDATOR_API_KEY also supported for single key)
    validator_api_keys: Optional[str] = None
    validator_api_key: Optional[str] = None

    # Redis
    redis_url: Optional[str] = None

    # CORS (comma-separated origins, e.g. "https://web.telegram.org,https://myapp.com". Empty = allow all.)
    cors_allowed_origins: str = ""

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # Rate limits (requests per minute). Set rate_limit_disabled=True to skip (e.g. tests).
    rate_limit_disabled: bool = False
    rate_limit_user: int = 60
    rate_limit_admin: int = 100
    rate_limit_validator: int = 300
    rate_limit_public: int = 120

    # Protocol (from PRD)
    protocol_interval_seconds: int = 600
    protocol_scheduled_enabled: bool = True  # Set False to disable auto emission
    protocol_k: int = 1000
    protocol_min_reward: float = 5.0
    protocol_max_reward: float = 100.0

    @property
    def is_sqlite(self) -> bool:
        """True if using SQLite (local dev)."""
        return "sqlite" in self.database_url

    @property
    def cors_origins_list(self) -> list[str]:
        """List of allowed CORS origins. Empty means allow all (*)."""
        if not self.cors_allowed_origins or not self.cors_allowed_origins.strip():
            return ["*"]
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def validator_keys_set(self) -> set[str]:
        """Set of valid validator API keys (from VALIDATOR_API_KEYS and/or VALIDATOR_API_KEY)."""
        keys: set[str] = set()
        if self.validator_api_keys:
            keys |= {k.strip() for k in self.validator_api_keys.split(",") if k.strip()}
        if self.validator_api_key and self.validator_api_key.strip():
            keys.add(self.validator_api_key.strip())
        # Dev fallback: when using SQLite and no keys configured, allow local dev keys
        if not keys and self.is_sqlite:
            keys = {"validator-key-1", "validator-key-2"}
        return keys


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
