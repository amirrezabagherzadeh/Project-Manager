from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.config import Settings
from app.main import create_app
from tests.helpers import migrate_database


def client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url=migrate_database(tmp_path / "tasks.db"),
                secret_key="task-test-secret-" + ("x" * 48),
                attachment_storage_path=tmp_path / "uploads",
            )
        )
    )


def register(client: TestClient, email: str) -> str:
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"name": email, "email": email, "password": "a-secure-password"},
        ).status_code
        == 201
    )
    response = client.post(
        "/api/v1/auth/token", data={"username": email, "password": "a-secure-password"}
    )
    return response.json()["access_token"]


def setup_project(client: TestClient, token: str) -> tuple[str, str, dict[str, str]]:
    headers = {"Authorization": f"Bearer {token}"}
    workspace_id = client.post("/api/v1/workspaces", headers=headers, json={"name": "W"}).json()[
        "data"
    ]["id"]
    project_id = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={"name": "P", "key": "P"},
    ).json()["data"]["id"]
    column_id = client.get(f"/api/v1/projects/{project_id}/columns", headers=headers).json()[
        "data"
    ][0]["id"]
    return project_id, column_id, headers


def test_task_lifecycle_queries_associations_and_permissions(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        owner_token = register(api, "owner@example.com")
        member_token = register(api, "member@example.com")
        outsider_token = register(api, "outsider@example.com")
        project_id, column_id, headers = setup_project(api, owner_token)

        no_auth = api.post(
            f"/api/v1/projects/{project_id}/tasks", json={"title": "T", "column_id": column_id}
        )
        assert no_auth.status_code == 401
        invalid = api.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=headers,
            json={"title": " ", "column_id": column_id},
        )
        assert invalid.status_code == 422
        created = api.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=headers,
            json={"title": "Alpha", "column_id": column_id, "priority": "high"},
        )
        assert created.status_code == 201
        task_id = created.json()["data"]["id"]
        columns = api.get(f"/api/v1/projects/{project_id}/columns", headers=headers).json()["data"]
        done_column_id = next(column["id"] for column in columns if column["is_done"])
        moved = api.post(
            f"/api/v1/tasks/{task_id}/move",
            headers=headers,
            json={"target_column_id": done_column_id, "target_index": 0, "version": 1},
        )
        assert moved.status_code == 200
        assert moved.json()["data"]["completed_at"] is not None
        assert moved.json()["data"]["version"] == 2
        assert (
            api.post(
                f"/api/v1/tasks/{task_id}/move",
                headers=headers,
                json={"target_column_id": column_id, "target_index": 0, "version": 1},
            ).status_code
            == 409
        )
        moved_back = api.post(
            f"/api/v1/tasks/{task_id}/move",
            headers=headers,
            json={"target_column_id": column_id, "target_index": 0, "version": 2},
        )
        assert moved_back.status_code == 200
        assert moved_back.json()["data"]["completed_at"] is None
        assert (
            api.get(
                f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {outsider_token}"}
            ).status_code
            == 404
        )
        queried = api.get(
            f"/api/v1/projects/{project_id}/tasks?search=Alpha&priority=high&sort=title",
            headers=headers,
        )
        assert queried.status_code == 200 and queried.json()["total"] == 1
        assert (
            api.get(f"/api/v1/projects/{project_id}/tasks?sort=unsafe", headers=headers).status_code
            == 422
        )

        subtask = api.post(
            f"/api/v1/tasks/{task_id}/subtasks",
            headers=headers,
            json={"title": "Child", "column_id": column_id},
        )
        assert subtask.status_code == 201 and subtask.json()["data"]["parent_id"] == task_id
        assert api.post(f"/api/v1/tasks/{task_id}/archive", headers=headers).status_code == 200
        assert api.get(f"/api/v1/projects/{project_id}/tasks", headers=headers).json()["total"] == 1
        archived_list = api.get(
            f"/api/v1/projects/{project_id}/tasks?include_archived=true",
            headers=headers,
        )
        assert archived_list.status_code == 200
        assert archived_list.json()["total"] == 2
        assert any(
            item["id"] == task_id and item["archived_at"] for item in archived_list.json()["data"]
        )
        assert api.post(f"/api/v1/tasks/{task_id}/restore", headers=headers).status_code == 200

        member_user_id = api.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {member_token}"}
        ).json()["data"]["id"]
        workspace_id = api.get(f"/api/v1/projects/{project_id}", headers=headers).json()["data"][
            "workspace_id"
        ]
        assert (
            api.post(
                f"/api/v1/workspaces/{workspace_id}/members",
                headers=headers,
                json={"email": "member@example.com", "role": "MEMBER"},
            ).status_code
            == 201
        )
        assert (
            api.post(
                f"/api/v1/projects/{project_id}/members",
                headers=headers,
                json={"user_id": member_user_id, "role": "member"},
            ).status_code
            == 201
        )
        label_id = api.post(
            f"/api/v1/projects/{project_id}/labels", headers=headers, json={"name": "Bug"}
        ).json()["data"]["id"]
        assert (
            api.post(
                f"/api/v1/tasks/{task_id}/assignees",
                headers=headers,
                json={"user_id": member_user_id},
            ).status_code
            == 204
        )
        member_headers = {"Authorization": f"Bearer {member_token}"}
        assert (
            api.get("/api/v1/notifications/unread-count", headers=member_headers).json()["data"]
            >= 1
        )
        assert (
            api.post(
                f"/api/v1/tasks/{task_id}/labels", headers=headers, json={"label_id": label_id}
            ).status_code
            == 204
        )
        statements: list[str] = []

        def count_statement(*args: object) -> None:
            statements.append(str(args[2]))

        engine = api.app.state.database.engine.sync_engine
        event.listen(engine, "before_cursor_execute", count_statement)
        try:
            detail = api.get(f"/api/v1/tasks/{task_id}", headers=headers)
        finally:
            event.remove(engine, "before_cursor_execute", count_statement)
        assert detail.status_code == 200
        # Authentication/project authorization uses five bounded queries; detail
        # loading adds four select-in queries irrespective of relation cardinality.
        assert len(statements) <= 9
        assert detail.json()["data"]["assignees"] == [{"user_id": member_user_id}]
        assert detail.json()["data"]["task_labels"][0]["label"]["id"] == label_id
        assert any(
            item["id"] == subtask.json()["data"]["id"] for item in detail.json()["data"]["subtasks"]
        )
        assert (
            api.post(
                f"/api/v1/tasks/{task_id}/labels", headers=headers, json={"label_id": label_id}
            ).status_code
            == 409
        )
        assert (
            api.patch(
                f"/api/v1/labels/{label_id}", headers=headers, json={"name": "Defect"}
            ).status_code
            == 200
        )
        assert api.delete(f"/api/v1/labels/{label_id}", headers=headers).status_code == 200


