from app.core.config import Settings
from app.main import create_app


def test_workspace_openapi_has_security_metadata_pagination_and_no_hashes() -> None:
    schema = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            secret_key="workspace-openapi-secret-" + ("x" * 48),
        )
    ).openapi()
    paths = schema["paths"]
    required_paths = {
        "/api/v1/workspaces",
        "/api/v1/workspaces/{workspace_id}",
        "/api/v1/workspaces/{workspace_id}/archive",
        "/api/v1/workspaces/{workspace_id}/restore",
        "/api/v1/workspaces/{workspace_id}/members",
        "/api/v1/workspaces/{workspace_id}/members/{member_id}",
        "/api/v1/workspaces/{workspace_id}/invitations",
        "/api/v1/workspaces/{workspace_id}/invitations/{invitation_id}/revoke",
        "/api/v1/invitations/{token}/accept",
    }
    assert required_paths.issubset(paths)

    for path in required_paths:
        for operation in paths[path].values():
            assert operation["summary"]
            assert operation["description"]
            assert operation["tags"] == ["workspaces"]
            assert operation["security"] == [{"OAuth2Password": []}]

    list_parameters = paths["/api/v1/workspaces"]["get"]["parameters"]
    page_size = next(item for item in list_parameters if item["name"] == "page_size")
    assert page_size["schema"]["default"] == 20
    assert page_size["schema"]["maximum"] == 100

    serialized = str(schema).lower()
    assert "token_hash" not in serialized
    assert "password_hash" not in serialized
    assert "refresh_token" not in serialized
