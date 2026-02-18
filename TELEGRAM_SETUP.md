# Telegram Mini App – Local Setup

## Quick start (one command)

From `karma-v3` folder:

```powershell
.\scripts\run-telegram-test.ps1
```

This will:
1. Create/use venv and install deps
2. Start the API in a new window (port 8000)
3. Start Cloudflare tunnel
4. Show the public URL in the tunnel output

## Manual steps

1. **Set Menu Button in BotFather**
   - Message @BotFather → /mybots → your bot → Bot Settings → Menu Button
   - Use: `https://YOUR-TUNNEL-URL/app/` (must end with `/app/`)

2. **Open in Telegram**
   - Open your bot, tap the menu/link icon (or tap bot name → menu button)

## Prerequisites

- **Python 3.10+** with `python` on PATH
- **Cloudflare Tunnel** (`winget install Cloudflare.cloudflared`)
- **.env** with `TELEGRAM_BOT_TOKEN` (copy from `.env.example`)

## Current tunnel URL

**Quick tunnel** (default): The URL changes each time you run it. Check the cloudflared output for the latest one, e.g.:

```
https://something-random.trycloudflare.com/app/
```

**Persistent URL**: For a stable URL that does not change, set up a named Cloudflare tunnel. See **[docs/CLOUDFLARE_PERSISTENT_TUNNEL.md](docs/CLOUDFLARE_PERSISTENT_TUNNEL.md)** for step-by-step instructions.
