from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database

TEST_SECRET = "test-only-project-api-secret-" + ("x" * 48)


def _client(tmp_path: Path) -> TestClient:
    database_url = migrate_database(tmp_path / "project-api.db")
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url=database_url,
                secret_key=TEST_SECRET,
                register_rate_limit_requests=20,
                login_rate_limit_requests=20,
            )
        )
    )


def _register(client: TestClient, email: str, name: str) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "a-secure-password"},
    )
    assert response.status_code == 201


def _token(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "a-secure-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _workspace(client: TestClient, token: str, name: str = "Team") -> str:
    response = client.post("/api/v1/workspaces", headers=_headers(token), json={"name": name})
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_project_http_flow_with_permissions_and_private_access(
    tmp_path: Path,
) -> None:
    with _client(tmp_path) as client:
        for email, name in (
            ("owner@example.com", "Owner"),
            ("member@example.com", "Member"),
            ("outsider@example.com", "Outsider"),
        ):
            _register(client, email, name)
        owner_token = _token(client, "owner@example.com")
        member_token = _token(client, "member@example.com")
        outsider_token = _token(client, "outsider@example.com")

        workspace_id = _workspace(client, owner_token)
        _ = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=_headers(owner_token),
            json={"email": "member@example.com", "role": "MEMBER"},
        )

        assert (
            client.post(
                f"/api/v1/workspaces/{workspace_id}/projects",
                json={"name": "No auth"},
            ).status_code
            == 401
        )

        invalid = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(owner_token),
            json={"name": "   ", "key": "  "},
        )
        assert invalid.status_code == 422

        created = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(owner_token),
            json={"name": "تیم محصول", "key": "PM"},
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]
        assert created.json()["data"]["is_private"] is False
        assert "password" not in created.text and "token_hash" not in created.text

        forbidden = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(member_token),
            json={"name": "Blocked", "key": "BL"},
        )
        assert forbidden.status_code == 403

        duplicate = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(owner_token),
            json={"name": "Duplicate", "key": "PM"},
        )
        assert duplicate.status_code == 409

        hidden = client.get(
            f"/api/v1/projects/{project_id}",
            headers=_headers(outsider_token),
        )
        assert hidden.status_code == 404
        assert hidden.json()["error"]["code"] == "resource_not_found"

        listed = client.get(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(member_token),
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["data"][0]["id"] == project_id

        columns = client.get(
            f"/api/v1/projects/{project_id}/columns",
            headers=_headers(member_token),
        )
        assert columns.status_code == 200
        names = [column["name"] for column in columns.json()["data"]]
        assert names == ["backlog", "todo", "doing", "review", "done"]
        assert columns.json()["data"][-1]["is_done"] is True


def test_project_member_and_column_api_authorization(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        for email, name in (
            ("owner@example.com", "Owner"),
            ("member@example.com", "Member"),
        ):
            _register(client, email, name)
        owner_token = _token(client, "owner@example.com")
        member_token = _token(client, "member@example.com")

        workspace_id = _workspace(client, owner_token)
        member_row = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=_headers(owner_token),
            json={"email": "member@example.com", "role": "MEMBER"},
        )
        assert member_row.status_code == 201
        member_user_id = member_row.json()["data"]["user_id"]

        created = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(owner_token),
            json={"name": "Team", "key": "TM", "is_private": True},
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]

        hidden_read = client.get(
            f"/api/v1/projects/{project_id}",
            headers=_headers(member_token),
        )
        assert hidden_read.status_code == 404

        added = client.post(
            f"/api/v1/projects/{project_id}/members",
            headers=_headers(owner_token),
            json={"user_id": member_user_id, "role": "member"},
        )
        assert added.status_code == 201
        added_id = added.json()["data"]["id"]
        assert added.json()["data"]["role"] == "member"
        assert added.json()["data"]["user"]["email"] == "member@example.com"
        listed_members = client.get(
            f"/api/v1/projects/{project_id}/members",
            headers=_headers(owner_token),
        )
        assert listed_members.status_code == 200
        listed_member = next(
            item for item in listed_members.json()["data"] if item["id"] == added_id
        )
        assert listed_member["user"]["name"] == "Member"

        now_visible = client.get(
            f"/api/v1/projects/{project_id}",
            headers=_headers(member_token),
        )
        assert now_visible.status_code == 200

        forbidden_member_add = client.post(
            f"/api/v1/projects/{project_id}/members",
            headers=_headers(member_token),
            json={"user_id": member_user_id, "role": "member"},
        )
        assert forbidden_member_add.status_code == 403

        duplicate = client.post(
            f"/api/v1/projects/{project_id}/members",
            headers=_headers(owner_token),
            json={"user_id": member_user_id, "role": "member"},
        )
        assert duplicate.status_code == 409

        promoted = client.patch(
            f"/api/v1/projects/{project_id}/members/{added_id}",
            headers=_headers(owner_token),
            json={"role": "manager"},
        )
        assert promoted.status_code == 200
        assert promoted.json()["data"]["role"] == "manager"

        removed = client.delete(
            f"/api/v1/projects/{project_id}/members/{added_id}",
            headers=_headers(owner_token),
        )
        assert removed.status_code == 204


