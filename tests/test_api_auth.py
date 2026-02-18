"""Auth API tests: Telegram initData validation and JWT."""
import json
from unittest.mock import patch
import pytest


@pytest.fixture
def valid_init_data():
    """Valid initData with user (for mock)."""
    user = {"id": 1001, "username": "alice", "first_name": "Alice"}
    return f"user={json.dumps(user)}&auth_date=9999999999"


class TestAuthTelegram:
    """POST /v1/auth/telegram"""

    def test_auth_503_when_not_configured(self, client):
        """Returns 503 when TELEGRAM_BOT_TOKEN not set."""
        with patch("app.api.v1.auth.get_settings") as mock:
            mock.return_value.telegram_bot_token = None
            mock.return_value.jwt_secret = "secret"
            mock.return_value.jwt_algorithm = "HS256"
            mock.return_value.jwt_expire_minutes = 60
            r = client.post("/v1/auth/telegram", json={"init_data": "user=123&auth_date=123"})
        assert r.status_code == 503
        assert "not configured" in r.json()["detail"].lower()

    def test_auth_401_invalid_init_data(self, client):
        """Returns 401 for invalid initData."""
        with patch("app.api.v1.auth.get_settings") as mock_settings:
            mock_settings.return_value.telegram_bot_token = "test-bot-token"
            mock_settings.return_value.jwt_secret = "secret"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_expire_minutes = 60
            with patch("app.api.v1.auth.validate_telegram_init_data", return_value=None):
                r = client.post("/v1/auth/telegram", json={"init_data": "invalid"})
        assert r.status_code == 401
        assert "invalid" in r.json()["detail"].lower() or "expired" in r.json()["detail"].lower()

    def test_auth_success_returns_jwt(self, client):
        """Valid initData returns JWT."""
        user_data = {"id": 1001, "username": "alice", "first_name": "Alice"}
        valid_data = {"user": json.dumps(user_data), "auth_date": "9999999999"}

        with patch("app.api.v1.auth.get_settings") as mock_settings:
            mock_settings.return_value.telegram_bot_token = "test-bot"
            mock_settings.return_value.jwt_secret = "test-jwt-secret"
            mock_settings.return_value.jwt_algorithm = "HS256"
            mock_settings.return_value.jwt_expire_minutes = 60
            with patch("app.api.v1.auth.validate_telegram_init_data", return_value=valid_data):
                r = client.post(
                    "/v1/auth/telegram",
                    json={"init_data": "user=%7B%22id%22%3A1001%7D&auth_date=9999999999"},
                )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "1001"
        assert data["username"] == "alice"
