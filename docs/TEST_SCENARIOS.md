# Karma Platform v3 — Test Scenarios

Comprehensive list of test scenarios for the platform. Each feature maps to one or more scenarios.

---

## 1. Health & Root

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| H-1 | GET /health | 200, `{status: "ok", version}` | test_api_health.py |
| H-2 | GET / | 200, message + docs link | test_api_health.py |

---

## 2. User Registration

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| UR-1 | Register new user | 200, status=created | test_api_users.py::TestRegister::test_register_new_user_returns_created |
| UR-2 | Register existing user | 200, status=exists | test_api_users.py::TestRegister::test_register_existing_user_returns_exists |
| UR-3 | Re-register with new username | 200, user updated | test_api_users.py::TestRegister::test_register_idempotent_updates_username |
| UR-4 | user_id non-numeric | 400 | test_api_users.py::TestRegister::test_register_rejects_non_numeric_user_id |
| UR-5 | Missing user_id | 422 | test_api_users.py::TestRegister::test_register_requires_user_id |
| UR-6 | Missing username | 422 | test_api_users.py::TestRegister::test_register_requires_username |

---

## 3. Balance

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| B-1 | Get balance of registered user | 200, balance/staked/rewards/chiliz | test_api_users.py::TestBalance::test_balance_returns_correct_structure |
| B-2 | Balance after mint | balance reflects minted amount | test_api_users.py::TestBalance::test_balance_after_mint |
| B-3 | User not found | 404 | test_api_users.py::TestBalance::test_balance_user_not_found |
| B-4 | user_id non-numeric | 400 | test_api_users.py::TestBalance::test_balance_rejects_non_numeric_user_id |

---

## 4. Send (Transfer)

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| S-1 | Send Karma | 200, balances updated | test_api_wallets.py::TestSend::test_send_success |
| S-2 | Insufficient balance | 400 | test_api_wallets.py::TestSend::test_send_insufficient_balance |
| S-3 | Amount < 0.001 | 422 | test_api_wallets.py::TestSend::test_send_min_amount |
| S-4 | Recipient not found | 404 | test_api_wallets.py::TestSend::test_send_user_not_found |
| S-5 | Send with note | 200 | test_api_wallets.py::TestSend::test_send_with_note |

---

## 5. Admin Mint

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| M-1 | Mint without auth | 403 | test_api_admin.py::TestAdminMint::test_mint_requires_auth |
| M-2 | Mint with auth | 200, balance increased | test_api_admin.py::TestAdminMint::test_mint_success |
| M-3 | Mint to non-existent user | 404 | test_api_admin.py::TestAdminMint::test_mint_user_not_found |
| M-4 | Amount < 0.001 | 422 | test_api_admin.py::TestAdminMint::test_mint_min_amount |

---

## 6. Admin Stats

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| AS-1 | Stats without auth | 403 | test_api_admin.py::TestAdminStats::test_admin_stats_requires_auth |
| AS-2 | Stats with auth | 200, total_users, total_minted, etc. | test_api_admin.py::TestAdminStats::test_admin_stats_returns_network_data |

---

## 7. Stake

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| ST-1 | Stake success | 200, balance→staked | test_api_stake.py::TestStake::test_stake_success |
| ST-2 | Stake insufficient balance | 400 | test_api_stake.py::TestStake::test_stake_insufficient_balance |
| ST-3 | Stake user not found | 404 | test_api_stake.py::TestStake::test_stake_user_not_found |
| ST-4 | Stake min amount | 422 | test_api_stake.py::TestStake::test_stake_min_amount |
| UN-1 | Unstake success | 200, staked→balance | test_api_stake.py::TestUnstake::test_unstake_success |
| UN-2 | Unstake insufficient staked | 400 | test_api_stake.py::TestUnstake::test_unstake_insufficient_staked |
| UN-3 | Unstake user not found | 404 | test_api_stake.py::TestUnstake::test_unstake_user_not_found |
| SI-1 | Stake info structure | total_staked, available, liquid | test_api_stake.py::TestStakeInfo |
| SI-2 | Stake info user not found | 404 | test_api_stake.py::TestStakeInfo::test_stake_info_user_not_found |

## 8. Referrals

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| RF-1 | Create referral | 200, +1 Karma to inviter | test_api_referrals.py::TestCreateReferral::test_referral_success |
| RF-2 | Referral already exists | 200, no extra Karma | test_api_referrals.py::TestCreateReferral::test_referral_already_referred |
| RF-3 | Referral user not found | 404 | test_api_referrals.py::TestCreateReferral::test_referral_user_not_found |
| RS-1 | Status not referred | invited_by=None | test_api_referrals.py::TestReferralStatus::test_status_not_referred |
| RS-2 | Status referred | invited_by, rewarded | test_api_referrals.py::TestReferralStatus::test_status_referred |

## 9. Public Stats

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| PS-1 | Stats without auth | 200 | test_api_stats.py::TestPublicStats::test_stats_public_no_auth |
| PS-2 | Stats structure | network_status, users, minted, transferred, etc. | test_api_stats.py::TestPublicStats::test_stats_structure |

---

## 10. E2E Flows

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| E2E-1 | Register → Balance | Register, then balance=0 | test_e2e_flows.py::TestE2ERegisterAndBalance |
| E2E-2 | Mint → Send → Balances | Balances correct | test_e2e_flows.py::TestE2EMintSendBalance |
| E2E-3 | Stake → Unstake | Partial unstake, balances correct | test_e2e_flows.py::TestE2EStakeUnstake |
| E2E-4 | Stats consistency | Stats reflect transactions | test_e2e_flows.py::TestE2EStatsConsistency |

---

## 11. Regression (Smoke)

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| R-1 | Health | 200 | test_regression.py::TestRegressionCore::test_health |
| R-2 | Register + balance roundtrip | Works | test_regression.py::TestRegressionCore::test_register_balance_roundtrip |
| R-3 | Mint + send roundtrip | Balances correct | test_regression.py::TestRegressionCore::test_mint_send_roundtrip |
| R-4 | Stats | Valid structure | test_regression.py::TestRegressionCore::test_stats_available |
| R-5 | Stake + unstake roundtrip | total_staked, liquid correct | test_regression.py::TestRegressionCore::test_stake_unstake_roundtrip |

---

## 12. Visual Verification

| ID | Scenario | Expected | Test |
|----|----------|----------|------|
| V-1 | Harness loads | Title contains Karma | test_ui/test_visual.py::TestVisualHarness::test_harness_loads |
| V-2 | Health button | Green result, ok/200 | test_ui/test_visual.py::TestVisualHarness::test_health_button_flow |
| V-3 | Full flow | Green result, alice=150, bob=50 | test_ui/test_visual.py::TestVisualHarness::test_full_flow_visual |

## 13. Top Holders (Validator Dashboard)

See **docs/TEST_SCENARIOS_TOP_HOLDERS.md** for full scenario matrix. All scenarios: `pytest tests/ui/test_top_holders.py -v`

---

## Running by Scenario Category

```bash
# API only
pytest tests/test_api_*.py -v

# E2E
pytest tests/test_e2e_flows.py -v

# Regression only
pytest tests/test_regression.py -v

# Visual (requires Playwright + server)
pytest tests/ui/test_visual.py -v

# Top Holders component (comprehensive, API interception)
pytest tests/ui/test_top_holders.py -v
```

---

## Coverage Goals

| Component | Target |
|-----------|--------|
| app/api/ | 90%+ |
| app/services/ | 85%+ |
| app/models/ | Via integration tests |
| app/core/ | 80%+ |

Run: `pytest tests/ --cov=app --cov-report=html`
