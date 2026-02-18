"""Wallet API tests: send."""
import pytest


class TestSend:
    """POST /v1/wallets/send"""

    def test_send_success(self, client, user_alice_with_balance, user_bob):
        """Send Karma from alice to bob."""
        r = client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "1002", "amount": 50},
        )
        assert r.status_code == 200
        assert "50" in r.json()["message"]

        r_a = client.get("/v1/users/balance/1001")
        r_b = client.get("/v1/users/balance/1002")
        assert r_a.json()["balance"] == 450.0
        assert r_b.json()["balance"] == 50.0

    def test_send_insufficient_balance(self, client, user_alice, user_bob):
        """Send with zero balance returns 400."""
        r = client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "1002", "amount": 10},
        )
        assert r.status_code == 400
        assert "insufficient" in r.json()["detail"].lower()

    def test_send_min_amount(self, client, user_alice_with_balance, user_bob):
        """Amount below 0.001 returns 422 (validation)."""
        r = client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "1002", "amount": 0.0001},
        )
        assert r.status_code == 422

    def test_send_user_not_found(self, client, user_alice_with_balance):
        """Send to non-existent user returns 404."""
        r = client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "99999", "amount": 10},
        )
        assert r.status_code == 404

    def test_send_with_note(self, client, user_alice_with_balance, user_bob):
        """Send with optional note succeeds."""
        r = client.post(
            "/v1/wallets/send",
            json={
                "sender_id": "1001",
                "recipient_id": "1002",
                "amount": 5,
                "note": "thanks!",
            },
        )
        assert r.status_code == 200
