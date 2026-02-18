#!/usr/bin/env bash
# Start Karma API and open UI test harness
# Usage: ./scripts/start-for-ui-test.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HARNESS="$PROJECT_ROOT/tests/ui/test_harness.html"

echo "Karma Platform v3 - UI Testing"
echo "==============================="
echo ""
echo "1. Ensure .env has ADMIN_API_KEY=test-admin-key"
echo "2. API will start on http://localhost:8000"
echo "3. Opening test harness in browser..."
echo ""

cd "$PROJECT_ROOT"

# Open harness (macOS/Linux)
if command -v xdg-open &> /dev/null; then
  xdg-open "$HARNESS"
elif command -v open &> /dev/null; then
  open "$HARNESS"
fi

# Start API (foreground - Ctrl+C to stop)
python -m uvicorn app.main:app --reload --port 8000
