"""Capture screenshot of validator dashboard at http://127.0.0.1:8001."""
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

API_URL = "http://127.0.0.1:8001"
project_root = Path(__file__).resolve().parents[1]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"{API_URL}/app/validator.html")
    page.wait_for_load_state("networkidle")
    # Key is now pre-filled; ensure base URL is set
    page.fill("#baseUrl", API_URL)
    page.click("button:has-text('Load All')")
    page.wait_for_timeout(4000)
    out_path = project_root / "validator-dashboard-8001.png"
    page.screenshot(path=str(out_path), full_page=True)
    browser.close()
print(f"Screenshot: {out_path}")
