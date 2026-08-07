## 1. Data model and migration

- [x] 1.1 Add Task, TaskAssignee, Label, and TaskLabel models with UUID/FK/unique/check/index constraints and relationships in `backend/app/models`; verify focused model tests. (BE-FR-05, UC-06/07/12)
- [x] 1.2 Create an Alembic revision after `20260729_0003` with upgrade/downgrade for Phase 4 tables and indexes; verify empty-database upgrade plus downgrade/re-upgrade. (BE-FR-05)

## 2. Task domain behavior

- [x] 2.1 Add public request/response schemas, filter/sort allowlists, validation, and no-sensitive-field serialization in `backend/app/schemas`; verify schema unit tests. (BE-FR-05, UC-12)
- [x] 2.2 Implement Task and Label repositories with targeted eager loading, bounded pagination, safe filter/sort mapping, counts, and no commits; verify query and N+1-focused tests. (BE-FR-05, UC-12)
- [x] 2.3 Implement service-owned resource authorization and transactions for task CRUD/archive/restore, same-project subtasks, assignees, labels, overdue/completion semantics, and conflict rollback; verify success, 401/403/404/409, and rollback tests. (BE-FR-05, UC-06/07)

## 3. HTTP contract

- [x] 3.1 Add documented `/api/v1` Task/Label routes and router registration with standard envelopes, examples, statuses, and errors; verify OpenAPI and real authenticated HTTP flows. (BE-FR-05)
- [x] 3.2 Add integration coverage for create/detail/update/archive/restore, assignment/labels/subtasks, pagination/search/filter/sort, private-project access, and cross-project/IDOR rejection. (UC-06/07/12)

## 4. Contract and phase verification

- [x] 4.1 Regenerate `frontend/src/lib/api/schema.d.ts`, update README/CHANGELOG with Phase 4 behavior, migration, commands, and known limitation that move is Phase 5. (BE-FR-05)
- [x] 4.2 Run `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest`; run `cd frontend && pnpm generate:api`; run `npx --yes @fission-ai/openspec@1.7.0 validate --all --strict`; record successful evidence before sync/archive. (Phase 4 gate)
