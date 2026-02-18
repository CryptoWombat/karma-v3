"""Validator API tests."""
import pytest
from unittest.mock import patch


@pytest.fixture
def validator_headers():
    """Headers for validator-authenticated requests."""
    return {"Authorization": "Bearer validator-key-1"}


class TestValidatorHealth:
    """GET /v1/validator/health - no auth required."""

    def test_health_returns_ok(self, client):
        """Validator health returns operational status."""
        r = client.get("/v1/validator/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"
        assert data["database"] == "ok"
        assert "timestamp" in data


class TestValidatorSnapshot:
    """GET /v1/validator/snapshot - requires validator auth."""

    def test_snapshot_requires_auth(self, client, user_alice):
        """Snapshot without validator key returns 401/503."""
        r = client.get("/v1/validator/snapshot")
        assert r.status_code in (401, 503)

    def test_snapshot_success(self, client, user_alice_with_balance, validator_headers):
        """Snapshot returns full platform data."""
        r = client.get("/v1/validator/snapshot", headers=validator_headers)
        assert r.status_code == 200
        data = r.json()
        assert "snapshot_at" in data
        assert "users" in data
        assert data["users"]["user_count"] >= 1
        assert "balances" in data
        assert data["balances"]["total_karma_balance"] == 500.0
        assert "transactions" in data
        assert "inflation" in data
        assert "top_wallets" in data

    def test_snapshot_accepts_25(self, client, user_alice_with_balance, validator_headers):
        """Snapshot include_top=25 is valid (aligns with leaderboard limit options)."""
        r = client.get("/v1/validator/snapshot?include_top=25", headers=validator_headers)
        assert r.status_code == 200
        data = r.json()
        assert "top_wallets" in data


class TestValidatorInflation:
    """GET /v1/validator/inflation."""

    def test_inflation_requires_auth(self, client):
        r = client.get("/v1/validator/inflation")
        assert r.status_code in (401, 503)

    def test_inflation_success(self, client, user_alice_with_balance, validator_headers):
        r = client.get("/v1/validator/inflation", headers=validator_headers)
        assert r.status_code == 200
        data = r.json()
        assert "inflation" in data
        assert "24h" in data["inflation"]
        assert "karma_minted" in data["inflation"]["24h"]
        assert "breakdown" in data["inflation"]["24h"]


class TestValidatorLeaderboard:
    """GET /v1/validator/leaderboard."""

    def test_leaderboard_requires_auth(self, client):
        r = client.get("/v1/validator/leaderboard")
        assert r.status_code in (401, 503)

    def test_leaderboard_success(self, client, user_alice_with_balance, validator_headers):
        r = client.get("/v1/validator/leaderboard", headers=validator_headers)
        assert r.status_code == 200
        data = r.json()
        assert "top_wallets" in data
        assert len(data["top_wallets"]) >= 1
        w = data["top_wallets"][0]
        assert "rank" in w
        assert "user_id" in w
        assert "karma_balance" in w
        assert "staked" in w
        assert "total" in w

    def test_leaderboard_respects_limit(self, client, user_alice_with_balance, validator_headers):
        """Leaderboard limit param returns at most that many wallets."""
        for limit in ("10", "25", "50", "100"):
            r = client.get(
                f"/v1/validator/leaderboard?limit={limit}",
                headers=validator_headers,
            )
            assert r.status_code == 200
            data = r.json()
            assert len(data["top_wallets"]) <= int(limit)


class TestValidatorTransactions:
    """GET /v1/validator/transactions."""

    def test_transactions_requires_auth(self, client):
        r = client.get("/v1/validator/transactions")
        assert r.status_code in (401, 503)

    def test_transactions_success(self, client, user_alice_with_balance, user_bob, validator_headers):
        client.post("/v1/wallets/send", json={"sender_id": "1001", "recipient_id": "1002", "amount": 50})
        r = client.get("/v1/validator/transactions", headers=validator_headers)
        assert r.status_code == 200
        data = r.json()
        assert "transactions" in data
        assert data["transactions"]["24h"]["count"] >= 1
        assert data["transactions"]["24h"]["volume_karma"] >= 50.0


class TestValidator503WhenNotConfigured:
    """Validator endpoints return 503 when VALIDATOR_API_KEYS not set."""

    def test_snapshot_503_when_no_keys(self, client, db_session):
        """Snapshot returns 503 when no validator keys configured."""
        mock_settings = type("MockSettings", (), {"validator_keys_set": set()})()

        with patch("app.core.dependencies.get_settings", return_value=mock_settings):
            r = client.get("/v1/validator/snapshot", headers={"Authorization": "Bearer any-key"})
        assert r.status_code == 503
        assert "not configured" in r.json()["detail"].lower()
