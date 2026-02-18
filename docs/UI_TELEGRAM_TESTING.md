# UI & Telegram Testing Guide

Run manual and automated tests against the Karma API, then connect with Telegram.

---

## 1. Quick Start – UI Test Harness

### Start the API

```bash
cd Karma-v3
pip install -r requirements.txt
cp .env.example .env   # Edit: set ADMIN_API_KEY=test-admin-key
python -m uvicorn app.main:app --reload --port 8000
```

### Open the harness in a browser

```bash
# Windows
start tests/ui/test_harness.html

# macOS
open tests/ui/test_harness.html

# Or open the file path directly in your browser
# e.g. file:///C:/Users/you/Karma-v3/tests/ui/test_harness.html
```

### Run the flow

1. **API Base URL**: `http://localhost:8000` (default)
2. **Admin API Key**: `test-admin-key` (must match `ADMIN_API_KEY` in `.env`)
3. Click **Health Check** – should show green
4. Click **Run Full Flow** – register → mint → send → balances (green = success)

---

## 2. Playwright automated UI tests

```bash
pip install playwright
playwright install chromium
pytest tests/ui/ -v
```

These tests start the server, open the harness in Chromium, and verify:
- Page loads
- Health Check returns OK
- Full Flow completes with correct balances

---

## 3. Telegram Mini App testing

The API supports JWT auth from Telegram WebApp `initData`. For local development you can bypass JWT.

### Option A: Bypass JWT (local / harness)

Set in `.env`:

```
JWT_REQUIRED=0
```

User endpoints (balance, send, stake, etc.) accept `user_id` in the body without a JWT. The test harness works this way.

### Option B: Real Telegram auth

1. **Create a Telegram Bot** (via [@BotFather](https://t.me/BotFather))
   - Get bot token → set `TELEGRAM_BOT_TOKEN` in `.env`

2. **Set JWT required**:
   ```
   JWT_REQUIRED=1
   TELEGRAM_BOT_TOKEN=your_bot_token
   JWT_SECRET=your_secret
   ```

3. **Auth flow**:
   - User opens your Mini App in Telegram
   - Telegram injects `window.Telegram.WebApp.initData`
   - Your frontend sends `POST /v1/auth/telegram` with `init_data`
   - API validates HMAC, returns JWT
   - Frontend stores JWT, sends `Authorization: Bearer <jwt>` on all requests

### Test auth manually

```bash
# With a valid initData from Telegram (replace with real value)
curl -X POST http://localhost:8000/v1/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{"init_data":"<paste from Telegram WebApp>"}'
```

---

## 4. Test script (start API + harness)

```bash
# PowerShell
.\scripts\start-for-ui-test.ps1

# Bash
./scripts/start-for-ui-test.sh
```

---

## 5. Environment for testing

| Variable          | Purpose                                  |
|-------------------|------------------------------------------|
| `ADMIN_API_KEY`   | Required for mint, admin endpoints       |
| `JWT_REQUIRED`    | `0` = bypass for harness; `1` = real auth |
| `TELEGRAM_BOT_TOKEN` | Required for Telegram auth (when JWT=1) |
| `VALIDATOR_API_KEYS` | Optional: for validator endpoints      |
| `RATE_LIMIT_DISABLED` | `1` = skip rate limit (tests)      |
