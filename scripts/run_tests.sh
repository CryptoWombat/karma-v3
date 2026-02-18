#!/bin/bash
# Karma v3 - Test runner
# Usage:
#   ./scripts/run_tests.sh           # API + E2E + regression
#   ./scripts/run_tests.sh --coverage
#   ./scripts/run_tests.sh --visual   # Include Playwright tests
#   ./scripts/run_tests.sh --regress  # Regression only

cd "$(dirname "$0")/.."
ARGS=(-v --tb=short)

case "${1:-}" in
    --coverage) ARGS+=(--cov=app --cov-report=html --cov-report=term-missing) ;;
    --visual)   ;;  # include ui tests
    --regress)  exec python -m pytest tests/test_regression.py "${ARGS[@]}" ;;
    *)          ARGS+=(--ignore=tests/ui/) ;;
esac

[ "$1" != "--regress" ] && exec python -m pytest tests/ "${ARGS[@]}"
