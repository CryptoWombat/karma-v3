"""Quick visual check of Top Holders - saves screenshot and dumps structure."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

url = "http://127.0.0.1:8765/app/validator.html"
out_dir = Path(__file__).resolve().parent.parent

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.fill("#baseUrl", "http://127.0.0.1:8765")
    page.fill("#apiKey", "validator-key-1")
    time.sleep(6)
    leaderboard = page.locator("#leaderboard")
    leaderboard.scroll_into_view_if_needed()
    time.sleep(0.5)
    page.screenshot(path=out_dir / "top_holders_screenshot.png")
    leaderboard.screenshot(path=out_dir / "top_holders_card_only.png")
    content_html = page.locator("#leaderboard .card-content").evaluate("el => el.innerHTML")
    with open(out_dir / "leaderboard_content_dump.txt", "w") as f:
        f.write(content_html)
    browser.close()

print("Screenshots and dump saved")
