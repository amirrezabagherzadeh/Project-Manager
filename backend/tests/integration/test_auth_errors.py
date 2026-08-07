from typing import Annotated

from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import Settings
from app.core.exceptions import (
    authentication_required,
    permission_denied,
    rate_limited,
    resource_conflict,
    token_expired,
)
from app.main import create_app
from app.models.identity import User


def _client() -> TestClient:
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            secret_key="test-only-error-secret-" + ("x" * 40),
        )
    )

    @app.get("/test/protected")
    async def protected(
        _user: Annotated[User, Depends(get_current_user)],
    ) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/test/domain/{kind}")
    async def domain_error(kind: str) -> None:
        errors = {
            "auth": authentication_required(),
            "expired": token_expired(),
            "forbidden": permission_denied(),
            "conflict": resource_conflict(),
            "limited": rate_limited(37),
        }
        raise errors[kind]

    class Payload(BaseModel):
        count: int

    @app.post("/test/validation")
    async def validation(_payload: Payload) -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


def test_missing_bearer_token_uses_safe_authentication_envelope() -> None:
    with _client() as client:
        response = client.get("/test/protected")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "authentication_required"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_domain_errors_preserve_status_code_headers_and_safe_details() -> None:
    expectations = {
        "auth": (401, "authentication_required"),
        "expired": (401, "token_expired"),
        "forbidden": (403, "permission_denied"),
        "conflict": (409, "resource_conflict"),
        "limited": (429, "rate_limited"),
    }
    with _client() as client:
        for kind, (status_code, code) in expectations.items():
            response = client.get(f"/test/domain/{kind}")
            assert response.status_code == status_code
            assert response.json()["error"]["code"] == code
            assert response.json()["error"]["request_id"]
            assert "traceback" not in response.text.lower()
        limited = client.get("/test/domain/limited")

    assert limited.headers["Retry-After"] == "37"
    assert limited.json()["error"]["details"] == {"retry_after_seconds": 37}


def test_validation_error_stays_in_standard_envelope_without_input_value() -> None:
    sensitive_value = "must-not-appear"
    with _client() as client:
        response = client.post(
            "/test/validation",
            json={"count": sensitive_value},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert sensitive_value not in response.text
