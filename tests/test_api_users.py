"""User API tests: register, balance."""
import pytest


class TestRegister:
    """POST /v1/users/register"""

    def test_register_new_user_returns_created(self, client):
        """New user registration returns status=created."""
        r = client.post("/v1/users/register", json={"user_id": "9001", "username": "newuser"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "created"
        assert "newuser" in data["message"]

    def test_register_existing_user_returns_exists(self, client, user_alice):
        """Re-registering same user returns status=exists."""
        r = client.post("/v1/users/register", json={"user_id": "1001", "username": "alice"})
        assert r.status_code == 200
        assert r.json()["status"] == "exists"

    def test_register_idempotent_updates_username(self, client, user_alice):
        """Re-register with new username updates the user."""
        r = client.post("/v1/users/register", json={"user_id": "1001", "username": "alice_updated"})
        assert r.status_code == 200
        # Balance should still work
        r2 = client.get("/v1/users/balance/1001")
        assert r2.status_code == 200

    def test_register_rejects_non_numeric_user_id(self, client):
        """user_id must be numeric (Pydantic validation)."""
        r = client.post("/v1/users/register", json={"user_id": "abc", "username": "test"})
        assert r.status_code == 422
        detail = r.json().get("detail", [])
        assert isinstance(detail, list)
        assert any("pattern" in str(d).lower() or "user_id" in str(d).lower() for d in detail)

    def test_register_requires_user_id(self, client):
        """Missing user_id returns 422."""
        r = client.post("/v1/users/register", json={"username": "test"})
        assert r.status_code == 422

    def test_register_requires_username(self, client):
        """Missing username returns 422."""
        r = client.post("/v1/users/register", json={"user_id": "123"})
        assert r.status_code == 422


class TestBalance:
    """GET /v1/users/balance/{user_id}"""

    def test_balance_returns_correct_structure(self, client, user_alice):
        """Balance response has required fields."""
        r = client.get("/v1/users/balance/1001")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == "1001"
        assert "balance" in data
        assert "staked" in data
        assert "rewards" in data
        assert "chiliz" in data
        assert data["balance"] == 0.0
        assert data["staked"] == 0.0

    def test_balance_after_mint(self, client, user_alice, admin_headers):
        """Balance reflects minted amount."""
        client.post("/v1/admin/mint", headers=admin_headers, json={"user_id": "1001", "amount": 100})
        r = client.get("/v1/users/balance/1001")
        assert r.status_code == 200
        assert r.json()["balance"] == 100.0

    def test_balance_user_not_found(self, client):
        """Unknown user returns 404."""
        r = client.get("/v1/users/balance/99999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_balance_rejects_non_numeric_user_id(self, client):
        """user_id path param must be numeric (Path validation)."""
        r = client.get("/v1/users/balance/abc")
        assert r.status_code == 422


class TestSelfUnregister:
    """POST /v1/users/unregister"""

    def test_self_unregister_success(self, client, user_alice):
        """User can unregister themselves (test mode with user_id in body)."""
        r = client.post("/v1/users/unregister", json={"user_id": "1001"})
        assert r.status_code == 200
        assert "unregistered" in r.json()["message"].lower()
        r2 = client.get("/v1/users/balance/1001")
        assert r2.status_code == 404

    def test_self_unregister_user_not_found(self, client):
        r = client.post("/v1/users/unregister", json={"user_id": "99999"})
        assert r.status_code == 404
