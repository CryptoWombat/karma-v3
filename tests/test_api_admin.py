"""Admin API tests: mint, stats."""
import pytest


class TestAdminMint:
    """POST /v1/admin/mint"""

    def test_mint_requires_auth(self, client, user_alice):
        """Mint without admin key returns 403."""
        r = client.post(
            "/v1/admin/mint",
            json={"user_id": "1001", "amount": 100},
        )
        assert r.status_code == 403

    def test_mint_success(self, client, user_alice, admin_headers):
        """Mint adds Karma to user."""
        r = client.post(
            "/v1/admin/mint",
            headers=admin_headers,
            json={"user_id": "1001", "amount": 100},
        )
        assert r.status_code == 200
        assert "100" in r.json()["message"]

        r2 = client.get("/v1/users/balance/1001")
        assert r2.json()["balance"] == 100.0

    def test_mint_user_not_found(self, client, admin_headers):
        """Mint to non-existent user returns 404."""
        r = client.post(
            "/v1/admin/mint",
            headers=admin_headers,
            json={"user_id": "99999", "amount": 100},
        )
        assert r.status_code == 404

    def test_mint_min_amount(self, client, user_alice, admin_headers):
        """Amount below 0.001 returns 422 (Pydantic validation)."""
        r = client.post(
            "/v1/admin/mint",
            headers=admin_headers,
            json={"user_id": "1001", "amount": 0.0001},
        )
        assert r.status_code in (400, 422)


class TestAdminStats:
    """GET /v1/admin/stats"""

    def test_admin_stats_requires_auth(self, client):
        """Stats without admin key returns 403."""
        r = client.get("/v1/admin/stats")
        assert r.status_code == 403

    def test_admin_stats_returns_network_data(self, client, user_alice_with_balance, admin_headers):
        """Admin stats returns correct aggregates."""
        r = client.get("/v1/admin/stats", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total_users"] >= 1
        assert data["total_minted"] == 500.0
        assert "total_transferred" in data
        assert "total_karma_supply" in data
        assert "total_savings" in data


class TestAdminUsers:
    """GET /v1/admin/users"""

    def test_list_users_requires_auth(self, client):
        r = client.get("/v1/admin/users")
        assert r.status_code == 403

    def test_list_users_success(self, client, user_alice_with_balance, admin_headers):
        r = client.get("/v1/admin/users", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "users" in data
        assert data["total"] >= 1
        u = data["users"][0]
        assert "user_id" in u
        assert "username" in u
        assert "karma_balance" in u
        assert "chiliz_balance" in u
        assert "staked" in u


class TestAdminUnregister:
    """POST /v1/admin/unregister"""

    def test_unregister_requires_auth(self, client, user_alice):
        r = client.post("/v1/admin/unregister", json={"user_id": "1001"})
        assert r.status_code == 403

    def test_unregister_success(self, client, user_alice, admin_headers):
        r = client.post("/v1/admin/unregister", headers=admin_headers, json={"user_id": "1001"})
        assert r.status_code == 200
        assert "unregistered" in r.json()["message"].lower()
        # User should be gone
        r2 = client.get("/v1/users/balance/1001")
        assert r2.status_code == 404

    def test_unregister_user_not_found(self, client, admin_headers):
        r = client.post("/v1/admin/unregister", headers=admin_headers, json={"user_id": "99999"})
        assert r.status_code == 404


class TestAdminProtocolRunOnce:
    """POST /v1/admin/protocol/run-once"""

    def test_protocol_run_once_requires_auth(self, client):
        r = client.post("/v1/admin/protocol/run-once")
        assert r.status_code == 403

    def test_protocol_run_once_success(self, client, admin_headers):
        """Emission runs even with no activity (reward may be zero)."""
        r = client.post("/v1/admin/protocol/run-once", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "block_id" in data
        assert "reward_total" in data
        assert "message" in data

    def test_protocol_run_once_with_send_activity(self, client, user_alice_with_balance, user_bob, admin_headers):
        """Emission with SEND activity produces non-zero eligible distribution."""
        # Send from Alice to Bob to create usage
        r = client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "1002", "amount": 10},
        )
        assert r.status_code == 200
        r = client.post("/v1/admin/protocol/run-once", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["block_id"] >= 1
        assert data["processed_tx_count"] >= 1
