from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_returns_stable_success_envelope_and_request_id() -> None:
    with TestClient(create_app(Settings(environment="test"))) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}
    assert response.headers["X-Request-ID"]


def test_development_documentation_and_versioned_openapi_are_available() -> None:
    with TestClient(create_app(Settings(environment="test"))) as client:
        docs_response = client.get("/docs")
        redoc_response = client.get("/redoc")
        schema_response = client.get("/api/v1/openapi.json")

    assert docs_response.status_code == 200
    assert redoc_response.status_code == 200
    assert schema_response.status_code == 200
    schema = schema_response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["paths"]["/health"]["get"]["summary"] == "بررسی سلامت سرویس"


def test_documentation_is_not_exposed_in_production() -> None:
    settings = Settings(
        environment="production",
        docs_enabled=True,
        secret_key="test-only-production-secret-value-123456789",
        refresh_cookie_secure=True,
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/api/v1/openapi.json").status_code == 404
        assert client.get("/health").status_code == 200


def test_unknown_route_uses_safe_error_envelope() -> None:
    with TestClient(create_app(Settings(environment="test"))) as client:
        response = client.get("/does-not-exist")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "resource_not_found"
    assert payload["error"]["details"] is None
    assert payload["error"]["request_id"]
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]
    assert "traceback" not in response.text.lower()
