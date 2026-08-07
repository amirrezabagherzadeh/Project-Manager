/goal Deliver the complete FastAPI backend program defined by the OpenSpec roadmap
`01-backend-prd`. Work through the numbered backend phases in order and do not claim
completion until every verifiable completion condition in this prompt and the active
OpenSpec artifacts is satisfied.

This is a long-running, phase-gated goal. Persist through all locally fixable test,
type, lint, migration, runtime, security, and contract failures. If a genuine
external or information blocker remains after safe in-scope investigation, stop at
that gate without claiming completion and report the exact blocker evidence.

## Authoritative sources

Read these files completely before modifying any code or OpenSpec artifact:

- `AGENTS.md`
- `docs/prd.1.1-backend-technical-implementation.md`
- `docs/engineering-rules.md`
- `docs/architecture.md`
- `docs/use-cases.md`
- `docs/design-guidelines.md`
- `openspec/config.yaml`
- `openspec/changes/01-backend-prd/proposal.md`
- `openspec/changes/01-backend-prd/design.md`
- every delta specification under `openspec/changes/01-backend-prd/specs/`
- `openspec/changes/01-backend-prd/tasks.md`

`CODEX_PLAN_PERSIAN_PROJECT_MANAGEMENT.md` does not exist in this repository. Do not
invent or require it; the maintained sources above are authoritative according to
`AGENTS.md`.

Before each numbered implementation phase, re-read the current versions of the
authoritative sources plus that phase's proposal, design, all delta specifications,
tasks, and the context files returned by:

```bash
openspec status --change "<phase-change-id>" --json
openspec instructions apply --change "<phase-change-id>" --json
```

Use the installed OpenSpec propose workflow to create phase artifacts, the apply
workflow to implement them, and the sync/archive workflow only after completion
evidence is verified.

## Hard preflight: Phase 0

Roadmap planning is allowed while the user repairs Docker, but backend Phase 1 code
is not allowed until Phase 0 is complete.

1. Read `openspec/changes/phase-0-repository-foundation/tasks.md`.
2. Confirm every checkbox is complete, including task 4.2 for actual Compose build
   and runtime verification.
3. Run the complete Phase 0 gates:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest

cd ../frontend
pnpm lint
pnpm test
pnpm build
pnpm e2e
pnpm generate:api

