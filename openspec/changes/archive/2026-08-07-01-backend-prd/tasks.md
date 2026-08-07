## 1. Phase 0 Preflight

- [x] 1.1 Verify `openspec/changes/phase-0-repository-foundation/tasks.md` has no
  unchecked task, including Compose task 4.2, and record successful Backend,
  Frontend, runtime, container, contract, and OpenSpec evidence
  (`backend-delivery-program`: Phase 0 completion gates backend implementation).
- [x] 1.2 Run the Phase 0 gate exactly—`cd backend && uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy app`, `uv run pytest`; `cd frontend
  && pnpm lint`, `pnpm test`, `pnpm build`, `pnpm e2e`, `pnpm generate:api`; then
  `openspec validate --all --strict`—synchronize its delta specs and archive
  `phase-0-repository-foundation` only after every result passes.

## 2. Phase 1 — Foundation, Database, and Authentication

- [x] 2.1 Create and strictly validate `01-backend-foundation-auth` with proposal,
  delta specs, design, and detailed tasks covering BE-FR-01 residual database work,
  BE-FR-02 authentication/session scope, and UC-01; do not edit runtime code until
  `openspec validate --all --strict` passes.
- [x] 2.2 Apply the validated Phase 1 tasks for async SQLAlchemy/session
  infrastructure, User/RefreshSession migrations, registration, OAuth2 login,
  access JWT, refresh-cookie rotation/replay revocation, logout, `/auth/me`, rate
  limiting, error/OpenAPI contracts, and positive/negative/edge-case tests; verify
  upgrade from an empty disposable database, authenticated HTTP flows, generated
  API types, README, and changelog.
- [x] 2.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 1 specs, verify the
  merge, archive the change, and record its evidence before Phase 2.

## 3. Phase 2 — Workspace and RBAC

- [x] 3.1 After Phase 1 archival, create and strictly validate
  `02-backend-workspace-rbac` for BE-FR-03, UC-02, and UC-03 with detailed model,
  migration, permission-matrix, transaction, endpoint, conflict, and test tasks.
- [x] 3.2 Apply Phase 2 for Workspace, WorkspaceMember, WorkspaceInvitation,
  atomic owner creation, membership/invitation flows, role changes, ownership
  safeguards, archive/restore/delete rules, Activity/Notification hooks, and
  success/`401`/`403`/`404`/`409`/rollback tests; regenerate the contract and update
  documentation/changelog.
- [x] 3.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 2 specs, verify the
  merge, archive the change, and record its evidence before Phase 3.

## 4. Phase 3 — Projects and Default Board

- [x] 4.1 After Phase 2 archival, create and strictly validate
  `03-backend-project-board-foundation` for BE-FR-04, UC-04, and UC-05 with detailed
  Project, ProjectMember, BoardColumn, private-access, migration, transaction,
  endpoint, permission, and test tasks.
- [x] 4.2 Apply Phase 3 for project CRUD/archive/restore, workspace-unique keys,
  project membership, private project access, atomic creator-manager plus five
  default columns, column CRUD/archive/reorder, and complete authorization/conflict/
  rollback tests; regenerate the contract and update documentation/changelog.
- [x] 4.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 3 specs, verify the
  merge, archive the change, and record its evidence before Phase 4.

## 5. Phase 4 — Task Core

- [x] 5.1 After Phase 3 archival, create and strictly validate
  `04-backend-task-core` for the non-move portions of BE-FR-05 and UC-06, UC-07,
  and UC-12 with detailed Task, TaskAssignee, Label, TaskLabel, subtask, migration,
  endpoint, query, permission, and test tasks.
- [x] 5.2 Apply Phase 4 for task create/detail/update/archive/restore, assignments,
  labels, same-project subtasks, pagination, search, filter and sort allowlists,
  overdue/completion semantics, eager-loading/N+1 controls, and success/validation/
  authorization/not-found/conflict tests; regenerate the contract and update
  documentation/changelog.
- [x] 5.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 4 specs, verify the
  merge, archive the change, and record its evidence before Phase 5.

## 6. Phase 5 — Atomic Board Move

- [x] 6.1 After Phase 4 archival, create and strictly validate
  `05-backend-board-move` for the BE-FR-05 move contract and UC-06 with detailed
  optimistic-version, position, transaction, completion, permission, activity,
  notification-suppression, conflict, and concurrency test tasks.
- [x] 6.2 Apply Phase 5 for atomic intra-column/inter-column move and reorder,
  `target_column_id`/`target_index`/`version` validation, source/target position
  normalization, Done/`completed_at` synchronization, version increment, final-task
  response, `409 version_conflict`, rollback, persistence-after-refresh, and query
  audit; regenerate the contract and update documentation/changelog.
- [x] 6.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 5 specs, verify the
  merge, archive the change, and record its evidence before Phase 6.

