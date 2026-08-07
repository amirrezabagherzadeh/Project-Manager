from app.core.config import Settings
from app.main import create_app


def test_project_openapi_has_security_metadata_pagination_and_no_hashes() -> None:
    schema = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            secret_key="project-openapi-secret-" + ("x" * 48),
        )
    ).openapi()
    paths = schema["paths"]
    required_paths = {
        "/api/v1/workspaces/{workspace_id}/projects",
        "/api/v1/projects/{project_id}",
        "/api/v1/projects/{project_id}/archive",
        "/api/v1/projects/{project_id}/restore",
        "/api/v1/projects/{project_id}/members",
        "/api/v1/projects/{project_id}/members/{member_id}",
        "/api/v1/projects/{project_id}/columns",
        "/api/v1/projects/{project_id}/columns/{column_id}",
        "/api/v1/projects/{project_id}/columns/{column_id}/archive",
        "/api/v1/projects/{project_id}/columns/reorder",
    }
    assert required_paths.issubset(paths)

    for path in required_paths:
        for operation in paths[path].values():
            assert operation["summary"]
            assert operation["description"]
            assert operation["tags"] == ["projects"]
            assert operation["security"] == [{"OAuth2Password": []}]

    list_parameters = paths["/api/v1/workspaces/{workspace_id}/projects"]["get"]["parameters"]
    page_size = next(item for item in list_parameters if item["name"] == "page_size")
    assert page_size["schema"]["default"] == 20
    assert page_size["schema"]["maximum"] == 100

    column_list_parameters = paths["/api/v1/projects/{project_id}/columns"]["get"]["parameters"]
    column_page_size = next(item for item in column_list_parameters if item["name"] == "page_size")
    assert column_page_size["schema"]["default"] == 20
    assert column_page_size["schema"]["maximum"] == 100

    serialized = str(schema).lower()
    assert "token_hash" not in serialized
    assert "password_hash" not in serialized
    assert "refresh_token" not in serialized


def test_project_openapi_examples_are_present() -> None:
    schema = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            secret_key="project-openapi-examples-secret-" + ("x" * 48),
        )
    ).openapi()
    components = schema["components"]["schemas"]
    for name in ("ProjectCreate", "ColumnCreate", "ColumnReorder"):
        schema_definition = components.get(name)
        assert schema_definition is not None, f"missing schema {name}"
        for field_name, field_schema in schema_definition["properties"].items():
            if name == "ProjectCreate" and field_name in {"name", "key"}:
                assert field_schema.get("examples"), f"missing example on {name}.{field_name}"
