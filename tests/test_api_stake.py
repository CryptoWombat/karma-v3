"""Stake API tests."""
import pytest


class TestStake:
    """POST /v1/stake"""

    def test_stake_success(self, client, user_alice_with_balance):
        """Stake moves karma from liquid to staked."""
        r = client.post("/v1/stake", json={"user_id": "1001", "amount": 100})
        assert r.status_code == 200
        assert "deposited" in r.json()["message"].lower()

        bal = client.get("/v1/users/balance/1001").json()
        assert bal["balance"] == 400.0
        assert bal["staked"] == 100.0

    def test_stake_insufficient_balance(self, client, user_alice):
        """Stake with zero balance returns 400."""
        r = client.post("/v1/stake", json={"user_id": "1001", "amount": 10})
        assert r.status_code == 400
        assert "insufficient" in r.json()["detail"].lower()

    def test_stake_user_not_found(self, client, user_alice_with_balance):
        """Stake for unknown user returns 404."""
        r = client.post("/v1/stake", json={"user_id": "99999", "amount": 10})
        assert r.status_code == 404

    def test_stake_min_amount(self, client, user_alice_with_balance):
        """Amount below 0.001 returns 422."""
        r = client.post("/v1/stake", json={"user_id": "1001", "amount": 0.0001})
        assert r.status_code == 422


class TestUnstake:
    """POST /v1/unstake"""

    def test_unstake_success(self, client, user_alice_with_balance):
        """Unstake moves karma from staked to liquid."""
        client.post("/v1/stake", json={"user_id": "1001", "amount": 100})
        r = client.post("/v1/unstake", json={"user_id": "1001", "amount": 40})
        assert r.status_code == 200
        data = r.json()
        assert data["unstaked_amount"] == 40.0
        assert data["remaining_staked"] == 60.0

        bal = client.get("/v1/users/balance/1001").json()
        assert bal["balance"] == 440.0  # 500 - 100 + 40
        assert bal["staked"] == 60.0

    def test_unstake_insufficient_staked(self, client, user_alice_with_balance):
        """Unstake more than staked returns 400."""
        client.post("/v1/stake", json={"user_id": "1001", "amount": 50})
        r = client.post("/v1/unstake", json={"user_id": "1001", "amount": 100})
        assert r.status_code == 400
        assert "not enough" in r.json()["detail"].lower()

    def test_unstake_user_not_found(self, client):
        """Unstake for unknown user returns 404."""
        r = client.post("/v1/unstake", json={"user_id": "99999", "amount": 10})
        assert r.status_code == 404


class TestStakeInfo:
    """GET /v1/stake/info/{user_id}"""

    def test_stake_info_structure(self, client, user_alice_with_balance):
        """Stake info returns required fields."""
        r = client.get("/v1/stake/info/1001")
        assert r.status_code == 200
        data = r.json()
        assert "total_staked" in data
        assert "available_to_unstake" in data
        assert "liquid_karma" in data
        assert data["liquid_karma"] == 500.0

    def test_stake_info_after_stake(self, client, user_alice_with_balance):
        """Stake info reflects staked amount."""
        client.post("/v1/stake", json={"user_id": "1001", "amount": 75})
        r = client.get("/v1/stake/info/1001")
        assert r.json()["total_staked"] == 75.0
        assert r.json()["available_to_unstake"] == 75.0
        assert r.json()["liquid_karma"] == 425.0

    def test_stake_info_user_not_found(self, client):
        """Unknown user returns 404."""
        r = client.get("/v1/stake/info/99999")
        assert r.status_code == 404
