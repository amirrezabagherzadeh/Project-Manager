from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database

TEST_SECRET = "test-only-workspace-http-secret-" + ("x" * 48)


def test_phase_2_disposable_http_flow_and_docs(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "workspace-http-flow.db")
    app = create_app(
        Settings(
            environment="test",
            database_url=database_url,
            secret_key=TEST_SECRET,
            register_rate_limit_requests=20,
            login_rate_limit_requests=20,
        )
    )

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
        assert client.get("/api/v1/openapi.json").status_code == 200

        def register_and_login(email: str) -> str:
            registered = client.post(
                "/api/v1/auth/register",
                json={
                    "name": email.split("@")[0],
                    "email": email,
                    "password": "a-secure-password",
                },
            )
            assert registered.status_code == 201
            login = client.post(
                "/api/v1/auth/token",
                data={"username": email, "password": "a-secure-password"},
            )
            assert login.status_code == 200
            return login.json()["access_token"]

        owner = register_and_login("owner@example.com")
        admin = register_and_login("admin@example.com")
        member = register_and_login("member@example.com")
        invited = register_and_login("invited@example.com")

        def auth(token: str) -> dict[str, str]:
            return {"Authorization": f"Bearer {token}"}

        created = client.post(
            "/api/v1/workspaces",
            headers=auth(owner),
            json={"name": "Phase 2 Workspace"},
        )
        assert created.status_code == 201
        workspace_id = created.json()["data"]["id"]

        added_admin = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=auth(owner),
            json={"email": "admin@example.com", "role": "ADMIN"},
        )
        assert added_admin.status_code == 201
        added_member = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=auth(admin),
            json={"email": "member@example.com", "role": "MEMBER"},
        )
        assert added_member.status_code == 201
        promoted = client.patch(
            (f"/api/v1/workspaces/{workspace_id}/members/{added_member.json()['data']['id']}"),
            headers=auth(admin),
            json={"role": "PROJECT_MANAGER"},
        )
        assert promoted.status_code == 200

        invitation = client.post(
            f"/api/v1/workspaces/{workspace_id}/invitations",
            headers=auth(owner),
            json={"email": "invited@example.com", "role": "MEMBER"},
        )
        assert invitation.status_code == 201
        accepted = client.post(
            f"/api/v1/invitations/{invitation.json()['data']['token']}/accept",
            headers=auth(invited),
        )
        assert accepted.status_code == 200

        forbidden = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            headers=auth(member),
            json={"name": "Not allowed"},
        )
        assert forbidden.status_code == 403

        transfer = client.patch(
            (f"/api/v1/workspaces/{workspace_id}/members/{accepted.json()['data']['id']}"),
            headers=auth(owner),
            json={"role": "OWNER"},
        )
        assert transfer.status_code == 200
        archived = client.post(
            f"/api/v1/workspaces/{workspace_id}/archive",
            headers=auth(invited),
        )
        assert archived.status_code == 200
        assert archived.json()["data"]["archived_at"] is not None
        restored = client.post(
            f"/api/v1/workspaces/{workspace_id}/restore",
            headers=auth(invited),
        )
        assert restored.status_code == 200
        assert restored.json()["data"]["archived_at"] is None
