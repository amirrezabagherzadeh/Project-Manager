from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database

TEST_SECRET = "test-only-project-http-secret-" + ("x" * 48)


def test_phase_3_disposable_http_flow_and_docs(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "project-http-flow.db")
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
        member = register_and_login("member@example.com")
        outsider = register_and_login("outsider@example.com")

        def auth(token: str) -> dict[str, str]:
            return {"Authorization": f"Bearer {token}"}

        workspace = client.post(
            "/api/v1/workspaces",
            headers=auth(owner),
            json={"name": "Phase 3 Workspace"},
        )
        assert workspace.status_code == 201
        workspace_id = workspace.json()["data"]["id"]

        added_member = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=auth(owner),
            json={"email": "member@example.com", "role": "MEMBER"},
        )
        assert added_member.status_code == 201
        member_user_id = added_member.json()["data"]["user_id"]

        created = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=auth(owner),
            json={"name": "Product", "key": "PD", "is_private": True},
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]

        default_columns = client.get(
            f"/api/v1/projects/{project_id}/columns",
            headers=auth(owner),
        )
        assert default_columns.status_code == 200
        names = [column["name"] for column in default_columns.json()["data"]]
        assert names == ["backlog", "todo", "doing", "review", "done"]
        column_ids = [column["id"] for column in default_columns.json()["data"]]

        hidden = client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth(member),
        )
        assert hidden.status_code == 404

        added = client.post(
            f"/api/v1/projects/{project_id}/members",
            headers=auth(owner),
            json={"user_id": member_user_id, "role": "member"},
        )
        assert added.status_code == 201
        assert added.json()["data"]["role"] == "member"

        visible = client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth(member),
        )
        assert visible.status_code == 200

        reordered = client.put(
            f"/api/v1/projects/{project_id}/columns/reorder",
            headers=auth(owner),
            json={"column_ids": column_ids[::-1]},
        )
        assert reordered.status_code == 200
        assert [column["position"] for column in reordered.json()["data"]] == [0, 1, 2, 3, 4]

        archived = client.post(
            f"/api/v1/projects/{project_id}/archive",
            headers=auth(owner),
        )
        assert archived.status_code == 200
        assert archived.json()["data"]["archived_at"] is not None

        hidden_after_archive = client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth(outsider),
        )
        assert hidden_after_archive.status_code == 404

        restored = client.post(
            f"/api/v1/projects/{project_id}/restore",
            headers=auth(owner),
        )
        assert restored.status_code == 200
        assert restored.json()["data"]["archived_at"] is None
