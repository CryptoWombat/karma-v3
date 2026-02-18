"""Public stats API tests."""
import pytest


class TestPublicStats:
    """GET /v1/stats - no auth required"""

    def test_stats_public_no_auth(self, client):
        """Public stats accessible without auth."""
        r = client.get("/v1/stats")
        assert r.status_code == 200

    def test_stats_structure(self, client, user_alice_with_balance):
        """Stats has required fields."""
        r = client.get("/v1/stats")
        data = r.json()
        assert data["network_status"] == "operational"
        assert "users" in data
        assert "transactions" in data
        assert "minted" in data
        assert "transferred" in data
        assert "total_in_circulation" in data
        assert "available" in data
        assert "savings" in data
        assert "rewards_earned" in data
        assert "last_block_id" in data
        assert "last_block_at" in data
        assert "foundation_balance" in data
