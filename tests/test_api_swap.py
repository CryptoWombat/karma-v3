"""Swap API tests: Karma ↔ Chiliz 1:1."""
import pytest


class TestSwap:
    """POST /v1/wallets/swap"""

    def test_swap_karma_to_chiliz(self, client, user_alice_with_balance):
        """Swap Karma to Chiliz."""
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "karma_to_chiliz", "amount": 100},
        )
        assert r.status_code == 200
        assert "Chiliz" in r.json()["message"]

        bal = client.get("/v1/users/balance/1001").json()
        assert bal["balance"] == 400.0  # 500 - 100
        assert bal["chiliz"] == 100.0

    def test_swap_chiliz_to_karma(self, client, user_alice_with_balance):
        """Swap Chiliz to Karma."""
        client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "karma_to_chiliz", "amount": 50},
        )
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "chiliz_to_karma", "amount": 25},
        )
        assert r.status_code == 200
        assert "Karma" in r.json()["message"]

        bal = client.get("/v1/users/balance/1001").json()
        assert bal["balance"] == 475.0  # 500 - 50 + 25
        assert bal["chiliz"] == 25.0

    def test_swap_insufficient_karma(self, client, user_alice):
        """Swap more Karma than balance returns 400."""
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "karma_to_chiliz", "amount": 100},
        )
        assert r.status_code == 400
        assert "insufficient" in r.json()["detail"].lower()

    def test_swap_insufficient_chiliz(self, client, user_alice_with_balance):
        """Swap more Chiliz than balance returns 400."""
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "chiliz_to_karma", "amount": 1},
        )
        assert r.status_code == 400
        assert "insufficient" in r.json()["detail"].lower()

    def test_swap_user_not_found(self, client):
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "99999", "direction": "karma_to_chiliz", "amount": 10},
        )
        assert r.status_code == 404

    def test_swap_min_amount(self, client, user_alice_with_balance):
        """Amount below 0.001 returns 422."""
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "karma_to_chiliz", "amount": 0.0001},
        )
        assert r.status_code == 422

    def test_swap_invalid_direction(self, client, user_alice_with_balance):
        """Invalid direction returns 422."""
        r = client.post(
            "/v1/wallets/swap",
            json={"user_id": "1001", "direction": "invalid", "amount": 10},
        )
        assert r.status_code == 422
