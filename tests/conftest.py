"""Pytest fixtures and test configuration."""
import os
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

# Set test environment BEFORE importing app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test_karma.db"
os.environ["ADMIN_API_KEY"] = "test-admin-key"
os.environ["VALIDATOR_API_KEYS"] = "validator-key-1,validator-key-2"
os.environ["JWT_REQUIRED"] = "0"  # Disable JWT for tests (backward compat)
os.environ["ENVIRONMENT"] = "testing"
os.environ["RATE_LIMIT_DISABLED"] = "1"  # Skip rate limiting in tests
os.environ["PROTOCOL_SCHEDULED_ENABLED"] = "0"  # Disable emission scheduler in tests

# Clear settings cache so test env is picked up
from app.config import get_settings

get_settings.cache_clear()

from app.main import app
from app.db.session import init_db, drop_db, get_db, SessionLocal, engine


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio for pytest-asyncio."""
    return "asyncio"


@pytest.fixture(scope="function")
def db_session():
    """Fresh DB session for each test. Creates/drops tables."""
    drop_db()
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    """Remove test DB file after all tests."""
    yield
    import os as _os
    if _os.path.exists("test_karma.db"):
        try:
            _os.remove("test_karma.db")
        except OSError:
            pass


@pytest.fixture
def client(db_session):
    """TestClient that overrides get_db to use test DB session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close - we manage it in fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def api_base():
    """Base URL for API (no trailing slash)."""
    return ""


@pytest.fixture
def admin_headers():
    """Headers for admin-authenticated requests."""
    return {"Authorization": "Bearer test-admin-key"}


# --- Test data factories ---
@pytest.fixture
def user_alice(client):
    """Registered user alice (telegram_id=1001)."""
    r = client.post("/v1/users/register", json={"user_id": "1001", "username": "alice"})
    assert r.status_code == 200
    return {"user_id": "1001", "username": "alice"}


@pytest.fixture
def user_bob(client):
    """Registered user bob (telegram_id=1002)."""
    r = client.post("/v1/users/register", json={"user_id": "1002", "username": "bob"})
    assert r.status_code == 200
    return {"user_id": "1002", "username": "bob"}


@pytest.fixture
def user_alice_with_balance(client, user_alice, admin_headers):
    """Alice with 500 Karma minted."""
    r = client.post(
        "/v1/admin/mint",
        headers=admin_headers,
        json={"user_id": "1001", "amount": 500},
    )
    assert r.status_code == 200
    return user_alice