## 7. Phase 6 — Task Collaboration

- [x] 7.1 After Phase 5 archival, create and strictly validate
  `06-backend-collaboration` for BE-FR-06 and UC-07 with detailed Checklist,
  ChecklistItem, Comment, Attachment, ActivityLog, StorageService, migration,
  permission, transaction, endpoint, cleanup, and abuse-test tasks.
- [x] 7.2 Apply Phase 6 for checklist/item CRUD and reorder, progress, comment
  ownership/edit/delete, attachment multipart upload/download/delete through local
  storage, size/MIME/name/path safeguards, physical cleanup, activity timelines,
  and authorized/unauthorized/large/unsupported/path-traversal tests; regenerate the
  contract and update documentation/changelog.
- [x] 7.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 6 specs, verify the
  merge, archive the change, and record its evidence before Phase 7.

## 8. Phase 7 — Project Views and Reporting

- [x] 8.1 After Phase 6 archival, create and strictly validate
  `07-backend-project-views-reporting` for project-scoped BE-FR-08, UC-05, and
  UC-08 with detailed overview, dashboard, timeline, calendar, aggregate, timezone,
  permission, query-performance, endpoint, and fixture-test tasks.
- [x] 8.2 Apply Phase 7 for project overview/dashboard metrics, completion,
  overdue/due-soon/unassigned groups, column/priority/assignee aggregation, recent
  activity, timeline/calendar task data, UTC boundaries, zero-total behavior, scoped
  permissions, bounded queries, and fixture-accurate tests; regenerate the contract
  and update documentation/changelog.
- [x] 8.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 7 specs, verify the
  merge, archive the change, and record its evidence before Phase 8.

## 9. Phase 8 — Notifications, Profile, and Global Dashboard

- [x] 9.1 After Phase 7 archival, create and strictly validate
  `08-backend-notifications-profile-dashboard` for the profile remainder of
  BE-FR-02, BE-FR-07, global BE-FR-08, and UC-09 through UC-11 with detailed models,
  migrations, endpoints, permissions, deduplication, job, aggregate, avatar, storage,
  and test tasks.
- [x] 9.2 Apply Phase 8 for notification lists/count/read/read-all, membership/
  assignment/comment/mention/due events, self-suppression and logical-key dedupe,
  due notification generation, global metrics/activity, profile name/timezone,
  avatar upload/delete, logout compatibility, scoped queries, and fixture/permission/
  storage tests; regenerate the contract and update documentation/changelog.
- [x] 9.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 8 specs, verify the
  merge, archive the change, and record its evidence before Phase 9.

## 10. Phase 9 — Hardening, Seed, and Delivery

- [x] 10.1 After Phase 8 archival, create and strictly validate
  `09-backend-hardening-seed-delivery` for BE-FR-09 and the Backend PRD Definition
  of Done with detailed seed, migration-chain, security, permissions, performance,
  OpenAPI, container/storage, documentation, and end-to-end audit tasks.
- [x] 10.2 Apply Phase 9 for an idempotent development-only demo seed, complete
  migration upgrade/downgrade verification, permission/IDOR and sensitive-data
  audit, N+1/query audit, rate-limit/storage/notification hardening, container
  persistence, startup-from-zero documentation, and the complete Backend PRD HTTP
  acceptance flow with no permanent mock, stub, placeholder, or critical/high defect.
- [x] 10.3 Run `cd backend && uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`, `uv run pytest`; run `cd frontend && pnpm generate:api`; run
  `openspec validate --all --strict`; then synchronize Phase 9 specs, verify the
  merge, archive the change, and record its evidence.

## 11. Backend Program Completion

- [x] 11.1 Audit BE-FR-01 through BE-FR-09 and UC-01 through UC-12 against archived
  phase specs, checked tasks, migrations, endpoint tests, Swagger operations, and
  completion records; leave this task unchecked for any coverage gap.
- [x] 11.2 From an empty disposable database run the complete Alembic chain, start a
  fresh application, verify `/health`, `/docs`, `/redoc`, `/api/v1/openapi.json`,
  exercise the critical Register → Workspace → Project → Task → Move → Collaboration
  → Dashboard → forbidden action → Logout flow, and verify seed idempotency.
- [x] 11.3 Run the final gates exactly: `cd backend && uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy app`, `uv run pytest`; run
  `cd frontend && pnpm generate:api`; run `openspec validate --all --strict`;
  confirm no unexplained OpenAPI drift or known critical/high defect remains.
- [x] 11.4 Update `README.md` and `CHANGELOG.md` with delivered backend behavior,
  migrations, commands, test evidence, security/production limitations, and rollback
  notes; synchronize `backend-delivery-program`, verify the main spec, and archive
  `01-backend-prd`.
