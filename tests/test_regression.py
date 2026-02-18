"""Regression test suite - run after any change to verify no breakage."""
import pytest


class TestRegressionCore:
    """Smoke tests for core functionality."""

    def test_health(self, client):
        """Health always responds."""
        assert client.get("/health").status_code == 200

    def test_register_balance_roundtrip(self, client):
        """Register -> balance works."""
        assert client.get("/v1/users/balance/abc").status_code == 422  # non-numeric path
        client.post("/v1/users/register", json={"user_id": "5001", "username": "reg"})
        assert client.get("/v1/users/balance/5001").status_code == 200

    def test_mint_send_roundtrip(self, client, admin_headers):
        """Mint -> send -> balance correct."""
        client.post("/v1/users/register", json={"user_id": "6001", "username": "a"})
        client.post("/v1/users/register", json={"user_id": "6002", "username": "b"})
        client.post("/v1/admin/mint", headers=admin_headers, json={"user_id": "6001", "amount": 10})
        client.post("/v1/wallets/send", json={"sender_id": "6001", "recipient_id": "6002", "amount": 4})
        a = client.get("/v1/users/balance/6001").json()
        b = client.get("/v1/users/balance/6002").json()
        assert a["balance"] == 6.0
        assert b["balance"] == 4.0

    def test_stats_available(self, client):
        """Public stats returns valid structure."""
        r = client.get("/v1/stats")
        assert r.status_code == 200
        d = r.json()
        assert "network_status" in d
        assert "users" in d
        assert isinstance(d["users"], int)

    def test_stake_unstake_roundtrip(self, client, user_alice_with_balance):
        """Stake -> unstake works."""
        client.post("/v1/stake", json={"user_id": "1001", "amount": 50})
        client.post("/v1/unstake", json={"user_id": "1001", "amount": 30})
        info = client.get("/v1/stake/info/1001").json()
        assert info["total_staked"] == 20.0
        assert info["liquid_karma"] == 480.0

    def test_swap_roundtrip(self, client, user_alice_with_balance):
        """Swap Karma -> Chiliz -> Karma preserves total value."""
        client.post("/v1/wallets/swap", json={"user_id": "1001", "direction": "karma_to_chiliz", "amount": 100})
        bal = client.get("/v1/users/balance/1001").json()
        assert bal["balance"] == 400.0
        assert bal["chiliz"] == 100.0

        client.post("/v1/wallets/swap", json={"user_id": "1001", "direction": "chiliz_to_karma", "amount": 100})
        bal2 = client.get("/v1/users/balance/1001").json()
        assert bal2["balance"] == 500.0
        assert bal2["chiliz"] == 0.0
