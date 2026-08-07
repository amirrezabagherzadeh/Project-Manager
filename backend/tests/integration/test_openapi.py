import json

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_phase_one_openapi_contract_and_documentation_are_complete() -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            secret_key="test-only-openapi-secret-" + ("x" * 48),
        )
    )
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
        response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    operations = {
        ("post", "/api/v1/auth/register"): {"201", "409", "422", "429"},
        ("post", "/api/v1/auth/token"): {"200", "401", "422", "429"},
        ("post", "/api/v1/auth/refresh"): {"200", "401", "403"},
        ("post", "/api/v1/auth/logout"): {"204", "403"},
        ("get", "/api/v1/auth/me"): {"200", "401"},
    }
    for (method, path), expected_responses in operations.items():
        operation = schema["paths"][path][method]
        assert operation["summary"]
        assert operation["description"]
        assert operation["tags"] == ["authentication"]
        assert expected_responses.issubset(operation["responses"])

    token_request = schema["paths"]["/api/v1/auth/token"]["post"]["requestBody"]
    assert "application/x-www-form-urlencoded" in token_request["content"]

    security_scheme = schema["components"]["securitySchemes"]["OAuth2Password"]
    password_flow = security_scheme["flows"]["password"]
    assert password_flow["tokenUrl"] == "/api/v1/auth/token"
    assert schema["paths"]["/api/v1/auth/me"]["get"]["security"] == [{"OAuth2Password": []}]

    serialized = json.dumps(schema)
    for private_field in (
        "password_hash",
        "token_hash",
        "replaced_by_id",
        "replay_detected_at",
    ):
        assert private_field not in serialized

    assert schema["paths"]["/api/v1/auth/register"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["example"]
    assert schema["paths"]["/api/v1/auth/token"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]
