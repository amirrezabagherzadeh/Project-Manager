from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database

TEST_SECRET = "test-only-auth-api-secret-" + ("x" * 48)


def _client(
    tmp_path: Path,
    *,
    register_limit: int = 20,
    login_limit: int = 20,
) -> TestClient:
    database_url = migrate_database(tmp_path / "auth-api.db")
    app = create_app(
        Settings(
            environment="test",
            database_url=database_url,
            secret_key=TEST_SECRET,
            trusted_origins=["http://localhost:3000"],
            register_rate_limit_requests=register_limit,
            login_rate_limit_requests=login_limit,
        )
    )
    return TestClient(app)


def _register(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "کاربر آزمون",
            "email": "USER@Example.com",
            "password": "a-secure-password",
        },
    )
    assert response.status_code == 201


def _login(client: TestClient):
    return client.post(
        "/api/v1/auth/token",
        data={"username": "user@example.com", "password": "a-secure-password"},
    )


def test_register_login_and_me_http_contract(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        register = client.post(
            "/api/v1/auth/register",
            json={
                "name": "  کاربر آزمون  ",
                "email": "USER@Example.com",
                "password": "a-secure-password",
            },
        )
        assert register.status_code == 201
        assert register.json()["data"]["email"] == "user@example.com"
        assert register.json()["data"]["name"] == "کاربر آزمون"
        assert "password" not in register.text
        assert "set-cookie" not in register.headers

        duplicate = client.post(
            "/api/v1/auth/register",
            json={
                "name": "تکراری",
                "email": "user@example.com",
                "password": "another-secure-password",
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "resource_conflict"

        invalid = client.post(
            "/api/v1/auth/register",
            json={"name": " ", "email": "invalid", "password": "short"},
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "validation_error"

        wrong = client.post(
            "/api/v1/auth/token",
            data={"username": "user@example.com", "password": "wrong-password"},
        )
        assert wrong.status_code == 401
        assert wrong.json()["error"]["code"] == "invalid_credentials"

        login = _login(client)
        assert login.status_code == 200
        assert login.json()["token_type"] == "bearer"
        assert "HttpOnly" in login.headers["set-cookie"]

        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["data"]["email"] == "user@example.com"


def test_login_requires_oauth2_form_and_me_requires_bearer(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _register(client)
        json_login = client.post(
            "/api/v1/auth/token",
            json={"username": "user@example.com", "password": "a-secure-password"},
        )
        missing_bearer = client.get("/api/v1/auth/me")

    assert json_login.status_code == 422
    assert json_login.json()["error"]["code"] == "validation_error"
    assert missing_bearer.status_code == 401
    assert missing_bearer.json()["error"]["code"] == "authentication_required"


def test_refresh_origin_rotation_replay_and_logout(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _register(client)
        login = _login(client)
        assert login.status_code == 200
        old_refresh = client.cookies.get("ppm_refresh")
        assert old_refresh is not None

        untrusted = client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "https://attacker.test"},
        )
        assert untrusted.status_code == 403
        assert untrusted.json()["error"]["code"] == "permission_denied"

        refreshed = client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "http://localhost:3000"},
        )
        assert refreshed.status_code == 200
        new_refresh = client.cookies.get("ppm_refresh")
        assert new_refresh is not None
        assert new_refresh != old_refresh

        replay = client.post(
            "/api/v1/auth/refresh",
            headers={
                "Origin": "http://localhost:3000",
                "Cookie": f"ppm_refresh={old_refresh}",
            },
        )
        assert replay.status_code == 401
        assert replay.json()["error"]["code"] == "authentication_required"
        assert "Max-Age=0" in replay.headers["set-cookie"]

        client.cookies.set("ppm_refresh", new_refresh, path="/api/v1/auth")
        revoked = client.post("/api/v1/auth/refresh")
        assert revoked.status_code == 401

        logout = client.post("/api/v1/auth/logout")
        repeated_logout = client.post("/api/v1/auth/logout")
        assert logout.status_code == 204
        assert repeated_logout.status_code == 204


def test_register_and_login_rate_limits_are_independent(tmp_path: Path) -> None:
    with _client(tmp_path, register_limit=1, login_limit=1) as client:
        _register(client)
        limited_register = client.post(
            "/api/v1/auth/register",
            json={
                "name": "دوم",
                "email": "second@example.com",
                "password": "a-secure-password",
            },
        )
        first_login = _login(client)
        limited_login = _login(client)

    assert limited_register.status_code == 429
    assert limited_register.json()["error"]["code"] == "rate_limited"
    assert first_login.status_code == 200
    assert limited_login.status_code == 429
    assert limited_login.headers["Retry-After"]
