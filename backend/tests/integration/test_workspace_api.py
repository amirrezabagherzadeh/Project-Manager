from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database

TEST_SECRET = "test-only-workspace-api-secret-" + ("x" * 48)


def _client(tmp_path: Path) -> TestClient:
    database_url = migrate_database(tmp_path / "workspace-api.db")
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


def test_workspace_member_invitation_and_ownership_http_flow(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        for email, name in (
            ("owner@example.com", "Owner"),
            ("admin@example.com", "Admin"),
            ("member@example.com", "Member"),
            ("invited@example.com", "Invited"),
            ("outsider@example.com", "Outsider"),
        ):
            _register(client, email, name)
        owner_token = _token(client, "owner@example.com")
        admin_token = _token(client, "admin@example.com")
        member_token = _token(client, "member@example.com")
        invited_token = _token(client, "invited@example.com")
        outsider_token = _token(client, "outsider@example.com")

        assert client.post("/api/v1/workspaces", json={"name": "No auth"}).status_code == 401
        invalid = client.post(
            "/api/v1/workspaces",
            headers=_headers(owner_token),
            json={"name": "   "},
        )
        assert invalid.status_code == 422

        created = client.post(
            "/api/v1/workspaces",
            headers=_headers(owner_token),
            json={"name": "تیم محصول", "description": "برنامه محصول"},
        )
        assert created.status_code == 201
        workspace_id = created.json()["data"]["id"]
        assert "password" not in created.text and "token_hash" not in created.text

        hidden = client.get(
            f"/api/v1/workspaces/{workspace_id}",
            headers=_headers(outsider_token),
        )
        assert hidden.status_code == 404
        assert hidden.json()["error"]["code"] == "resource_not_found"

        admin_member = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=_headers(owner_token),
            json={"email": "admin@example.com", "role": "ADMIN"},
        )
        assert admin_member.status_code == 201
        assert admin_member.json()["data"]["user"] == {
            "id": admin_member.json()["data"]["user_id"],
            "email": "admin@example.com",
            "name": "Admin",
            "avatar_content_type": None,
        }
        member = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=_headers(admin_token),
            json={"email": "member@example.com", "role": "MEMBER"},
        )
        assert member.status_code == 201

        duplicate = client.post(
            f"/api/v1/workspaces/{workspace_id}/members",
            headers=_headers(owner_token),
            json={"email": "member@example.com", "role": "MEMBER"},
        )
        assert duplicate.status_code == 409

        forbidden = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            headers=_headers(member_token),
            json={"name": "Forbidden"},
        )
        assert forbidden.status_code == 403

        invitation = client.post(
            f"/api/v1/workspaces/{workspace_id}/invitations",
            headers=_headers(admin_token),
            json={"email": "INVITED@example.com", "role": "PROJECT_MANAGER"},
        )
        assert invitation.status_code == 201
        raw_token = invitation.json()["data"]["token"]
        assert raw_token and "token_hash" not in invitation.text

        accepted = client.post(
            f"/api/v1/invitations/{raw_token}/accept",
            headers=_headers(invited_token),
        )
        assert accepted.status_code == 200
        assert accepted.json()["data"]["role"] == "PROJECT_MANAGER"

        transfer = client.patch(
            f"/api/v1/workspaces/{workspace_id}/members/{member.json()['data']['id']}",
            headers=_headers(owner_token),
            json={"role": "OWNER"},
        )
        assert transfer.status_code == 200
        assert transfer.json()["data"]["role"] == "OWNER"

        old_owner_delete = client.delete(
            f"/api/v1/workspaces/{workspace_id}",
            headers=_headers(owner_token),
        )
        assert old_owner_delete.status_code == 403


def test_workspace_pagination_and_validation_caps(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        _register(client, "owner@example.com", "Owner")
        token = _token(client, "owner@example.com")
        workspace_ids = []
        for index in range(3):
            response = client.post(
                "/api/v1/workspaces",
                headers=_headers(token),
                json={"name": f"Workspace {index}"},
            )
            assert response.status_code == 201
            workspace_ids.append(response.json()["data"]["id"])

        assert (
            client.post(
                f"/api/v1/workspaces/{workspace_ids[0]}/archive", headers=_headers(token)
            ).status_code
            == 200
        )

        page = client.get(
            "/api/v1/workspaces?page=2&page_size=2",
            headers=_headers(token),
        )
        assert page.status_code == 200
        assert page.json()["page"] == 2
        assert page.json()["page_size"] == 2
        assert page.json()["total"] == 2
        assert len(page.json()["data"]) == 0

        including_archived = client.get(
            "/api/v1/workspaces?include_archived=true&page_size=10",
            headers=_headers(token),
        )
        assert including_archived.status_code == 200
        assert including_archived.json()["total"] == 3
        assert any(item["archived_at"] for item in including_archived.json()["data"])

        too_large = client.get(
            "/api/v1/workspaces?page_size=101",
            headers=_headers(token),
        )
        assert too_large.status_code == 422
