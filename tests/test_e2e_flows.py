"""End-to-end flow tests - full user journeys."""
import pytest


class TestE2ERegisterAndBalance:
    """Full flow: register -> balance check."""

    def test_flow_register_then_balance(self, client):
        """New user registers, then checks balance."""
        r1 = client.post("/v1/users/register", json={"user_id": "2001", "username": "e2e_user"})
        assert r1.status_code == 200
        assert r1.json()["status"] == "created"

        r2 = client.get("/v1/users/balance/2001")
        assert r2.status_code == 200
        assert r2.json()["balance"] == 0.0
        assert r2.json()["user_id"] == "2001"


class TestE2EMintSendBalance:
    """Full flow: register 2 users -> mint -> send -> verify balances."""

    def test_flow_mint_send_verify(self, client, admin_headers):
        """Admin mints to alice, alice sends to bob, verify both balances."""
        client.post("/v1/users/register", json={"user_id": "3001", "username": "alice"})
        client.post("/v1/users/register", json={"user_id": "3002", "username": "bob"})

        r_mint = client.post(
            "/v1/admin/mint",
            headers=admin_headers,
            json={"user_id": "3001", "amount": 200},
        )
        assert r_mint.status_code == 200

        r_send = client.post(
            "/v1/wallets/send",
            json={"sender_id": "3001", "recipient_id": "3002", "amount": 75},
        )
        assert r_send.status_code == 200

        r_a = client.get("/v1/users/balance/3001")
        r_b = client.get("/v1/users/balance/3002")
        assert r_a.json()["balance"] == 125.0
        assert r_b.json()["balance"] == 75.0


class TestE2EStakeUnstake:
    """Full flow: register -> mint -> stake -> unstake -> verify."""

    def test_flow_stake_unstake(self, client, user_alice_with_balance, admin_headers):
        """Stake then partial unstake."""
        r1 = client.post("/v1/stake", json={"user_id": "1001", "amount": 200})
        assert r1.status_code == 200

        r2 = client.post("/v1/unstake", json={"user_id": "1001", "amount": 50})
        assert r2.status_code == 200
        assert r2.json()["remaining_staked"] == 150.0

        bal = client.get("/v1/users/balance/1001").json()
        assert bal["balance"] == 350.0  # 500 - 200 + 50
        assert bal["staked"] == 150.0


class TestE2EStatsConsistency:
    """Stats match actual data after operations."""

    def test_stats_reflect_transactions(self, client, user_alice_with_balance, user_bob, admin_headers):
        """Stats match balance and tx counts."""
        client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "1002", "amount": 100},
        )

        r_stats = client.get("/v1/stats")
        assert r_stats.status_code == 200
        data = r_stats.json()
        assert data["minted"] == 500.0
        assert data["transferred"] == 100.0
        assert data["users"] >= 2
        assert data["transactions"] == 1


class TestE2EReferralBonus:
    """Referral bonus: when inviter sends to invitee, inviter gets 3 Karma."""

    def test_referral_bonus_on_first_send_to_invitee(self, client, user_alice_with_balance, user_bob):
        """Alice invites Bob. Alice sends to Bob → Alice gets 3 Karma bonus."""
        # Record referral: alice invited bob
        r_ref = client.post(
            "/v1/referrals",
            json={"inviter_id": "1001", "new_user_id": "1002"},
        )
        assert r_ref.status_code == 200

        # Alice has 501 (500 minted + 1 referral invite bonus), Bob has 0
        bal_alice_before = client.get("/v1/users/balance/1001").json()["balance"]
        bal_bob_before = client.get("/v1/users/balance/1002").json()["balance"]

        # Alice (inviter) sends 10 Karma to Bob (invitee) → Alice gets 3 bonus
        r_send = client.post(
            "/v1/wallets/send",
            json={"sender_id": "1001", "recipient_id": "1002", "amount": 10},
        )
        assert r_send.status_code == 200

        # Alice: before - 10 (sent) + 3 (referral bonus)
        bal_alice_after = client.get("/v1/users/balance/1001").json()["balance"]
        assert bal_alice_after == bal_alice_before - 10 + 3

        # Bob: receives 10
        bal_bob_after = client.get("/v1/users/balance/1002").json()["balance"]
        assert bal_bob_after == bal_bob_before + 10

        # Status shows rewarded=True
        r_status = client.get("/v1/referrals/status/1002")
        assert r_status.json()["rewarded"] is True
