## 1. Models and Migration

- [x] 1.1 Implement Project, ProjectMember, and BoardColumn models plus role enums, the
  `project(workspace_id,key)` unique constraint, `project_member(project_id,user_id)`
  unique constraint, named indexes, `is_private`, `is_done`, `position`, `archived_at`,
  and relationships; verify metadata with `cd backend && uv run pytest
  tests/unit/test_project_models.py`.
- [x] 1.2 Add reversible Alembic revision `20260729_0003` creating project/member/column
  tables; verify empty migration, expected constraints/FKs/indexes, downgrade to Phase 2,
  and re-upgrade with `cd backend && uv run pytest
  tests/integration/test_project_migrations.py`.

## 2. Repositories and Permissions

- [x] 2.1 Implement bounded Project/member/column repositories with scoped eager loading,
  pagination, workspace-unique key lookup, active/archived filters, and no commits; verify
  query and rollback behavior with `cd backend && uv run pytest
  tests/integration/test_project_repositories.py`.
- [x] 2.2 Implement shared project permission predicates: workspace-role gate for create,
  project membership/private-access resolution for read/mutate, `manager`/workspace
  ADMIN/OWNER gate for mutations, non-member safe `404`; verify the complete matrix with
  `cd backend && uv run pytest tests/unit/test_project_permissions.py`.


## 3. Project, Member, and Column Services

- [x] 3.1 Implement atomic create/list/read/update/archive/restore with creator-manager
  membership, five default columns, workspace-unique key, and creation activity; test
  success, validation, `401` integration boundary, `403`, safe `404`, `409` duplicate key,
  private-project access, and rollback using `cd backend && uv run pytest
  tests/integration/test_project_service.py -k "project and not member and not column"`.
- [x] 3.2 Implement project member add/list/role-change/remove with existing-workspace-
  member enforcement, duplicate/unknown `404`/`409`, durable activity, and self-suppressed
  notifications; verify with `cd backend && uv run pytest
  tests/integration/test_project_service.py -k member`.
- [x] 3.3 Implement column create/list/update/archive/reorder with full-list atomic
  position rewrite, reject-unchanged-on-invalid, default-column seed preservation, and
  activity; verify success, reorder validation, archive exclusion, and rollback with `cd
  backend && uv run pytest tests/integration/test_project_service.py -k column`.

## 4. HTTP and OpenAPI

- [x] 4.1 Add project authorization dependencies, public schemas/envelopes, and versioned
  project/member/column routes with pagination caps and complete metadata; verify positive
  and `401`/`403`/safe-`404`/`409`/`422` HTTP flows with `cd backend && uv run pytest
  tests/integration/test_project_api.py`.
- [x] 4.2 Audit activity/notification atomicity and sensitive-field redaction across
  public responses/logs, including injected side-effect failure rollback, with `cd backend
  && uv run pytest tests/integration/test_project_side_effects.py`.
- [x] 4.3 Audit Swagger/ReDoc/OpenAPI operations, security, examples, pagination, and
  absence of hashes; verify with `cd backend && uv run pytest
  tests/integration/test_project_openapi.py`.

## 5. Runtime, Contract, and Documentation

- [x] 5.1 Exercise a disposable real HTTP OWNER → Workspace → Project → default columns →
  member add → private Project `404` → column reorder → archive/restore flow, and verify
  migration/startup/docs with `cd backend && uv run pytest
  tests/integration/test_project_http_flow.py` plus the runtime smoke command.
- [x] 5.2 Regenerate `frontend/src/lib/api/schema.d.ts` from the running migrated API;
  inspect no private hash fields or unexplained drift.
- [x] 5.3 Update README and CHANGELOG with Phase 3 endpoints, permissions, migrations,
  Swagger/Postman flow, tests, rollback, and limitations.

## 6. Phase 3 Quality Gate

- [x] 6.1 Run exactly `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, and `uv run pytest`; all must pass.
- [x] 6.2 Run `cd frontend && pnpm generate:api`, then `openspec validate --all --strict`;
  verify all requirements, sync the delta spec, and archive only after all evidence is
  green.
