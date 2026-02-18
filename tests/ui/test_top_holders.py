"""Top Holders component — thorough functionality tests.

Uses network interception to verify correct limit parameter in API requests.
Runs against live API (live_server fixture). See docs/TEST_SCENARIOS_TOP_HOLDERS.md.
"""
import time

import pytest

from tests.ui.test_visual import API_URL, HAS_PLAYWRIGHT, live_server

# Use same server as test_visual when run together
TOP_HOLDERS_API_URL = API_URL

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

def _parse_limit_from_url(url: str) -> str | None:
    """Extract limit query param from leaderboard URL."""
    if "?" not in url:
        return None
    qs = url.split("?")[1]
    for part in qs.split("&"):
        if part.startswith("limit="):
            return part.split("=")[1]
    return None


def _wait_for_leaderboard_load(page, timeout_ms=6000):
    """Wait until leaderboard shows data or error (not loading)."""
    card = page.locator("#leaderboard")
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        text = (card.text_content() or "").lower()
        if "loading" not in text and len(text.strip()) > 20:
            return True
        time.sleep(0.3)
    return False


@pytest.mark.skipif(not HAS_PLAYWRIGHT, reason="Playwright not installed")
class TestTopHoldersScenarios:
    """Thorough Top Holders functionality tests — maps to docs/TEST_SCENARIOS_TOP_HOLDERS.md."""

    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()

    @pytest.fixture
    def page_with_capture(self, browser, live_server):
        """Page that captures leaderboard request URLs."""
        captured = []

        def handle(route, request):
            if "/leaderboard" in request.url:
                captured.append(request.url)
            route.continue_()

        page = browser.new_page()
        page.route("**/*", handle)
        page._leaderboard_urls = captured
        page.goto(f"{TOP_HOLDERS_API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", TOP_HOLDERS_API_URL)
        page.fill("#apiKey", "validator-key-1")
        yield page
        page.close()

    @pytest.fixture
    def validator_page(self, browser, live_server):
        """Standard validator page (no capture)."""
        page = browser.new_page()
        page.goto(f"{TOP_HOLDERS_API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", TOP_HOLDERS_API_URL)
        page.fill("#apiKey", "validator-key-1")
        yield page
        page.close()

    # --- A. Initial Load & Structure ---

    def test_th_a1_default_limit_first_visit(self, page_with_capture):
        """TH-A1: Default limit 10 on first visit."""
        captured = page_with_capture._leaderboard_urls
        page_with_capture.wait_for_timeout(5000)
        assert len(captured) >= 1, "At least one leaderboard request"
        limit = _parse_limit_from_url(captured[0])
        assert limit == "10", f"First request should have limit=10, got limit={limit} in {captured[0]}"

    def test_th_a2_limit_selector_present(self, validator_page):
        """TH-A2: Limit selector with options 10, 25, 50, 100."""
        validator_page.wait_for_timeout(500)
        sel = validator_page.locator("#topHoldersLimit")
        assert sel.count() == 1
        opts = sel.locator("option")
        assert opts.count() == 4
        values = [o.get_attribute("value") for o in opts.all()]
        assert set(values) == {"10", "25", "50", "100"}

    def test_th_a3_card_structure(self, validator_page):
        """TH-A3: Card has header, selector, content."""
        validator_page.wait_for_timeout(5000)
        card = validator_page.locator("#leaderboard")
        assert card.locator(".card-header-row").count() == 1
        assert card.locator("#topHoldersLimit").count() == 1
        assert card.locator(".card-content").count() == 1

    def test_resize_buttons_present(self, validator_page):
        """Resize button (⊞) present on every card."""
        validator_page.wait_for_timeout(3000)
        for card_id in ["leaderboard", "health", "snapshot", "inflation", "transactions"]:
            card = validator_page.locator(f"#{card_id}")
            resize = card.locator(".card-resize[data-card='" + card_id + "']")
            assert resize.count() == 1, f"Card {card_id} must have resize button"

    def test_th_a4_card_content_preserved(self, validator_page):
        """TH-A4: Exactly one .card-content after load."""
        validator_page.wait_for_timeout(5000)
        content = validator_page.locator("#leaderboard .card-content")
        assert content.count() == 1

    # --- B. Limit Selector Behavior ---

    def test_th_b1_change_to_25(self, page_with_capture):
        """TH-B1: Change to 25, API uses limit=25."""
        page_with_capture.wait_for_timeout(4500)
        captured = page_with_capture._leaderboard_urls
        initial_count = len(captured)
        page_with_capture.select_option("#topHoldersLimit", "25")
        page_with_capture.wait_for_timeout(2500)
        assert len(captured) > initial_count
        last_url = captured[-1]
        assert "limit=25" in last_url, f"Last request should have limit=25: {last_url}"
        card = page_with_capture.locator("#leaderboard")
        assert "failed to fetch" not in (card.text_content() or "").lower()

    def test_th_b2_change_to_50(self, page_with_capture):
        """TH-B2: Change to 50, API uses limit=50."""
        page_with_capture.wait_for_timeout(4500)
        captured = page_with_capture._leaderboard_urls
        initial = len(captured)
        page_with_capture.select_option("#topHoldersLimit", "50")
        page_with_capture.wait_for_timeout(2500)
        assert len(captured) > initial
        assert "limit=50" in captured[-1]

    def test_th_b3_change_to_100(self, page_with_capture):
        """TH-B3: Change to 100, API uses limit=100."""
        page_with_capture.wait_for_timeout(4500)
        captured = page_with_capture._leaderboard_urls
        initial = len(captured)
        page_with_capture.select_option("#topHoldersLimit", "100")
        page_with_capture.wait_for_timeout(2500)
        assert len(captured) > initial
        assert "limit=100" in captured[-1]

    def test_th_b4_selector_persists_after_content_update(self, validator_page):
        """TH-B4: Selector persists after limit change and reload."""
        validator_page.wait_for_timeout(4500)
        validator_page.select_option("#topHoldersLimit", "50")
        validator_page.wait_for_timeout(2500)
        sel = validator_page.locator("#topHoldersLimit")
        assert sel.count() == 1, "Selector must persist after content update"
        assert sel.input_value() == "50"

    def test_th_b5_multiple_rapid_changes(self, page_with_capture):
        """TH-B5: Rapid 10→25→50→100, final request uses 100."""
        page_with_capture.wait_for_timeout(4500)
        captured = page_with_capture._leaderboard_urls
        initial = len(captured)
        for val in ["25", "50", "100"]:
            page_with_capture.select_option("#topHoldersLimit", val)
        page_with_capture.wait_for_timeout(3000)
        assert len(captured) > initial
        assert "limit=100" in captured[-1]
        assert page_with_capture.locator("#topHoldersLimit").count() == 1

    # --- C. Limit Persistence ---

    def test_th_c1_limit_saved_after_change(self, validator_page):
        """TH-C1: localStorage saved after limit change."""
        validator_page.wait_for_timeout(4500)
        validator_page.select_option("#topHoldersLimit", "50")
        validator_page.wait_for_timeout(2500)
        saved = validator_page.evaluate(
            "() => localStorage.getItem('karma-validator-top-holders-limit')"
        )
        assert saved == "50", f"Expected localStorage '50', got {saved}"

    def test_th_c2_limit_restored_on_reload_first_request(self, browser, live_server):
        """TH-C2: Reload with saved limit 50 — first API request uses limit=50."""
        captured = []

        def handle(route, request):
            if "/leaderboard" in request.url:
                captured.append(request.url)
            route.continue_()

        page = browser.new_page()
        page.route("**/*", handle)
        page.goto(f"{TOP_HOLDERS_API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", TOP_HOLDERS_API_URL)
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(4500)
        page.select_option("#topHoldersLimit", "50")
        page.wait_for_timeout(2500)
        captured.clear()
        page.reload()
        page.wait_for_load_state("networkidle")
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(5500)
        assert len(captured) >= 1, "At least one leaderboard request after reload"
        limit = _parse_limit_from_url(captured[0])
        assert limit == "50", (
            f"First request after reload should use restored limit=50, got limit={limit} in {captured[0]}"
        )
        assert page.locator("#topHoldersLimit").input_value() == "50"
        page.close()

    def test_th_c3_invalid_saved_limit_fallback(self, browser, live_server):
        """TH-C3: Invalid saved limit (e.g. 99 or 422) falls back to 10 and table renders."""
        captured = []

        def handle(route, request):
            if "/leaderboard" in request.url:
                captured.append(request.url)
            route.continue_()

        page = browser.new_page()
        page.route("**/*", handle)
        page.goto(f"{TOP_HOLDERS_API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.evaluate("() => localStorage.setItem('karma-validator-top-holders-limit', '422')")
        page.reload()
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", TOP_HOLDERS_API_URL)
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(5500)
        assert len(captured) >= 1
        limit = _parse_limit_from_url(captured[0])
        assert limit == "10", f"Invalid saved limit 422 should fallback to 10, got {limit}"
        table = page.locator("#leaderboard table")
        assert table.count() == 1, "Table must render after invalid limit fallback"
        assert page.locator("#leaderboard tbody tr").count() >= 1
        page.close()

    # --- D. Load Triggers ---

    def test_th_d1_load_all_uses_current_limit(self, page_with_capture):
        """TH-D1: Load All uses current limit (50)."""
        page_with_capture.wait_for_timeout(4500)
        page_with_capture.select_option("#topHoldersLimit", "50")
        page_with_capture.wait_for_timeout(1500)
        captured = page_with_capture._leaderboard_urls
        initial = len(captured)
        page_with_capture.click("button:has-text('Load All')")
        page_with_capture.wait_for_timeout(4000)
        assert len(captured) > initial
        last_leaderboard = [u for u in captured[initial:] if "/leaderboard" in u][-1]
        assert "limit=50" in last_leaderboard

    def test_th_d2_top_holders_button_uses_current_limit(self, page_with_capture):
        """TH-D2: Top Holders button uses current limit (25)."""
        page_with_capture.wait_for_timeout(4500)
        page_with_capture.select_option("#topHoldersLimit", "25")
        page_with_capture.wait_for_timeout(1500)
        captured = page_with_capture._leaderboard_urls
        initial = len(captured)
        page_with_capture.click("button:has-text('Top Holders')")
        page_with_capture.wait_for_timeout(2500)
        assert len(captured) > initial
        last_leaderboard = [u for u in captured[initial:] if "/leaderboard" in u][-1]
        assert "limit=25" in last_leaderboard

    def test_th_d3_load_all_twice_preserves_controls(self, validator_page):
        """TH-D3: Load All twice — selector persists."""
        validator_page.wait_for_timeout(4500)
        validator_page.click("button:has-text('Load All')")
        validator_page.wait_for_timeout(4000)
        validator_page.click("button:has-text('Load All')")
        validator_page.wait_for_timeout(4000)
        assert validator_page.locator("#topHoldersLimit").count() == 1

    def test_th_d4_top_holders_button_twice_preserves_controls(self, validator_page):
        """TH-D4: Top Holders button twice — selector persists."""
        validator_page.wait_for_timeout(4500)
        validator_page.click("button:has-text('Top Holders')")
        validator_page.wait_for_timeout(2500)
        validator_page.click("button:has-text('Top Holders')")
        validator_page.wait_for_timeout(2500)
        assert validator_page.locator("#topHoldersLimit").count() == 1

    # --- E. Restored Order Interaction ---

    def test_th_e2_drag_then_change_limit(self, page_with_capture):
        """TH-E2: After dragging leaderboard card, limit change still works."""
        page_with_capture.wait_for_timeout(4500)
        # Drag leaderboard card to first position (use handle to trigger Sortable)
        leaderboard_handle = page_with_capture.locator("#leaderboard .card-drag-handle")
        health = page_with_capture.locator("#health")
        leaderboard_handle.drag_to(health)
        page_with_capture.wait_for_timeout(500)
        # Change limit - must still work after DOM reorder
        captured = page_with_capture._leaderboard_urls
        initial = len(captured)
        page_with_capture.select_option("#topHoldersLimit", "50")
        page_with_capture.wait_for_timeout(2500)
        assert len(captured) > initial, "Limit change should trigger request after drag"
        assert "limit=50" in captured[-1]
        assert page_with_capture.locator("#topHoldersLimit").count() == 1

    def test_th_e1_restored_limit_after_restore_order(self, browser, live_server):
        """TH-E1: Custom order + limit 50 saved, reload — first request uses limit=50."""
        captured = []

        def handle(route, request):
            if "/leaderboard" in request.url:
                captured.append(request.url)
            route.continue_()

        page = browser.new_page()
        page.route("**/*", handle)
        page.goto(f"{TOP_HOLDERS_API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", TOP_HOLDERS_API_URL)
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(4500)
        page.select_option("#topHoldersLimit", "50")
        page.wait_for_timeout(2000)
        page.evaluate(
            """() => {
            localStorage.setItem('karma-validator-dashboard-order',
                JSON.stringify(['leaderboard','health','snapshot','inflation','transactions']));
            localStorage.setItem('karma-validator-top-holders-limit', '50');
        }"""
        )
        captured.clear()
        page.reload()
        page.wait_for_load_state("networkidle")
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(5500)
        assert len(captured) >= 1
        limit = _parse_limit_from_url(captured[0])
        assert limit == "50", (
            f"With restored order + limit, first request should use limit=50, got {limit}"
        )
        page.close()

    # --- F. Error & Edge States ---

    def test_th_f1_api_error_preserves_selector(self, validator_page):
        """TH-F1: Invalid API key — error shown, selector persists."""
        validator_page.wait_for_timeout(500)
        validator_page.fill("#apiKey", "invalid-key-xyz")
        validator_page.click("button:has-text('Top Holders')")
        validator_page.wait_for_timeout(3000)
        card = validator_page.locator("#leaderboard")
        assert "unauthorized" in (card.text_content() or "").lower()
        assert validator_page.locator("#topHoldersLimit").count() == 1

    def test_th_f3_no_saved_limit_default_10(self, browser, live_server):
        """TH-F3: No saved limit (fresh context) — first request uses limit=10."""
        captured = []

        def handle(route, request):
            if "/leaderboard" in request.url:
                captured.append(request.url)
            route.continue_()

        context = browser.new_context()  # Fresh storage, no prior localStorage
        page = context.new_page()
        page.route("**/*", handle)
        page.goto(f"{TOP_HOLDERS_API_URL}/app/validator.html")
        page.wait_for_load_state("networkidle")
        page.fill("#baseUrl", TOP_HOLDERS_API_URL)
        page.fill("#apiKey", "validator-key-1")
        page.wait_for_timeout(5500)
        assert len(captured) >= 1
        limit = _parse_limit_from_url(captured[0])
        assert limit == "10", f"First visit should default to limit=10, got {limit}"
        context.close()

    # --- G. Data Integrity ---

    def test_th_g1_row_count_bounded_by_limit(self, validator_page):
        """TH-G1: Table has ≤ limit rows when limit=25."""
        validator_page.wait_for_timeout(4500)
        validator_page.select_option("#topHoldersLimit", "25")
        validator_page.wait_for_timeout(2500)
        rows = validator_page.locator("#leaderboard tbody tr")
        count = rows.count()
        assert count <= 25, f"Table should have ≤25 rows, got {count}"
        card = validator_page.locator("#leaderboard")
        assert "failed to fetch" not in (card.text_content() or "").lower()

    def test_th_g2_leaderboard_table_renders_when_data_exists(self, validator_page):
        """Regression: When API returns top_wallets, the table must be visible (Bug: table missing)."""
        validator_page.wait_for_timeout(4500)
        card = validator_page.locator("#leaderboard")
        content = card.locator(".card-content")
        table = content.locator("table")
        tbody_rows = content.locator("tbody tr")
        assert table.count() == 1, "Leaderboard must have a table when API returns data"
        assert tbody_rows.count() >= 1, "Leaderboard table must have data rows when wallets exist"
        assert "failed to fetch" not in (content.text_content() or "").lower()

    def test_th_g3_inflation_referral_header_visible(self, validator_page):
        """Regression: Inflation table must show full 'Referral' header (Bug: truncated to 'R')."""
        validator_page.wait_for_timeout(4500)
        inflation = validator_page.locator("#inflation")
        assert "Referral" in (inflation.text_content() or ""), "Inflation table must display full 'Referral' column header"