cd ..
openspec validate --all --strict
```

4. Verify the native and Compose runtime resources required by the Phase 0 change.
5. Synchronize the Phase 0 delta specs, verify the main specs, and archive the Phase
   0 change.
6. Check roadmap tasks 1.1 and 1.2 only after all evidence exists.

If Phase 0 task 4.2 is still blocked by Docker, WSL, virtualization, or another host
dependency, perform no Phase 1 code, schema, dependency, or task changes. Report:

- exact incomplete task
- commands attempted
- relevant observed output
- required external action
- remaining Phase 0 work

## Backend delivery sequence

Create only the next eligible phase change. Do not create later phase changes in
advance.

1. `01-backend-foundation-auth`
   - BE-FR-01 residual database foundation, BE-FR-02 auth/session, UC-01
2. `02-backend-workspace-rbac`
   - BE-FR-03, UC-02, UC-03
3. `03-backend-project-board-foundation`
   - BE-FR-04, UC-04, UC-05
4. `04-backend-task-core`
   - BE-FR-05 task core excluding atomic move, UC-06, UC-07, UC-12
5. `05-backend-board-move`
   - BE-FR-05 atomic move/version behavior, UC-06
6. `06-backend-collaboration`
   - BE-FR-06, UC-07
7. `07-backend-project-views-reporting`
   - project-scoped BE-FR-08, UC-05, UC-08
8. `08-backend-notifications-profile-dashboard`
   - remaining BE-FR-02 profile, BE-FR-07, global BE-FR-08, UC-09–UC-11
9. `09-backend-hardening-seed-delivery`
   - BE-FR-09 and the complete Backend PRD Definition of Done

For each phase:

1. Confirm the preceding change is synchronized and archived.
2. Create the exact phase change ID with OpenSpec.
3. Generate proposal, delta specs, design, and tasks in dependency order using the
   current `openspec instructions <artifact> --change "<id>" --json`.
4. Make every phase task independently verifiable and trace it to the relevant PRD
   requirement, use case, acceptance criterion, and test.
5. Run `openspec validate --all --strict` before changing runtime code.
6. Apply only that phase's approved tasks in order.
7. Update a task checkbox only after its named validation succeeds.
8. Complete migrations, OpenAPI regeneration, tests, documentation, and changelog
   work within the phase.
9. Run the phase gate and inspect failures; fix root causes and rerun the relevant
   checks.
10. Compare and synchronize delta specs into the main specs, verify the merge, and
    archive the phase change.
11. Check the corresponding `01-backend-prd/tasks.md` checkpoints only after the
    phase is archived with evidence.
12. Only then create the next phase.

## Architecture and implementation rules

1. Preserve API → Service → Repository → SQLAlchemy/DB dependency flow.
2. Route handlers may parse input, inject dependencies, manage HTTP details and
   cookies, declare OpenAPI metadata/statuses, and serialize responses. Do not put
   business logic or persistence queries in route handlers.
3. Services own business rules, final resource authorization, transaction
   boundaries, Activity/Notification orchestration, and StorageService coordination.
4. Repositories own queries, CRUD primitives, pagination, allowlisted filters/sorts,
   aggregates, and intentional eager loading. Repositories do not make business-role
   decisions and do not commit service transactions.
5. Enforce authentication and authorization in the backend at resource level.
   Hidden frontend controls are not authorization.
6. Use UUID primary keys, explicit foreign keys/unique constraints/query-driven
   indexes, and offset-aware UTC timestamps.
7. Make every schema change through Alembic. Do not use application `create_all()` as
   a migration substitute.
8. Keep SQLite transactions short and avoid SQLite-specific domain behavior that
   blocks future PostgreSQL migration.
9. Prefer archive over destructive deletion for Project, Task, and BoardColumn.
10. Never store, log, return, or commit plaintext passwords, access tokens, refresh
    tokens, secrets, password hashes, token hashes, or sensitive session metadata.
11. Do not expose stack traces, SQL errors, internal exception details, or resource
    existence that should be protected from enumeration.
12. Do not implement frontend functionality. Regenerating
    `frontend/src/lib/api/schema.d.ts` after API changes is required contract work.
13. Do not implement WebSocket/SSE, external workers, real email/push, SSO/LDAP,
    billing, webhooks/public API keys, PostgreSQL provisioning, S3, or another PRD
    exclusion.
14. Do not leave permanent mocks, stubs, placeholder implementations, `pass`, fake
    success responses, disabled tests, commented-out unfinished code, or unexplained
    TODO/FIXME markers.
15. Preserve unrelated user changes. Do not perform broad refactors or introduce
    dependencies outside the active phase.
16. Review current official/Context7 documentation before adding or using a changing
    framework, library, SDK, API, or CLI dependency.

## Public contract rules

- Keep `/health` at the root.
- Put product API routes under `/api/v1`.
- Publish Swagger at `/docs`, ReDoc at `/redoc`, and OpenAPI at
  `/api/v1/openapi.json` when documentation is enabled.
- Keep production documentation disabled through configuration.
- Use the project success envelopes:

```json
{ "data": {} }
```

```json
{
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 0
  }
}
```

- Use the project error envelope:

```json
{
  "error": {
    "code": "stable_code",
    "message": "safe message",
    "details": null,
    "request_id": "request-id"
  }
}
```

- `/api/v1/auth/token` is the OAuth2 compatibility exception and returns top-level
  `access_token` and `token_type` fields so Swagger Authorize works.
- Every route must declare summary, description, tags, response model, status code,
  important error responses, and examples.
- Pagination defaults to 20 and is capped at 100.
- Client-provided sort fields use explicit allowlists.

## Phase 1 security contract

Unless current primary documentation reveals a concrete incompatibility, implement
these locked defaults in the Phase 1 artifacts and code:

- `POST /api/v1/auth/register` returns `201` with public user data and does not
  implicitly log the user in.
- Normalize emails to lowercase before uniqueness checks.
- Require passwords of at least ten characters.
- Hash passwords using `pwdlib[argon2]` recommended settings.
- Perform a dummy password verification for an unknown email and return a generic
  invalid-credentials error.
- Issue 30-minute HS256 access JWTs containing `sub`, `iat`, `exp`, and unique `jti`.
- Pin the allowed decode algorithm and safely distinguish expiration from other
  invalid token cases.
- Use a cryptographically random opaque seven-day refresh value in an `HttpOnly`
  cookie. Store only its cryptographic hash in RefreshSession.
- Rotate refresh sessions on every successful refresh, link replacements, revoke on
  logout, reject expired/revoked values, and revoke the affected replacement chain
  when a previously rotated credential is replayed.
- Apply environment-aware `Secure`, `SameSite`, cookie path/domain, credentialed CORS,
  and configured-origin validation to refresh/logout operations.
- Put register/login rate limiting behind an injected, deterministically testable
  interface. Document the MVP single-process limitation; do not add Redis solely for
  Phase 1.

## Required endpoint and behavior coverage

Implement the endpoint groups exactly as they become in scope in Backend PRD 1.1:

- Auth and profile: register, token, refresh, logout, auth me, users me, avatar.
- Workspace/RBAC: workspace CRUD/archive/restore, members, invitations, acceptance.
- Projects/Board: project CRUD/archive/restore, members, columns, reorder/archive.
- Tasks: CRUD/archive/restore, move, assignees, labels, subtasks, query filters.
- Collaboration: checklists/items, comments, attachments, activity.
- Notifications: list, unread count, mark one/read all, due notification job.
- Reporting: global dashboard, project dashboard/overview/timeline/calendar.
- Delivery: idempotent development seed, migration/startup/container documentation.

For each endpoint, add positive, validation, unauthenticated, unauthorized,
not-found/conflict, and domain edge-case tests where applicable. Test compound
operation rollback and prevent IDOR.

## Required validation loop

Run the relevant focused tests while implementing. At the end of every phase run:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

When the public API changes, start the backend and run:

```bash
cd frontend
pnpm generate:api
```

Then run from the repository root:

```bash
openspec validate --all --strict
```

Do not mark the phase gate complete merely because a command was attempted. It must
exit successfully and its result must represent the intended behavior.

## Runtime and HTTP verification

At applicable checkpoints start the app with:

```bash
cd backend
uv run fastapi dev app/main.py
```

Verify:

- `/health`
- `/docs`
- `/redoc`
- `/api/v1/openapi.json`
- Swagger OAuth2 Password Flow authorization
- the active phase's real success and failure scenarios through HTTP

By final completion, verify the real sequence:

1. Register and validate duplicate/invalid/weak-input rejection.
2. Log in with OAuth2 form data and retrieve authenticated identity.
3. Refresh, prove rotation, reject replay/revocation, and log out.
4. Create a Workspace and prove atomic Owner membership.
5. Add an existing member and prove unauthorized role changes fail.
6. Create a Project and prove creator membership plus five default columns.
7. Create, query, edit, assign, label, and archive/restore Tasks.
8. Move/reorder a Task, prove persistence and Done/completion synchronization, and
   reject a stale version.
9. Add Checklist, Subtask, Comment, and Attachment; prove file and permission
   safeguards.
10. Verify project views, global/project dashboards, and fixture-accurate metrics.
11. Verify notifications, dedupe, profile/avatar behavior, and due notification job.
12. Prove a Member cannot perform an Admin action.
13. Log out and prove the revoked session cannot be reused.

## Database verification

Use only explicit disposable test databases:

1. Start from an empty database.
2. Run `alembic upgrade head`.
3. Confirm all expected tables, foreign keys, indexes, and unique/check constraints.
4. Run safe downgrade/upgrade round trips required by the active phase.
5. Start a fresh application against the migrated database.
6. Run the phase integration tests and final seed twice to prove idempotency.
7. Never downgrade, delete, overwrite, or repoint a non-test database.

## Progress log

Keep a concise progress log throughout the goal:

- current roadmap phase and checkpoint
- active OpenSpec change and task number
- files changed
- migration revision/state
- validation completed with results
- remaining work
- exact blockers and attempted commands

Do not use the progress log as completion evidence unless the referenced validation
actually passed.

## Final stopping condition

Stop successfully only when all of the following are true:

- Phase 0 was fully verified and archived before Phase 1 implementation.
- All nine backend phase changes were created sequentially, strictly validated,
  fully implemented, synchronized, and archived.
- Every checkbox in `openspec/changes/01-backend-prd/tasks.md` is checked with
  evidence.
- BE-FR-01 through BE-FR-09 and the backend responsibilities of UC-01 through UC-12
  have traceable implementation and test evidence.
- All Alembic migrations succeed from an empty disposable database and expected
  constraints/indexes exist.
- The application starts without startup errors against the migrated database.
- Swagger OAuth2 authorization and all required HTTP flows pass.
- Ruff lint, Ruff formatting, MyPy, Pytest, generated OpenAPI types, and strict
  OpenSpec validation pass.
- Seed execution is idempotent.
- Permission, IDOR, sensitive-data, file-storage, notification-dedupe, ordering,
  query/N+1, and migration audits have no known critical/high defect.
- No permanent mock, stub, placeholder, unfinished code, disabled critical test, or
  unexplained contract drift remains.
- README and CHANGELOG accurately describe the delivered backend, migrations,
  commands, production/security limitations, and known non-critical issues.
- The `backend-delivery-program` delta spec is synchronized and `01-backend-prd` is
  ready to archive.

If completion is blocked, do not claim partial work is the complete backend. Report
the exact blocker, affected roadmap and phase tasks, attempted commands, observed
output, safe work completed, and remaining work.
