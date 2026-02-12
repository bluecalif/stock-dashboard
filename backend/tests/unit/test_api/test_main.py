"""Tests for FastAPI app skeleton — main.py, CORS, error handlers, health."""

from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app

# Temporary router to test the generic 500 handler
_error_router = APIRouter()


@_error_router.get("/v1/_test_500")
def _raise_error():
    raise RuntimeError("deliberate test error")


app.include_router(_error_router)


@pytest.fixture
def mock_db():
    """Return a mock SQLAlchemy session."""
    return MagicMock(spec=Session)


@pytest.fixture
def client(mock_db):
    """TestClient with mocked DB dependency."""
    from api.dependencies import get_db

    def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    def test_health_ok(self, client, mock_db):
        """GET /v1/health returns ok when DB is reachable."""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] == "connected"

    def test_health_db_disconnected(self, client, mock_db):
        """GET /v1/health returns disconnected when DB raises."""
        mock_db.execute.side_effect = Exception("connection refused")
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["db"] == "disconnected"


class TestCORS:
    def test_cors_allowed_origin(self, client):
        """CORS allows localhost:5173."""
        response = client.options(
            "/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_disallowed_origin(self, client):
        """CORS blocks unknown origins."""
        response = client.options(
            "/v1/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in response.headers


class TestErrorHandlers:
    def test_404_not_found(self, client):
        """Unknown route returns 404."""
        response = client.get("/v1/nonexistent")
        assert response.status_code == 404

    def test_generic_exception_handler(self, client):
        """Unhandled exceptions return 500 with structured error."""
        response = client.get("/v1/_test_500")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["detail"] == "Internal server error"


class TestAppMetadata:
    def test_openapi_available(self, client):
        """OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Stock Dashboard API"
        assert schema["info"]["version"] == "0.1.0"