def test_task_collaboration_permissions_files_and_activity(tmp_path: Path) -> None:
    with client(tmp_path) as api:
        owner_token = register(api, "collab-owner@example.com")
        member_token = register(api, "collab-member@example.com")
        outsider_token = register(api, "collab-outsider@example.com")
        project_id, column_id, owner_headers = setup_project(api, owner_token)
        task_id = api.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=owner_headers,
            json={"title": "Collaborate", "column_id": column_id},
        ).json()["data"]["id"]
        workspace_id = api.get(f"/api/v1/projects/{project_id}", headers=owner_headers).json()[
            "data"
        ]["workspace_id"]
        member_id = api.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {member_token}"}
        ).json()["data"]["id"]
        assert (
            api.post(
                f"/api/v1/workspaces/{workspace_id}/members",
                headers=owner_headers,
                json={"email": "collab-member@example.com", "role": "MEMBER"},
            ).status_code
            == 201
        )
        assert (
            api.post(
                f"/api/v1/projects/{project_id}/members",
                headers=owner_headers,
                json={"user_id": member_id, "role": "member"},
            ).status_code
            == 201
        )
        member_headers = {"Authorization": f"Bearer {member_token}"}
        comment = api.post(
            f"/api/v1/tasks/{task_id}/comments",
            headers=member_headers,
            json={"body": "Hello @collab-owner@example.com"},
        )
        assert comment.status_code == 201
        assert any(
            item["type"] == "task.mention"
            for item in api.get("/api/v1/notifications", headers=owner_headers).json()["data"]
        )
        assert (
            api.patch(
                f"/api/v1/comments/{comment.json()['data']['id']}",
                headers=owner_headers,
                json={"body": "Manager edit"},
            ).status_code
            == 200
        )
        checklist = api.post(
            f"/api/v1/tasks/{task_id}/checklists", headers=owner_headers, json={"title": "Ship"}
        )
        assert checklist.status_code == 201
        item = api.post(
            f"/api/v1/checklists/{checklist.json()['data']['id']}/items",
            headers=owner_headers,
            json={"title": "Test"},
        )
        assert item.status_code == 201
        assert api.patch(
            f"/api/v1/checklist-items/{item.json()['data']['id']}",
            headers=owner_headers,
            json={"completed": True},
        ).json()["data"]["completed"]
        second_item = api.post(
            f"/api/v1/checklists/{checklist.json()['data']['id']}/items",
            headers=owner_headers,
            json={"title": "Review"},
        ).json()["data"]
        reordered = api.put(
            f"/api/v1/checklists/{checklist.json()['data']['id']}/items/reorder",
            headers=owner_headers,
            json={"item_ids": [second_item["id"], item.json()["data"]["id"]]},
        )
        assert reordered.status_code == 200 and reordered.json()[0]["id"] == second_item["id"]
        checklist_data = api.get(
            f"/api/v1/tasks/{task_id}/checklists", headers=member_headers
        ).json()["data"][0]
        assert checklist_data["completed_items"] == 1 and checklist_data["total_items"] == 2
        upload = api.post(
            f"/api/v1/tasks/{task_id}/attachments",
            headers=owner_headers,
            files={"file": ("note.txt", b"private note", "text/plain")},
        )
        assert upload.status_code == 201
        attachment_id = upload.json()["data"]["id"]
        assert (
            api.get(
                f"/api/v1/attachments/{attachment_id}/download",
                headers={"Authorization": f"Bearer {outsider_token}"},
            ).status_code
            == 404
        )
        downloaded = api.get(
            f"/api/v1/attachments/{attachment_id}/download", headers=member_headers
        )
        assert downloaded.status_code == 200 and downloaded.content == b"private note"
        assert api.get(f"/api/v1/tasks/{task_id}/activity", headers=owner_headers).json()["data"]
        assert (
            api.delete(f"/api/v1/attachments/{attachment_id}", headers=owner_headers).status_code
            == 204
        )
