"""Full page visual check - capture entire dashboard to catch layout issues."""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

url = "http://127.0.0.1:8765/app/validator.html"
out_dir = Path(__file__).resolve().parent.parent

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 1080})
    page.goto(url)
    page.wait_for_load_state("networkidle")
    page.fill("#baseUrl", "http://127.0.0.1:8765")
    page.fill("#apiKey", "validator-key-1")
    time.sleep(6)
    page.screenshot(path=out_dir / "full_dashboard.png", full_page=True)
    leaderboard = page.locator("#leaderboard")
    has_table = leaderboard.locator("table").count() == 1
    has_tbody_rows = leaderboard.locator("tbody tr").count() >= 1
    content_text = (page.locator("#leaderboard .card-content").text_content() or "")
    with open(out_dir / "visual_check_report.txt", "w") as f:
        f.write(f"has_table: {has_table}\n")
        f.write(f"has_tbody_rows: {has_tbody_rows}\n")
        f.write(f"tbody row count: {leaderboard.locator('tbody tr').count()}\n")
        f.write(f"content length: {len(content_text)}\n")
        f.write(f"content preview: {repr(content_text[:200])}\n")
        f.write(f"contains '422': {'422' in content_text}\n")
    print(f"has_table={has_table}, has_tbody_rows={has_tbody_rows}, '422' in content={'422' in content_text}")
    browser.close()
