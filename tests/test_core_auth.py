"""Unit tests for auth module."""
import hashlib
import hmac
import json
from urllib.parse import quote

import pytest
from app.core.auth import validate_telegram_init_data, create_jwt, decode_jwt


def _make_valid_init_data(bot_token: str, user_id: int = 1001, username: str = "alice") -> str:
    """Create valid initData for testing (with correct HMAC)."""
    import time
    user = json.dumps({"id": user_id, "username": username, "first_name": "Alice"})
    auth_date = str(int(time.time()))  # Current time so it's not expired
    parsed = {"user": user, "auth_date": auth_date}
    data_check_str = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed.keys()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_str.encode(), hashlib.sha256).hexdigest()
    return f"auth_date={auth_date}&hash={hash_val}&user={quote(user)}"


class TestValidateTelegramInitData:
    def test_valid_init_data(self):
        """Valid initData with correct hash returns parsed data."""
        token = "test-bot-token-12345"
        init_data = _make_valid_init_data(token)
        result = validate_telegram_init_data(init_data, token, max_age_seconds=999999)
        assert result is not None
        assert "user" in result
        assert json.loads(result["user"])["id"] == 1001

    def test_invalid_hash(self):
        """Wrong hash returns None."""
        token = "test-bot-token"
        init_data = _make_valid_init_data(token)
        bad_init = init_data.replace("hash=", "hash=x")
        result = validate_telegram_init_data(bad_init, token)
        assert result is None

    def test_wrong_token(self):
        """InitData signed with different token returns None."""
        token = "real-token"
        init_data = _make_valid_init_data(token)
        result = validate_telegram_init_data(init_data, "different-token")
        assert result is None

    def test_expired(self):
        """Expired auth_date returns None."""
        import time
        token = "test-token"
        user = json.dumps({"id": 1001, "username": "alice"})
        auth_date = str(int(time.time() - 86400))  # 24h ago
        parsed = {"user": user, "auth_date": auth_date}
        data_check_str = "\n".join(f"{k}={parsed[k]}" for k in sorted(parsed.keys()))
        secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        hash_val = hmac.new(secret_key, data_check_str.encode(), hashlib.sha256).hexdigest()
        from urllib.parse import quote
        init_data = f"auth_date={auth_date}&hash={hash_val}&user={quote(user)}"
        result = validate_telegram_init_data(init_data, token, max_age_seconds=3600)
        assert result is None


class TestJWT:
    def test_create_and_decode(self):
        """JWT roundtrip works."""
        token = create_jwt("1001", "alice", "secret", "HS256", 60)
        payload = decode_jwt(token, "secret", "HS256")
        assert payload is not None
        assert payload["sub"] == "1001"
        assert payload["username"] == "alice"
        assert "exp" in payload

    def test_decode_invalid_returns_none(self):
        """Invalid JWT returns None."""
        assert decode_jwt("invalid", "secret", "HS256") is None
