"""Health and root endpoint tests."""
import pytest


class TestHealth:
    """Health check endpoint."""

    def test_health_returns_ok(self, client):
        """GET /health returns status ok."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_returns_message(self, client):
        """GET / returns API info."""
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "Karma" in data["message"]
        assert "/docs" in data["docs"]
