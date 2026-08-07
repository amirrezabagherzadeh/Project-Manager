## Why

Workspace members still cannot partition work into Projects, and the board has no
columns for Tasks to live on. Phase 3 delivers Backend PRD 1.1 BE-FR-04 and UC-04/UC-05
so later Task phases can rely on atomic Project creation, workspace-unique keys,
project membership, private-project access, and five default board columns.

## What Changes

- Add Project, ProjectMember, and BoardColumn models and a reversible Alembic revision
  with UUID/UTC constraints, the `project(workspace_id,key)` unique constraint, and
  query-driven indexes.
- Add Project CRUD/list/archive/restore, project membership management, and board column
  CRUD/archive/reorder under `/api/v1`.
- Enforce workspace-role authorization for Project mutations and project membership, plus
  private-project access checks that hide non-member Projects from workspace Members.
- Create Project, the creator as `manager`, and five default columns
  (`backlog`, `todo`, `doing`, `review`, `done`) in one transaction; only the `done`
  column is `is_done=true`.
- Record Project/member/column activity transactionally and create self-suppressed
  membership notifications through the durable engagement records established in Phase 2.
- Add full success, validation, `401`, `403`/safe `404`, `409`, rollback, migration,
  OpenAPI, and generated-client tests.

Goals:

- Satisfy BE-FR-04 and backend acceptance for UC-04 and UC-05.
- Create Project plus exactly one `manager` ProjectMember and five default columns
  atomically.
- Make project mutations, membership, column reorder, activity, and notification side
  effects atomic and backend-authorized.
- Enforce private-project access so a workspace Member without project membership cannot
  read or mutate the Project.

Non-goals:

- Task models, assignment, labels, or board move behavior, which belong to Phases 4 and 5.
- Project overview/dashboard/timeline/calendar aggregate data, which belong to Phase 7;
  Phase 3 exposes only the Project, member, and column resources that UC-05 lists.
- Email delivery, guest accounts, SSO, or frontend Project UI.

Dependencies:

- Archived Phase 2 workspace/RBAC and engagement capabilities.

Risks and rollback:

- Permission drift and IDOR are controlled by one permission matrix, service rechecks,
  private-project access tests, and negative tests.
- Column ordering corruption is controlled by explicit positions, a bounded reorder
  contract, and atomic normalization tests.
- Rollback removes Phase 3 routes/modules and downgrades only an explicitly approved
  database; Project, membership, column, and engagement data are lost on downgrade.

## Capabilities

### New Capabilities

- `backend-project-board-foundation`: Project lifecycle, project membership, default board
  columns, column CRUD/archive/reorder, private-project access, activity/notification side
  effects, and resource-level authorization (Backend PRD 1.1 BE-FR-04; UC-04 and UC-05).

### Modified Capabilities

None.

## Impact

- Backend Project/board models, schemas, repositories, services, dependencies, versioned
  endpoints, migrations, and tests.
- Public `/api/v1/workspaces/{workspace_id}/projects`, `/api/v1/projects/{project_id}`,
  project member and column operations.
- Generated `frontend/src/lib/api/schema.d.ts`, README, and changelog.
