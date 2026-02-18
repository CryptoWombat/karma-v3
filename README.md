# Karma Platform v3

Rebuild of the Karma token economy backend — PostgreSQL/SQLite-backed API with FastAPI.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env and set ADMIN_API_KEY for admin endpoints
cp .env.example .env

# Run (SQLite for local dev)
python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

**Deployment:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)  
**Test in Telegram:** [docs/TELEGRAM_TEST_INSTRUCTIONS.md](docs/TELEGRAM_TEST_INSTRUCTIONS.md)

## Implemented

- **Users**: Register (idempotent), balance, self-unregister
- **Wallets**: Send Karma, swap (Karma ↔ Chiliz), referral bonus on first send from invitee
- **Stake**: POST /v1/stake, POST /v1/unstake, GET /v1/stake/info/{id}
- **Referrals**: POST /v1/referrals, GET /v1/referrals/status/{id}
- **Admin**: Mint, stats, unregister, event wallets, backup/restore, validator keys, protocol run-once
- **Stats**: Public /v1/stats (last_block_*, foundation_balance)
- **Validator API**: Snapshot, inflation, leaderboard, transactions, health
- **Protocol emission**: Block-based rewards (admin trigger)
- **Observability**: Structured JSON logging, request IDs, audit log

## Environment

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL or `sqlite:///./karma.db` |
| `ADMIN_API_KEY` | Required for /v1/admin/* |
| `JWT_SECRET` | For future Telegram JWT auth |

## Project Structure

```
app/
├── main.py           # FastAPI app
├── config.py         # Settings
├── api/v1/           # Route handlers
├── models/           # SQLAlchemy models
├── services/         # Business logic
├── schemas/          # Pydantic request/response
└── db/               # Session, init

docs/                 # PRD and planning
```

## Testing

```bash
# API + E2E + regression (default, no Playwright)
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Start API + open UI harness for manual testing
.\scripts\start-for-ui-test.ps1   # Windows
./scripts/start-for-ui-test.sh    # macOS/Linux

# Visual tests (requires: pip install playwright && playwright install chromium)
pytest tests/ui/ -v  # runs Playwright tests (starts server automatically)
```

See **docs/TESTING.md** and **docs/TEST_SCENARIOS.md** for full coverage.  
**UI & Telegram testing:** [docs/UI_TELEGRAM_TESTING.md](docs/UI_TELEGRAM_TESTING.md)

## To Do

- [ ] Auth: Telegram initData + JWT (flow exists; set `TELEGRAM_BOT_TOKEN` for production)
- [ ] Scheduled protocol emission (background job on interval)
- [ ] Redis-based rate limiting (optional, for production)