def test_project_column_reorder_api_validation(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _register(client, "owner@example.com", "Owner")
        owner_token = _token(client, "owner@example.com")
        workspace_id = _workspace(client, owner_token)
        created = client.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=_headers(owner_token),
            json={"name": "Team", "key": "TM"},
        )
        assert created.status_code == 201
        project_id = created.json()["data"]["id"]

        columns = client.get(
            f"/api/v1/projects/{project_id}/columns",
            headers=_headers(owner_token),
        ).json()["data"]
        column_ids = [column["id"] for column in columns]

        added = client.post(
            f"/api/v1/projects/{project_id}/columns",
            headers=_headers(owner_token),
            json={"name": "In Progress"},
        )
        assert added.status_code == 201
        assert added.json()["data"]["position"] == 5

        updated_columns = client.get(
            f"/api/v1/projects/{project_id}/columns",
            headers=_headers(owner_token),
        ).json()["data"]
        column_ids = [column["id"] for column in updated_columns]

        invalid_reorder = client.put(
            f"/api/v1/projects/{project_id}/columns/reorder",
            headers=_headers(owner_token),
            json={"column_ids": column_ids[:-1]},
        )
        assert invalid_reorder.status_code == 409

        reordered = client.put(
            f"/api/v1/projects/{project_id}/columns/reorder",
            headers=_headers(owner_token),
            json={"column_ids": column_ids[1:] + column_ids[:1]},
        )
        assert reordered.status_code == 200
        positions = [column["position"] for column in reordered.json()["data"]]
        assert positions == [0, 1, 2, 3, 4, 5]

        blank = client.post(
            f"/api/v1/projects/{project_id}/columns",
            headers=_headers(owner_token),
            json={"name": "   "},
        )
        assert blank.status_code == 422


def test_project_pagination_caps(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _register(client, "owner@example.com", "Owner")
        owner_token = _token(client, "owner@example.com")
        workspace_id = _workspace(client, owner_token)
        for index in range(3):
            created = client.post(
                f"/api/v1/workspaces/{workspace_id}/projects",
                headers=_headers(owner_token),
                json={"name": f"Project {index}", "key": f"P{index}"},
            )
            assert created.status_code == 201

        page = client.get(
            f"/api/v1/workspaces/{workspace_id}/projects?page=2&page_size=2",
            headers=_headers(owner_token),
        )
        assert page.status_code == 200
        assert page.json()["page"] == 2
        assert page.json()["page_size"] == 2
        assert page.json()["total"] == 3
        assert len(page.json()["data"]) == 1

        too_large = client.get(
            f"/api/v1/workspaces/{workspace_id}/projects?page_size=101",
            headers=_headers(owner_token),
        )
        assert too_large.status_code == 422
