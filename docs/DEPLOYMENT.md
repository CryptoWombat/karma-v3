# Karma Platform v3 – Deployment Guide

Deploy the API so you can test with the real Telegram Mini App.

---

## 1. Pre-deploy checklist

Before deploying, ensure everything works locally:

```bash
# Full test suite (95 tests)
pytest tests/ --ignore=tests/ui -v -q

# Manual harness (API running)
# 1. Start: python -m uvicorn app.main:app --port 8000
# 2. Open tests/ui/test_harness.html
# 3. Run Full Flow → green = success
```

**Required for production:**

| Item | Value |
|------|-------|
| `DATABASE_URL` | PostgreSQL URL (Railway, Supabase, Neon, etc.) |
| `ADMIN_API_KEY` | Strong secret for admin endpoints |
| `JWT_SECRET` | Strong secret for JWT signing |
| `TELEGRAM_BOT_TOKEN` | From @BotFather for your Mini App |
| `JWT_REQUIRED` | `1` (required for Telegram auth) |

---

## 2. Deployment options

### Option A: Railway

1. **Create project** at [railway.app](https://railway.app)
2. **Add PostgreSQL** (one-click)
3. **Add service** → Deploy from GitHub (this repo)
4. **Variables** – set in Railway dashboard:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}   # auto-linked if you named it Postgres
   ADMIN_API_KEY=<generate-strong-secret>
   JWT_SECRET=<generate-strong-secret>
   TELEGRAM_BOT_TOKEN=<from-BotFather>
   JWT_REQUIRED=1
   ```
5. **Build** – Railway detects Dockerfile
6. **Domain** – Railway provides `*.railway.app`; add custom domain if needed

### Option B: Render

1. **New Web Service** at [render.com](https://render.com)
2. **Connect repo** → select Karma-v3
3. **Build**:
   - Build Command: `docker build -t karma-api . && docker save karma-api`
   - Or use: `pip install -r requirements.txt`
   - Start Command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Add PostgreSQL** (Render Postgres)
5. **Environment variables** – set all required vars
6. **Domain** – `*.onrender.com` or custom

### Option C: Fly.io

```bash
# Install flyctl, then:
cd Karma-v3
fly launch
# Add Postgres: fly postgres create
fly secrets set DATABASE_URL=... ADMIN_API_KEY=... JWT_SECRET=... TELEGRAM_BOT_TOKEN=...
fly deploy
```

### Option D: Docker + VPS (DigitalOcean, Hetzner, etc.)

```bash
# Build
docker build -t karma-api .

# Run with env file
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e ADMIN_API_KEY=... \
  -e JWT_SECRET=... \
  -e TELEGRAM_BOT_TOKEN=... \
  -e JWT_REQUIRED=1 \
  karma-api
```

---

## 3. Telegram Mini App setup

### 3.1 Built-in Mini App

The API serves a Mini App at `/app/`. **URL:** `https://YOUR-API-DOMAIN/app/`

1. **@BotFather** – create bot, get token
2. **BotFather** → /newapp or set Menu Button URL to your Mini App
3. Your Mini App URL: `https://your-frontend.com` (or Telegram’s Web App host)

### 3.2 Configure in BotFather

1. **@BotFather** → your bot → **Bot Settings** → **Menu Button** → **Configure menu button**
2. Set **Menu button URL** to: `https://YOUR-API-DOMAIN/app/`

**Step-by-step:** [TELEGRAM_TEST_INSTRUCTIONS.md](TELEGRAM_TEST_INSTRUCTIONS.md)

### 3.3 Auth flow (Telegram → API)

1. User opens Mini App → Telegram injects `window.Telegram.WebApp.initData`
2. Frontend: `POST https://your-api/v1/auth/telegram` with `{"init_data": "..."}`
3. API validates HMAC with `TELEGRAM_BOT_TOKEN`, returns JWT
4. Frontend stores JWT, sends `Authorization: Bearer <jwt>` on all user endpoints

### 3.4 CORS

The API allows `*` origins. For production, restrict to your Mini App domain:

```
# In app/main.py or via env
CORS_ORIGINS=https://your-mini-app.vercel.app,https://t.me
```

---

## 4. Post-deploy verification

1. **Health**
   ```bash
   curl https://your-api.railway.app/health
   # → {"status":"ok","version":"3.0.0"}
   ```

2. **Auth (requires real initData from Telegram)**
   - Open your Mini App in Telegram
   - From browser dev tools or a test page, capture `initData`
   - `curl -X POST https://your-api/v1/auth/telegram -H "Content-Type: application/json" -d '{"init_data":"..."}'`
   - Should return `{"access_token":"...", "token_type":"bearer"}`

3. **User flow**
   - Register (or idempotent register from Telegram user data)
   - Get balance
   - Send Karma (with JWT in header)

---

## 5. Environment variables reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string |
| `ADMIN_API_KEY` | Yes | Admin endpoints |
| `JWT_SECRET` | Yes | JWT signing |
| `JWT_REQUIRED` | No (default 1) | 0 = bypass auth (dev only) |
| `TELEGRAM_BOT_TOKEN` | Yes (prod) | For initData validation |
| `VALIDATOR_API_KEYS` | No | Comma-separated validator keys |
| `LOG_LEVEL` | No | INFO, DEBUG, etc. |
| `ENVIRONMENT` | No | development, production |

---

## 6. Migration from SQLite to PostgreSQL

If you developed with SQLite, migrations are already defined. On first deploy with Postgres:

```bash
# Run automatically via Docker CMD, or manually:
alembic upgrade head
```

Existing SQLite data can be exported via `GET /v1/admin/backup` and transformed for Postgres if needed.
