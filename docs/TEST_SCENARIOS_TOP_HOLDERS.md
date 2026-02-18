# Top Holders Component — Functionality Test Scenarios

Exhaustive test scenarios for the validator dashboard Top Holders component. Each scenario is designed to be independently executable and to detect regressions.

---

## Component Behavior Summary

- **UI**: Card with header (h3), limit selector (10/25/50/100), and content table
- **Data source**: `GET /v1/validator/leaderboard?limit=N&sort_by=total`
- **Limit persistence**: Stored in `localStorage` key `karma-validator-top-holders-limit`
- **Card order**: Stored in `localStorage` key `karma-validator-dashboard-order`
- **Load triggers**: Page init (auto-load), Load All, Top Holders button, limit selector change

---

## Scenario Categories

### A. Initial Load & Structure

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-A1 | Default limit on first visit | Open dashboard, wait for auto-load | API called with `limit=10` | Request URL contains `limit=10` |
| TH-A2 | Limit selector present | Open dashboard | Selector exists with 4 options | `#topHoldersLimit` visible, options 10,25,50,100 |
| TH-A3 | Card structure | After any load | Card has header + selector + content | `.card-header-row`, `#topHoldersLimit`, `.card-content` exist |
| TH-A4 | Card-content preserved | After load | Exactly one `.card-content` | `#leaderboard .card-content` count === 1 |

### B. Limit Selector Behavior

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-B1 | Change to 25 | Select 25, wait for reload | API called with `limit=25`, table shows data | Request has `limit=25`, no errors |
| TH-B2 | Change to 50 | Select 50, wait | API called with `limit=50` | Request has `limit=50` |
| TH-B3 | Change to 100 | Select 100, wait | API called with `limit=100` | Request has `limit=100` |
| TH-B4 | Selector persists after content update | Select 50, wait for reload | Selector still visible, value 50 | `#topHoldersLimit` count=1, value=50 |
| TH-B5 | Multiple rapid changes | Select 10→25→50→100 quickly | No crash, final request uses 100 | Final request has `limit=100`, selector intact |

### C. Limit Persistence (localStorage)

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-C1 | Limit saved after change | Select 50, wait for load | localStorage has `karma-validator-top-holders-limit=50` | `localStorage.getItem(...)` === `"50"` |
| TH-C2 | Limit restored on reload | Set limit 50, reload page, wait for auto-load | Select shows 50, first API call uses limit=50 | Select value=50, first leaderboard request has `limit=50` |
| TH-C3 | Invalid saved limit ignored | Set localStorage to "99", reload | Falls back to 10 | Request has `limit=10` or select shows 10 |

### D. Load Triggers

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-D1 | Load All uses current limit | Set limit 50, click Load All | Leaderboard request has `limit=50` | Request has `limit=50` |
| TH-D2 | Top Holders button uses current limit | Set limit 25, click Top Holders | Leaderboard request has `limit=25` | Request has `limit=25` |
| TH-D3 | Load All twice preserves controls | Load All, wait, Load All again | Selector still present | `#topHoldersLimit` count=1 |
| TH-D4 | Top Holders button twice preserves controls | Click Top Holders twice | Selector still present | `#topHoldersLimit` count=1 |

### E. Restored Order Interaction

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-E1 | Restored limit used after restoreOrder | Save custom order + limit 50, reload | First request uses limit=50 | First leaderboard request has `limit=50` |
| TH-E2 | Limit selector works after card reorder | Drag leaderboard card, change limit | Request uses new limit | Request has correct limit |

### F. Error & Edge States

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-F1 | API error preserves selector | Use invalid API key, trigger load | Error message shown, selector still exists | `#topHoldersLimit` count=1 |
| TH-F2 | Empty leaderboard | Fresh DB with no wallets | "No wallets yet" or table with 0 rows | No crash, content present |
| TH-F3 | No saved limit (first visit) | Clear localStorage, open dashboard | Default 10, request has limit=10 | Request has `limit=10` |

### G. Data Integrity

| ID | Scenario | Steps | Expected | Pass Criteria |
|----|----------|-------|----------|---------------|
| TH-G1 | Row count ≤ limit | Request limit=25 | Table has ≤25 data rows | `#leaderboard tbody tr` count ≤ 25 |
| TH-G2 | Table structure | After load with data | Header row + data rows, columns #/User/Balance/Staked/Total | Table structure valid |

---

## Execution

```bash
# Run all Top Holders scenarios
pytest tests/ui/test_top_holders.py -v

# Run with API request logging
pytest tests/ui/test_top_holders.py -v -s
```

---

## Bug Detection Focus

These scenarios target historically missed bugs:

1. **Selector destroyed on content replace** (TH-B4, TH-D3, TH-D4)
2. **card-content structure lost** (TH-A4)
3. **Restored limit not used on first load** (TH-C2, TH-E1)
4. **Wrong limit sent to API** (TH-A1, TH-B1–B3, TH-D1–D2)
