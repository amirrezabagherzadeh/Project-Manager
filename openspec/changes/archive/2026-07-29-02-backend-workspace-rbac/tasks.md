## 1. Models and Migration

- [x] 1.1 Implement Workspace, WorkspaceMember, WorkspaceInvitation, ActivityLog,
  and Notification models plus role enums, named constraints, indexes, private-token
  fields, and relationships; verify metadata with `cd backend && uv run pytest
  tests/unit/test_workspace_models.py`.
- [x] 1.2 Add reversible Alembic revision `20260729_0002`; verify empty upgrade,
  expected constraints/FKs/indexes, downgrade to Phase 1, and re-upgrade with
  `cd backend && uv run pytest tests/integration/test_workspace_migrations.py`.

## 2. Repositories and Permissions

- [x] 2.1 Implement bounded Workspace/member/invitation repositories with scoped
  eager loading, pagination, normalized lookups, and no commits; verify query and
  rollback behavior with `cd backend && uv run pytest
  tests/integration/test_workspace_repositories.py`.
- [x] 2.2 Implement shared role predicates and resource-scoped membership resolution
  for OWNER/ADMIN/PROJECT_MANAGER/MEMBER, including non-member safe `404`; verify
  the complete matrix with `cd backend && uv run pytest
  tests/unit/test_workspace_permissions.py`.

## 3. Workspace Services

- [x] 3.1 Implement atomic create/list/read/update/archive/restore/delete with exact
  owner membership and creation/activity invariants; test success, validation,
  `401` integration boundary, `403`, safe `404`, owner-only delete, and rollback
  using `cd backend && uv run pytest tests/integration/test_workspace_service.py -k
  "workspace and not member and not invitation"`.
- [x] 3.2 Implement direct member add/list/role change/removal and atomic ownership
  transfer with duplicate, unknown-user, owner/admin/member safeguards, durable
  activity, and self-suppressed notifications; verify with `cd backend && uv run
  pytest tests/integration/test_workspace_service.py -k "member or ownership"`.
- [x] 3.3 Implement hashed invitation create/list/revoke/accept with normalized email,
  expiry, reuse/conflict rules, matching-user enforcement, atomic membership and
  side effects; verify success, expired/revoked/accepted/mismatch, `409`, rollback,
  and hash privacy using `cd backend && uv run pytest
  tests/integration/test_workspace_service.py -k invitation`.

## 4. HTTP and OpenAPI

- [x] 4.1 Add Workspace authorization dependencies, public schemas/envelopes, and
  versioned Workspace/member/invitation routes with pagination caps and complete
  metadata; verify positive and `401`/`403`/safe-`404`/`409`/`422` HTTP flows with
  `cd backend && uv run pytest tests/integration/test_workspace_api.py`.
- [x] 4.2 Audit activity/notification atomicity and sensitive-field redaction across
  public responses/logs, including injected side-effect failure rollback, with
  `cd backend && uv run pytest tests/integration/test_workspace_side_effects.py`.
- [x] 4.3 Audit Swagger/ReDoc/OpenAPI operations, security, examples, pagination, and
  absence of hashes; verify with `cd backend && uv run pytest
  tests/integration/test_workspace_openapi.py`.

## 5. Runtime, Contract, and Documentation

- [x] 5.1 Exercise a disposable real HTTP Owner → Workspace → member → role →
  invitation → accept → forbidden Member action → ownership transfer → archive/
  restore flow, and verify migration/startup/docs with `cd backend && uv run pytest
  tests/integration/test_workspace_http_flow.py` plus the runtime smoke command.
- [x] 5.2 Regenerate `frontend/src/lib/api/schema.d.ts` from the running migrated API;
  inspect no private hash fields or unexplained drift.
- [x] 5.3 Update README and CHANGELOG with Phase 2 endpoints, roles, migrations,
  Swagger/Postman flow, tests, rollback, and limitations.

## 6. Phase 2 Quality Gate

- [x] 6.1 Run exactly `cd backend && uv run ruff check .`, `uv run ruff format
  --check .`, `uv run mypy app`, and `uv run pytest`; all must pass.
- [x] 6.2 Run `cd frontend && pnpm generate:api`, then `openspec validate --all
  --strict`; verify all requirements, sync the delta spec, and archive only after
  all evidence is green.
