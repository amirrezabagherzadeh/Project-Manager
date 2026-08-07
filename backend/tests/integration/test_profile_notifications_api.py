from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database


def test_profile_notifications_and_global_dashboard(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                environment="test",
                database_url=migrate_database(tmp_path / "profile.db"),
                secret_key="profile-test-secret-" + ("x" * 48),
                attachment_storage_path=tmp_path / "uploads",
            )
        )
    )
    with api:
        email = "profile@example.com"
        assert (
            api.post(
                "/api/v1/auth/register",
                json={"name": "Profile", "email": email, "password": "a-secure-password"},
            ).status_code
            == 201
        )
        token = api.post(
            "/api/v1/auth/token", data={"username": email, "password": "a-secure-password"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        profile = api.patch(
            "/api/v1/auth/profile",
            headers=headers,
            json={"name": "Updated", "timezone": "Asia/Tehran"},
        )
        assert profile.status_code == 200 and profile.json()["data"]["timezone"] == "Asia/Tehran"
        avatar = api.post(
            "/api/v1/auth/profile/avatar",
            headers=headers,
            files={"file": ("avatar.png", b"png", "image/png")},
        )
        assert (
            avatar.status_code == 200
            and avatar.json()["data"]["avatar_content_type"] == "image/png"
        )
        downloaded_avatar = api.get("/api/v1/auth/profile/avatar", headers=headers)
        assert downloaded_avatar.status_code == 200
        assert downloaded_avatar.content == b"png"
        assert downloaded_avatar.headers["content-type"] == "image/png"
        assert (
            api.post(
                "/api/v1/auth/profile/avatar",
                headers=headers,
                files={"file": ("bad.txt", b"x", "text/plain")},
            ).status_code
            == 415
        )
        assert api.get("/api/v1/notifications", headers=headers).json()["unread_count"] == 0
        assert api.get("/api/v1/notifications/unread-count", headers=headers).json()["data"] == 0
        assert api.post("/api/v1/notifications/read-all", headers=headers).status_code == 204
        assert api.get("/api/v1/dashboard", headers=headers).json()["data"] == {
            "projects": 0,
            "tasks": 0,
            "completed": 0,
            "overdue": 0,
        }
        assert api.delete("/api/v1/auth/profile/avatar", headers=headers).status_code == 204
        assert api.get("/api/v1/auth/profile/avatar", headers=headers).status_code == 404
