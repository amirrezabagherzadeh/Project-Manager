from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.models.base import utc_now
from tests.helpers import migrate_database


def client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url=migrate_database(tmp_path / "reporting.db"),
                secret_key="reporting-test-secret-" + ("x" * 48),
            )
        )
    )


def token(api: TestClient, email: str) -> str:
    api.post(
        "/api/v1/auth/register",
        json={"name": email, "email": email, "password": "a-secure-password"},
    )
    return api.post(
        "/api/v1/auth/token", data={"username": email, "password": "a-secure-password"}
    ).json()["access_token"]


def test_project_reporting_metrics_ranges_and_access(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        owner_headers = {"Authorization": f"Bearer {token(api, 'reporter@example.com')}"}
        outsider_headers = {"Authorization": f"Bearer {token(api, 'other-reporter@example.com')}"}
        workspace_id = api.post(
            "/api/v1/workspaces", headers=owner_headers, json={"name": "W"}
        ).json()["data"]["id"]
        project_id = api.post(
            f"/api/v1/workspaces/{workspace_id}/projects",
            headers=owner_headers,
            json={"name": "P", "key": "REP"},
        ).json()["data"]["id"]
        column_id = api.get(f"/api/v1/projects/{project_id}/columns", headers=owner_headers).json()[
            "data"
        ][0]["id"]
        empty = api.get(f"/api/v1/projects/{project_id}/dashboard", headers=owner_headers)
        assert empty.status_code == 200 and empty.json()["data"]["total"] == 0
        now = utc_now()
        assert (
            api.post(
                f"/api/v1/projects/{project_id}/tasks",
                headers=owner_headers,
                json={
                    "title": "Soon",
                    "column_id": column_id,
                    "due_at": (now + timedelta(days=1)).isoformat(),
                },
            ).status_code
            == 201
        )
        assert (
            api.post(
                f"/api/v1/projects/{project_id}/tasks",
                headers=owner_headers,
                json={
                    "title": "Late",
                    "column_id": column_id,
                    "due_at": (now - timedelta(days=1)).isoformat(),
                },
            ).status_code
            == 201
        )
        dashboard = api.get(f"/api/v1/projects/{project_id}/dashboard", headers=owner_headers)
        assert dashboard.json()["data"] == {
            "total": 2,
            "completed": 0,
            "overdue": 1,
            "due_soon": 1,
            "unassigned": 2,
            "by_priority": {"medium": 2},
            "by_column": {column_id: 2},
            "by_assignee": {},
        }
        timeline = api.get(
            f"/api/v1/projects/{project_id}/timeline",
            headers=owner_headers,
            params={
                "start": (now - timedelta(days=2)).isoformat(),
                "end": (now + timedelta(days=2)).isoformat(),
            },
        )
        assert timeline.status_code == 200 and timeline.json()["total"] == 2
        assert (
            api.get(
                f"/api/v1/projects/{project_id}/dashboard", headers=outsider_headers
            ).status_code
            == 404
        )
