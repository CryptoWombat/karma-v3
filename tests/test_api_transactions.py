"""Transaction history API tests."""
import pytest


class TestTransactionHistory:
    """GET /v1/transactions"""

    def test_transactions_empty(self, client, user_alice):
        """New user has no transactions."""
        r = client.get("/v1/transactions?user_id=1001")
        assert r.status_code == 200
        data = r.json()
        assert data["transactions"] == []
        assert data["total"] == 0
        assert data["limit"] >= 1
        assert data["offset"] == 0

    def test_transactions_after_mint(self, client, user_alice_with_balance, admin_headers):
        """Mint creates a transaction."""
        r = client.get("/v1/transactions?user_id=1001")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        tx = data["transactions"][0]
        assert tx["type"] == "mint"
        assert tx["amount_karma"] == 500.0
        assert tx["to_user_id"] == "1001"

    def test_transactions_after_send(self, client, user_alice_with_balance, user_bob, admin_headers):
        """Send creates transactions for both parties."""
        client.post("/v1/wallets/send", json={"sender_id": "1001", "recipient_id": "1002", "amount": 50})
        r1 = client.get("/v1/transactions?user_id=1001")
        r2 = client.get("/v1/transactions?user_id=1002")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Alice: mint + send
        assert r1.json()["total"] >= 2
        # Bob: receive (if we record it) or just send from alice's perspective. We only have SEND type.
        # Actually we only record SEND, not RECEIVE. So Bob wouldn't have a transaction unless we add RECEIVE.
        # Looking at wallet_service - we only add SEND. The recipient isn't in from/to as a separate row.
        # So Bob has no transaction. Let me check - for SEND: from_user_id=sender, to_user_id=recipient.
        # So both sender and recipient are in the transaction. Our filter is actor OR from OR to.
        # SEND: actor=sender, from=sender, to=recipient. So both match. Good.
        assert r2.json()["total"] >= 1

    def test_transactions_pagination(self, client, user_alice_with_balance, admin_headers):
        """Pagination works."""
        r = client.get("/v1/transactions?user_id=1001&limit=10&offset=0")
        assert r.status_code == 200
        assert r.json()["limit"] == 10
        assert r.json()["offset"] == 0

    def test_transactions_invalid_user_id(self, client):
        """Non-numeric user_id returns 422."""
        r = client.get("/v1/transactions?user_id=abc")
        assert r.status_code == 422
