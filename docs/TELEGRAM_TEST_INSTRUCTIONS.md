# How to Test Karma in Telegram

Step-by-step guide to deploy the API and test the Mini App inside Telegram.

---

## Quick Path (local + ngrok, no deploy)

```powershell
# 1. Install ngrok: winget install ngrok  (or from ngrok.com)
# 2. Run:
.\scripts\run-with-ngrok.ps1
```
This starts the API + gives you a public URL. Set that URL + `/app/` in BotFather → Menu Button, then mint and test.

---

## Full Path (deploy to Railway)

---

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g. "Karma Test")
4. Choose a username (e.g. `karma_test_12345_bot`) – must end in `bot`
5. **Save the token** (e.g. `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

---

## Step 2: Deploy the API

### Option A: Railway (recommended)

1. Go to [railway.app](https://railway.app) and sign in
2. **New Project** → **Deploy from GitHub** → connect repo → select `Karma-v3`
3. Add **PostgreSQL** (one-click, from templates)
4. Click your **API service** → **Variables** → add:

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | Click "Add variable" → Reference → Postgres → `DATABASE_URL` (auto-linked) |
   | `ADMIN_API_KEY` | Generate: `openssl rand -hex 24` (or any strong secret) |
   | `JWT_SECRET` | Generate: `openssl rand -hex 32` |
   | `TELEGRAM_BOT_TOKEN` | Your bot token from Step 1 |
   | `JWT_REQUIRED` | `1` |

5. **Settings** → **Networking** → **Generate domain**
6. **Copy the public URL** (e.g. `https://karma-v3-production.up.railway.app`)

### Option B: Run locally (for quick test)

```bash
cd Karma-v3
cp .env.example .env
# Edit .env: set TELEGRAM_BOT_TOKEN, ADMIN_API_KEY, JWT_SECRET
# Use ngrok or similar to expose: ngrok http 8000
python -m uvicorn app.main:app --port 8000
```

Use the ngrok HTTPS URL as your API URL (e.g. `https://abc123.ngrok.io`).

---

## Step 3: Set the Mini App URL in BotFather

1. Open **@BotFather** in Telegram
2. Send `/mybots` → select your bot
3. **Bot Settings** → **Menu Button** → **Configure menu button**
4. Set **Menu button URL** to:
   ```
   https://YOUR-API-URL/app/
   ```
   Example (Railway):
   ```
   https://karma-v3-production.up.railway.app/app/
   ```
   Must be **HTTPS** and end with `/app/`

5. Or use **Set up Web App** / **Configure Web App** if your BotFather shows that option – set the same URL

---

## Step 4: Mint Karma (first-time setup)

Before testing, give your Telegram user some Karma:

**PowerShell script:**
```powershell
.\scripts\mint-to-user.ps1 -ApiUrl "https://YOUR-API-URL" -UserId "YOUR_TELEGRAM_ID"
```

**Or curl:**
```bash
curl -X POST https://YOUR-API-URL/v1/admin/mint \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_API_KEY" \
  -d '{"user_id": "YOUR_TELEGRAM_USER_ID", "amount": 100}'
```

**Get your Telegram user ID:**
- Send `/start` to **@userinfobot** – it will reply with your ID  
- Or use **@getidsbot**

---

## Step 5: Test in Telegram

1. Open your bot in Telegram (search for the username you created)
2. Tap **Menu** (or the button under the chat)
3. The Mini App opens – you should see:
   - Your balance (or 0 if you haven't minted)
   - Send form
   - Refresh button

4. **If you see "Loading..." then an error:**
   - `Telegram auth not configured` → Check `TELEGRAM_BOT_TOKEN` is set
   - `Invalid or expired initData` → Make sure you opened the app from the bot (not by pasting the URL in a browser)

5. **To test Send:**
   - Mint to your account first (Step 4)
   - Enter a recipient’s Telegram user ID (friend or second account)
   - Enter amount → **Send**
   - Other user opens the bot → should see updated balance after refreshing

---

## Step 6: Troubleshooting

| Issue | Fix |
|-------|-----|
| "Open in Telegram" message | Open the app via the bot Menu, not in a browser |
| "Invalid or expired initData" | You must open from Telegram; initData is only set when launched from Telegram |
| "User not found" on balance | Run register first – open the app; it auto-registers |
| CORS error | API allows all origins; if using a separate frontend, add your domain to CORS |
| 503 on auth | `TELEGRAM_BOT_TOKEN` not set |
| Balance shows 0 | Mint to your user_id via admin (Step 4) |

---

## Quick Reference

- **Mini App URL:** `https://YOUR-API-URL/app/`
- **API docs:** `https://YOUR-API-URL/docs`
- **Health:** `https://YOUR-API-URL/health`
