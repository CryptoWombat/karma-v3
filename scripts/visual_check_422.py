"""Reproduce the 422 scenario - invalid limit triggers API 422."""
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
    time.sleep(5)
    # Inject invalid limit into the select to trigger 422
    page.evaluate("""
        () => {
            const sel = document.getElementById('topHoldersLimit');
            const opt = document.createElement('option');
            opt.value = '422';
            opt.textContent = '422';
            sel.appendChild(opt);
            sel.value = '422';
            sel.dispatchEvent(new Event('change'));
        }
    """)
    time.sleep(4)
    leaderboard = page.locator("#leaderboard")
    content = page.locator("#leaderboard .card-content").inner_html()
    leaderboard.screenshot(path=out_dir / "leaderboard_422_scenario.png")
    with open(out_dir / "leaderboard_422_content.txt", "w") as f:
        f.write(content)
    print("Content:", content[:500])
    browser.close()
