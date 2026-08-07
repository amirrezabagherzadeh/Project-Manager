from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database

TEST_SECRET = "test-only-http-flow-secret-" + ("x" * 48)


def test_phase_one_complete_http_acceptance_flow(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "phase-one-http-flow.db")
    app = create_app(
        Settings(
            environment="test",
            database_url=database_url,
            secret_key=TEST_SECRET,
            trusted_origins=["http://localhost:3000"],
            register_rate_limit_requests=3,
            login_rate_limit_requests=3,
        )
    )

    with TestClient(app) as client:
        for path in ("/health", "/docs", "/redoc", "/api/v1/openapi.json"):
            assert client.get(path).status_code == 200

        weak = client.post(
            "/api/v1/auth/register",
            json={
                "name": "کاربر",
                "email": "user@example.com",
                "password": "short",
            },
        )
        assert weak.status_code == 422

        registered = client.post(
            "/api/v1/auth/register",
            json={
                "name": "کاربر اصلی",
                "email": "USER@Example.com",
                "password": "a-secure-password",
            },
        )
        assert registered.status_code == 201
        assert registered.json()["data"]["email"] == "user@example.com"
        assert "password" not in registered.text

        duplicate = client.post(
            "/api/v1/auth/register",
            json={
                "name": "تکراری",
                "email": "user@example.com",
                "password": "another-secure-password",
            },
        )
        assert duplicate.status_code == 409

        second_user = client.post(
            "/api/v1/auth/register",
            json={
                "name": "کاربر دوم",
                "email": "second@example.com",
                "password": "a-second-password",
            },
        )
        assert second_user.status_code == 201

        limited_registration = client.post(
            "/api/v1/auth/register",
            json={
                "name": "کاربر سوم",
                "email": "third@example.com",
                "password": "a-third-password",
            },
        )
        assert limited_registration.status_code == 429
        assert limited_registration.json()["error"]["code"] == "rate_limited"

        invalid_login = client.post(
            "/api/v1/auth/token",
            data={"username": "user@example.com", "password": "wrong-password"},
        )
        assert invalid_login.status_code == 401
        assert invalid_login.json()["error"]["code"] == "invalid_credentials"

        login = client.post(
            "/api/v1/auth/token",
            data={"username": "user@example.com", "password": "a-secure-password"},
        )
        assert login.status_code == 200
        access_token = login.json()["access_token"]
        original_refresh = client.cookies.get("ppm_refresh")
        assert original_refresh is not None

        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me.status_code == 200
        assert me.json()["data"]["email"] == "user@example.com"

        untrusted_refresh = client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "https://attacker.example"},
        )
        assert untrusted_refresh.status_code == 403

        refreshed = client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "http://localhost:3000"},
        )
        assert refreshed.status_code == 200
        replacement_refresh = client.cookies.get("ppm_refresh")
        assert replacement_refresh is not None
        assert replacement_refresh != original_refresh

        replay = client.post(
            "/api/v1/auth/refresh",
            headers={"Cookie": f"ppm_refresh={original_refresh}"},
        )
        assert replay.status_code == 401
        assert replay.json()["error"]["code"] == "authentication_required"

        revoked_replacement = client.post(
            "/api/v1/auth/refresh",
            headers={"Cookie": f"ppm_refresh={replacement_refresh}"},
        )
        assert revoked_replacement.status_code == 401

        second_login = client.post(
            "/api/v1/auth/token",
            data={"username": "second@example.com", "password": "a-second-password"},
        )
        assert second_login.status_code == 200
        logout_refresh = client.cookies.get("ppm_refresh")
        assert logout_refresh is not None

        logout = client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "http://localhost:3000"},
        )
        assert logout.status_code == 204
        assert "Max-Age=0" in logout.headers["set-cookie"]

        revoked_after_logout = client.post(
            "/api/v1/auth/refresh",
            headers={"Cookie": f"ppm_refresh={logout_refresh}"},
        )
        assert revoked_after_logout.status_code == 401

        third_failed_login = client.post(
            "/api/v1/auth/token",
            data={"username": "user@example.com", "password": "wrong-password"},
        )
        assert third_failed_login.status_code == 401
        limited_login = client.post(
            "/api/v1/auth/token",
            data={"username": "user@example.com", "password": "wrong-password"},
        )
        assert limited_login.status_code == 429
        assert limited_login.headers["Retry-After"]
