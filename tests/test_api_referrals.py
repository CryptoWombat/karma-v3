"""Referral API tests."""
import pytest


class TestCreateReferral:
    """POST /v1/referrals"""

    def test_referral_success(self, client, user_alice_with_balance, user_bob):
        """Recording referral gives 1 Karma to inviter."""
        bal_before = client.get("/v1/users/balance/1001").json()["balance"]
        r = client.post(
            "/v1/referrals",
            json={"inviter_id": "1001", "new_user_id": "1002"},
        )
        assert r.status_code == 200
        assert "recorded" in r.json()["message"].lower()

        bal_after = client.get("/v1/users/balance/1001").json()["balance"]
        assert bal_after == bal_before + 1.0

    def test_referral_already_referred(self, client, user_alice_with_balance, user_bob):
        """Re-recording same referral returns message, no extra Karma."""
        client.post("/v1/referrals", json={"inviter_id": "1001", "new_user_id": "1002"})
        bal1 = client.get("/v1/users/balance/1001").json()["balance"]
        r = client.post("/v1/referrals", json={"inviter_id": "1001", "new_user_id": "1002"})
        assert r.status_code == 200
        assert "already" in r.json()["message"].lower()
        bal2 = client.get("/v1/users/balance/1001").json()["balance"]
        assert bal2 == bal1  # No extra Karma

    def test_referral_user_not_found(self, client, user_alice):
        """Referral with non-existent user returns 404."""
        r = client.post(
            "/v1/referrals",
            json={"inviter_id": "1001", "new_user_id": "99999"},
        )
        assert r.status_code == 404


class TestReferralStatus:
    """GET /v1/referrals/status/{user_id}"""

    def test_status_not_referred(self, client, user_alice):
        """User with no referral returns invited_by=None."""
        r = client.get("/v1/referrals/status/1001")
        assert r.status_code == 200
        assert r.json()["invited_by"] is None
        assert r.json()["rewarded"] is False

    def test_status_referred(self, client, user_alice_with_balance, user_bob):
        """Referred user returns inviter and rewarded=False."""
        client.post("/v1/referrals", json={"inviter_id": "1001", "new_user_id": "1002"})
        r = client.get("/v1/referrals/status/1002")
        assert r.status_code == 200
        assert r.json()["invited_by"] == "1001"
        assert r.json()["rewarded"] is False

    def test_status_non_existent_user(self, client):
        """Non-existent user returns invited_by=None, rewarded=False."""
        r = client.get("/v1/referrals/status/99999")
        assert r.status_code == 200
        assert r.json()["invited_by"] is None
        assert r.json()["rewarded"] is False
