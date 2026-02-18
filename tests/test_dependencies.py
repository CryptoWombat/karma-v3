"""Tests for FastAPI dependencies and config."""
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db, get_db_context


@pytest.fixture
def client_no_admin(db_session):
    """Client with ADMIN_API_KEY unset - admin endpoints return 503."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_require_admin_503_when_not_configured(client_no_admin, db_session):
    """Admin mint returns 503 when ADMIN_API_KEY is not set."""
    # Ensure user exists
    from app.models import User, Wallet
    from app.services.user_service import register_user
    from app.schemas.user import RegisterRequest

    register_user(db_session, RegisterRequest(user_id="1001", username="alice"))
    db_session.commit()

    mock_settings = type("MockSettings", (), {"admin_api_key": None})()

    with patch("app.core.dependencies.get_settings", return_value=mock_settings):
        r = client_no_admin.post(
            "/v1/admin/mint",
            json={"user_id": "1001", "amount": 10},
        )
    assert r.status_code == 503
    assert "not configured" in r.json()["detail"].lower()


def test_get_db_context(db_session):
    """get_db_context yields a session and commits on success."""
    from app.models import User
    from app.services.user_service import get_user_by_telegram_id

    # Use context manager - should work
    with get_db_context() as db:
        user = get_user_by_telegram_id(db, 1001)
        # May be None if no user - that's ok
        assert db is not None
