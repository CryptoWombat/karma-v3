# Karma Platform v3 — Testing Guide

This document describes the testing strategy, tools, and how to run tests for the Karma Platform.

---

## Overview

| Layer | Tool | Location | Purpose |
|-------|------|----------|---------|
| **API** | pytest + httpx (TestClient) | `tests/test_api_*.py` | Unit/integration tests for all endpoints |
| **E2E** | pytest | `tests/test_e2e_flows.py` | Full user journey tests |
| **Regression** | pytest | `tests/test_regression.py` | Smoke tests after any change |
| **Visual/UI** | Playwright + HTML harness | `tests/ui/` | Visual verification of API via browser |

---

## Quick Start

```bash
# Run all API and E2E tests (no server needed)
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run only regression suite
pytest tests/test_regression.py -v

# Run visual tests (requires Playwright + running server)
playwright install chromium
pytest tests/ui/ -v
```

---

## Test Structure

```
tests/
├── conftest.py           # Fixtures: client, db_session, admin_headers
├── test_api_health.py    # Health, root
├── test_api_users.py    # Register, balance
├── test_api_wallets.py   # Send
├── test_api_admin.py     # Mint, admin stats
├── test_api_stats.py     # Public stats
├── test_e2e_flows.py     # Full flows (register→mint→send)
├── test_regression.py    # Smoke/regression
└── ui/
    ├── test_harness.html # Manual/Playwright test UI
    └── test_visual.py    # Playwright visual tests
```

---

## API Test Coverage

Every API endpoint has corresponding tests:

| Endpoint | Tests |
|----------|-------|
| `GET /health` | Returns ok, version |
| `GET /` | Returns message, docs link |
| `POST /v1/users/register` | New user (created), existing (exists), invalid user_id, missing fields |
| `GET /v1/users/balance/{id}` | Structure, after mint, not found, non-numeric |
| `POST /v1/wallets/send` | Success, insufficient balance, min amount, not found, with note |
| `POST /v1/admin/mint` | Auth required, success, not found, min amount |
| `GET /v1/admin/stats` | Auth required, correct aggregates |
| `POST /v1/stake` | Success, insufficient, not found, min amount |
| `POST /v1/unstake` | Success, insufficient staked, not found |
| `GET /v1/stake/info/{id}` | Structure, after stake, not found |
| `POST /v1/referrals` | Success, already referred, not found |
| `GET /v1/referrals/status/{id}` | Not referred, referred |
| `GET /v1/stats` | No auth, correct structure |

---

## Visual Verification

### Test Harness

`tests/ui/test_harness.html` is a standalone HTML page that:

1. Calls the Karma API (configurable base URL)
2. Runs a full flow: register → mint → send → balance
3. Displays results with green/red styling

**Manual usage:**
1. Start API: `python -m uvicorn app.main:app --port 8000`
2. Open `tests/ui/test_harness.html` in a browser
3. Set Admin API Key if needed
4. Click "Run Full Flow" — success shows green border

### Playwright Tests

Automated browser tests:

```bash
pip install playwright
playwright install chromium
pytest tests/ui/test_visual.py -v
```

These tests spawn the API server, load the harness, and verify:
- Page loads
- Health Check button shows OK
- Full Flow completes with correct balances (green result)

### UI Component Testing (Validator Dashboard, etc.)

For dashboard/UI components with interactive controls (dropdowns, buttons, reloads):

1. **Initial load** — Data loads and displays correctly.
2. **Control persistence** — Interactive controls (select, button) must still exist after:
   - Changing a dropdown and waiting for reload
   - Clicking "Load" / "Refresh" multiple times
   - Any async data fetch that replaces DOM content
3. **Structural integrity** — Cards/sections that use `.card-content` or similar wrappers must preserve them after content replacement, so subsequent loads target the correct element.
4. **Multiple interactions** — Test that changing a control repeatedly (e.g. limit 10→25→50) doesn't break the UI.
5. **Assert controls exist** — Don't just assert "data loaded"; assert that interactive elements are still present and functional after reload.

---

## Regression Testing

**When to run:** After every change that touches:
- API routes
- Services
- Models
- Database schema

```bash
pytest tests/test_regression.py -v
```

The regression suite is small and fast; it covers:
- Health
- Register + balance roundtrip
- Mint + send + balance roundtrip
- Stats availability

---

## Adding Tests for New Features

### Checklist for New Features

1. **API tests** — Add to `test_api_*.py` or create `test_api_<feature>.py`
   - Happy path
   - Error cases (404, 400, 403)
   - Validation (422 for invalid input)

2. **E2E test** — Add flow to `test_e2e_flows.py` if it's a user journey

3. **Regression** — Add a smoke test to `test_regression.py` if it's core

4. **Visual** — If the feature affects the harness flow, update `test_harness.html` and `test_visual.py`

5. **Docs** — Update `TEST_SCENARIOS.md` with the new scenarios

### Example: Adding Stake

```python
# tests/test_api_stake.py
class TestStake:
    def test_stake_success(self, client, user_alice_with_balance):
        r = client.post("/v1/stake", json={"user_id": "1001", "amount": 50})
        assert r.status_code == 200
        # ...
```

### Regression Workflow

When adding a feature:

1. Write tests first (TDD) or alongside the feature
2. Run full suite: `pytest tests/ -v --ignore=tests/ui/`
3. Run regression: `pytest tests/test_regression.py -v`
4. Add a regression smoke for the new feature if it's core
5. Update TEST_SCENARIOS.md with new scenario IDs

---

## Environment for Tests

Tests use:
- `DATABASE_URL=sqlite:///./test_karma.db` (or `test_visual.db` for UI tests)
- `ADMIN_API_KEY=test-admin-key`
- `TESTING=1`

Set in `tests/conftest.py` before app import.
