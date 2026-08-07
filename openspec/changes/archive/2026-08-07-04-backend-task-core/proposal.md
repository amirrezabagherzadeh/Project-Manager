## Why

Phase 3 delivers projects and columns but users cannot yet create or manage the
work items that make a project board useful. Phase 4 delivers the non-move Task
core required by BE-FR-05 and UC-06, UC-07, and UC-12 while preserving the later
atomic board-move contract for Phase 5.

## What Changes

- Add persisted Tasks with same-project parent/subtask relationships, assignments,
  labels, archive/restore state, optimistic version fields, and query-driven
  indexes through an Alembic revision.
- Add project Task and Label endpoints plus Task detail, update, archive/restore,
  assignee, label, and subtask endpoints under `/api/v1`.
- Implement permission-scoped task services and repositories with bounded,
  allowlisted pagination, search, filters, and sorting.
- Define completion and overdue semantics without implementing board moves; Phase 5
  remains solely responsible for atomic position/column transitions.
- Regenerate the OpenAPI TypeScript contract and add migration, service, HTTP,
  permission, conflict, and query-loading tests.

## Capabilities

### New Capabilities

- `backend-task-core`: Task CRUD, relationships, task-query behavior, and
  resource-level authorization for BE-FR-05, UC-06, UC-07, and UC-12.

### Modified Capabilities

None.

## Impact

- Affected backend modules: task models, schemas, repositories, services, API
  routes, router registration, Alembic migrations, and unit/integration tests.
- New public REST operations appear under `/api/v1`; generated frontend API types
  change, but no frontend behavior is added.
- Depends on the archived Phase 3 Project/Board foundation. Risks include IDOR,
  N+1 list/detail loading, invalid cross-project relationships, and incorrect
  completion semantics; service authorization, constraints, eager loading, and
  negative tests control these risks. The migration downgrade removes only the
  Phase 4 tables and rollback stops before the Phase 5 move contract.
