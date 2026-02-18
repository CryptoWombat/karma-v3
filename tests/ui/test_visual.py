"""Visual verification tests using Playwright against the test harness.

Requires: pip install playwright && playwright install chromium
Visual tests need a running API server. Run in two steps:
  1. python -m uvicorn app.main:app --port 8000  (in one terminal)
  2. pytest tests/ui/test_visual.py -v
Or use: pytest tests/ --run-visual (custom marker, starts server automatically).
"""
import os
import subprocess
import sys
import pytest
import time
from pathlib import Path

# Set test env for server subprocess
TEST_ENV = {
    **os.environ,
    "TESTING": "1",
    "DATABASE_URL": "sqlite:///./test_visual.db",
    "ADMIN_API_KEY": "test-admin-key",
    "VALIDATOR_API_KEYS": "validator-key-1,validator-key-2",
}

HARNESS_PATH = Path(__file__).parent / "test_harness.html"
API_URL = "http://127.0.0.1:8765"  # Different port to avoid conflicts

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


def _wait_for_api(timeout=15):
    """Wait for API to be reachable."""
    import urllib.request
    import urllib.error
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(API_URL + "/health")
            with urllib.request.urlopen(req, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def live_server():
    """Start API server for visual tests."""
    proj_root = Path(__file__).resolve().parents[2]
    db_path = proj_root / "test_visual.db"
    for suffix in ("", "-wal", "-shm"):
        p = proj_root / f"test_visual.db{suffix}"
        if p.exists():
            p.unlink()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8765"],
        cwd=Path(__file__).resolve().parents[2],
        env={**TEST_ENV, "DATABASE_URL": "sqlite:///./test_visual.db", "VALIDATOR_API_KEYS": "validator-key-1,validator-key-2"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not _wait_for_api():
        proc.kill()
        pytest.skip("Could not start API server for visual tests")
    yield proc
    proc.terminate()
    proc.wait(timeout=5)


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed (pip install playwright && playwright install chromium)")
class TestVisualHarness:
    """Visual verification via test harness HTML page."""

    @pytest.fixture(scope="class")
    def browser(self):
        """Launch browser for visual tests."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()

    @pytest.fixture
    def page(self, browser, live_server):
        """Page with harness loaded. API must be running."""
        page = browser.new_page()
        harness_url = f"file://{HARNESS_PATH.absolute().as_posix()}"
        page.goto(harness_url)
        page.fill("#baseUrl", API_URL)
        page.fill("#adminKey", "test-admin-key")
        yield page
        page.close()

    def test_harness_loads(self, page):
        """Test harness page loads with title."""
        assert "Karma" in page.title()
        assert page.locator("h1").text_content()

    def test_health_button_flow(self, page):
        """Click Health Check and verify response area shows OK."""
        page.click("button:has-text('Health Check')")
        page.wait_for_selector("#output", state="visible", timeout=5000)
        text = page.locator("#output").text_content()
        assert "ok" in text.lower() or "200" in text
        assert page.locator("#output.ok").count() == 1

    def test_full_flow_visual(self, page):
        """Run full flow and verify success (green result box)."""
        page.click("button:has-text('Run Full Flow')")
        page.wait_for_selector("#output", state="visible", timeout=15000)
        time.sleep(0.5)
        text = page.locator("#output").text_content()
        has_ok = page.locator("#output.ok").count() == 1
        assert "150" in text, f"Expected balance 150 in: {text[:300]}"
        assert has_ok, f"Expected success. Output: {text[:400]}"


def test_harness_file_exists():
    """Smoke: harness HTML exists and is valid."""
    assert HARNESS_PATH.exists()
    content = HARNESS_PATH.read_text()
    assert "Karma" in content
    assert "Run Full Flow" in content


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestValidatorDashboard:
    """Visual verification of validator dashboard - all sections must load with validator key."""

    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()

    @pytest.fixture
    def validator_page(self, browser, live_server):
        """Load validator dashboard, fill API key, ready for Load All."""
        page = browser.new_page()
        # Validator dashboard is at /app/validator.html (static mount)
        page.goto(f"{API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", API_URL)
        page.fill("#apiKey", "validator-key-1")
        yield page
        page.close()

    def test_validator_auto_loads_on_open(self, validator_page):
        """Data loads automatically on page open without clicking Load All."""
        page = validator_page
        page.wait_for_timeout(4500)  # Auto-load runs on init
        for section_id in ["health", "snapshot", "inflation", "leaderboard", "transactions"]:
            card = page.locator(f"#{section_id}")
            text = (card.text_content() or "").lower()
            assert "unauthorized" not in text, f"Section {section_id} shows unauthorized"
            assert "failed to fetch" not in text, f"Section {section_id} shows Failed to fetch"
            assert len(text.strip()) > 30, f"Section {section_id} has insufficient data"

    def test_validator_load_all_succeeds(self, validator_page):
        """Click Load All and verify all 5 sections show data (no unauthorized, no Failed to fetch)."""
        page = validator_page
        page.click("button:has-text('Load All')")
        page.wait_for_timeout(4000)  # Wait for all fetches
        for section_id in ["health", "snapshot", "inflation", "leaderboard", "transactions"]:
            card = page.locator(f"#{section_id}")
            text = (card.text_content() or "").lower()
            assert "unauthorized" not in text, f"Section {section_id} shows unauthorized"
            assert "failed to fetch" not in text, f"Section {section_id} shows Failed to fetch"
            assert len(text.strip()) > 30, f"Section {section_id} has insufficient data"

    def test_top_holders_card_has_limit_selector(self, validator_page):
        """Top Holders card shows limit selector with options 10, 25, 50, 100."""
        page = validator_page
        page.wait_for_timeout(500)
        assert page.locator("h3:has-text('Top Holders')").count() == 1
        sel = page.locator("#topHoldersLimit")
        assert sel.count() == 1
        options = sel.locator("option")
        assert options.count() == 4
        values = [o.get_attribute("value") for o in options.all()]
        assert set(values) == {"10", "25", "50", "100"}

    def test_top_holders_limit_change_reloads(self, validator_page):
        """Changing Top Holders limit triggers reload and shows data."""
        page = validator_page
        page.wait_for_timeout(4500)  # Initial auto-load
        page.select_option("#topHoldersLimit", "25")
        page.wait_for_timeout(2500)  # Reload after change
        card = page.locator("#leaderboard")
        text = (card.text_content() or "").lower()
        assert "unauthorized" not in text
        assert "failed to fetch" not in text
        assert len(text.strip()) > 50, "Leaderboard should have data after limit change"

    def test_top_holders_limit_selector_persists_after_reload(self, validator_page):
        """CRITICAL: Limit selector must still exist after changing limit (was destroyed by Bug 1)."""
        page = validator_page
        page.wait_for_timeout(4500)  # Initial auto-load
        page.select_option("#topHoldersLimit", "50")
        page.wait_for_timeout(2500)  # Reload after change
        sel = page.locator("#topHoldersLimit")
        assert sel.count() == 1, "Limit selector must persist after reload"
        assert sel.input_value() == "50", "Selector should show selected value 50"

    def test_top_holders_multiple_limit_changes(self, validator_page):
        """Changing limit multiple times must keep selector and show correct data."""
        page = validator_page
        page.wait_for_timeout(4500)  # Initial auto-load
        page.select_option("#topHoldersLimit", "25")
        page.wait_for_timeout(2000)
        page.select_option("#topHoldersLimit", "100")
        page.wait_for_timeout(2500)
        sel = page.locator("#topHoldersLimit")
        assert sel.count() == 1, "Selector must persist after multiple changes"
        assert sel.input_value() == "100"
        card = page.locator("#leaderboard")
        assert "failed to fetch" not in (card.text_content() or "").lower()

    def test_top_holders_limit_persists_across_reload(self, validator_page):
        """Saved limit (localStorage) must be restored after page reload."""
        page = validator_page
        page.wait_for_timeout(4500)  # Initial auto-load
        page.select_option("#topHoldersLimit", "50")
        page.wait_for_timeout(2500)  # Load completes, localStorage saved
        page.reload()
        page.wait_for_load_state("networkidle")
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(4500)  # Auto-load after reload
        sel = page.locator("#topHoldersLimit")
        assert sel.count() == 1, "Limit selector must exist after reload"
        assert sel.input_value() == "50", "Limit 50 must be restored from localStorage"
        card = page.locator("#leaderboard")
        assert "failed to fetch" not in (card.text_content() or "").lower()

    def test_validator_cards_preserve_card_content_structure(self, validator_page):
        """All cards must retain .card-content after load (structural integrity for subsequent loads)."""
        page = validator_page
        page.wait_for_timeout(4500)  # Auto-load
        for section_id in ["health", "snapshot", "inflation", "leaderboard", "transactions"]:
            card = page.locator(f"#{section_id}")
            content = card.locator(".card-content")
            assert content.count() == 1, f"Section {section_id} must have exactly one .card-content after load"

    def test_validator_reload_section_preserves_controls(self, validator_page):
        """Re-loading a section (e.g. Load All twice) must not destroy controls like limit selector."""
        page = validator_page
        page.wait_for_timeout(4500)  # Initial auto-load
        page.click("button:has-text('Top Holders')")  # Re-load leaderboard
        page.wait_for_timeout(2500)
        assert page.locator("#topHoldersLimit").count() == 1, "Limit selector must survive re-load"

    def test_dashboard_grid_is_sortable(self, validator_page):
        """Dashboard has sortable grid with all 5 cards (drag-and-drop enabled)."""
        page = validator_page
        page.wait_for_timeout(500)
        grid = page.locator("#dashboardGrid")
        assert grid.count() == 1
        cards = grid.locator(".card")
        assert cards.count() == 5
        assert page.locator('script[src*="sortablejs"]').count() == 1
