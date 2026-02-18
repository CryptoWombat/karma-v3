"""Capture screenshot of validator dashboard with all data loaded."""
import os
import subprocess
import sys
import time
from pathlib import Path

# Start server with validator keys
project_root = Path(__file__).resolve().parents[1]
env = {
    **os.environ,
    "VALIDATOR_API_KEYS": "validator-key-1,validator-key-2",
    "DATABASE_URL": "sqlite:///./karma.db",
    "ADMIN_API_KEY": "test-admin-key",
}
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8766"],
    cwd=project_root,
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Wait for server
for _ in range(20):
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8766/health", timeout=2) as r:
            if r.status == 200:
                break
    except Exception:
        time.sleep(0.5)
else:
    proc.kill()
    sys.exit(1)

# Load page, fill key, click Load All, screenshot
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://127.0.0.1:8766/app/validator.html")
    page.fill("#baseUrl", "http://127.0.0.1:8766")
    page.fill("#apiKey", "validator-key-1")
    page.click("button:has-text('Load All')")
    page.wait_for_timeout(4000)
    out_path = project_root / "validator-dashboard-screenshot.png"
    page.screenshot(path=str(out_path), full_page=True)
    browser.close()

proc.terminate()
proc.wait(timeout=5)
print(f"Screenshot saved: {out_path}")
