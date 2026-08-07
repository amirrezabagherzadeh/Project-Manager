## Context

See `proposal.md` for motivation and
`specs/backend-delivery-program/spec.md` for the observable delivery contract.
Phase 0 provides a runnable FastAPI shell, OpenAPI, logging, error envelopes, and
Alembic infrastructure, but it has no domain revision and Compose verification task
4.2 is still open. Backend PRD 1.1 spans security-sensitive identity, authorization,
ordering, file storage, notifications, reporting, and delivery work, so treating it
as one implementation batch would defeat the mandatory phase gates.

## Goals / Non-Goals

**Goals:**

- Keep one durable roadmap and master prompt for the complete backend while allowing
  only one phase-specific implementation change at a time.
- Make every phase independently specifiable, migratable, testable, reversible, and
  archivable.
- Preserve the modular-monolith boundaries and public contracts defined by the
  project documents.
- Carry validation evidence and traceability forward without copying unfinished
  implementation tasks into later phases.

**Non-Goals:**

- Use the roadmap change itself as authorization to implement all phases at once.
- Preselect detailed schemas, dependencies, or query strategies that belong to a
  later phase and require that phase's current documentation review.
- Change the frontend beyond regenerating its committed OpenAPI type contract.

## Decisions

### The roadmap is an orchestrator, not a monolithic implementation change

`01-backend-prd` remains active for the duration of backend delivery. Its tasks track
phase creation, completion evidence, synchronization, and archival. Runtime code is
changed only under the current phase-specific change.

Alternative rejected: one proposal/design/task list containing every implementation
detail for Phases 1–9. It would violate `openspec/config.yaml`, encourage stale
decisions, and allow later work to begin before earlier public contracts stabilize.

### Fixed phase sequence and ownership

| Phase | Change ID | Governing backend scope |
|---|---|---|
| 1 | `01-backend-foundation-auth` | BE-FR-01 residual database work and BE-FR-02 auth/session; UC-01 |
| 2 | `02-backend-workspace-rbac` | BE-FR-03; UC-02 and UC-03 |
| 3 | `03-backend-project-board-foundation` | BE-FR-04; UC-04 and UC-05 |
| 4 | `04-backend-task-core` | BE-FR-05 task CRUD/query relationships; UC-06, UC-07, UC-12 |
| 5 | `05-backend-board-move` | BE-FR-05 atomic move/version contract; UC-06 |
| 6 | `06-backend-collaboration` | BE-FR-06; UC-07 |
| 7 | `07-backend-project-views-reporting` | Project portions of BE-FR-08; UC-05, UC-08 |
| 8 | `08-backend-notifications-profile-dashboard` | BE-FR-02 profile remainder, BE-FR-07, global BE-FR-08; UC-09, UC-10, UC-11 |
| 9 | `09-backend-hardening-seed-delivery` | BE-FR-09 and complete security/performance/delivery audit |

The next change is created only after the current change has all tasks verified,
delta specs synchronized into `openspec/specs/`, and the change archived.

### Phase lifecycle

Each phase follows the same state machine:

1. Confirm the preceding gate and read the current project documents.
2. Create the numbered change and generate proposal → specs/design → tasks using
   current OpenSpec instructions.
3. Run strict OpenSpec validation.
4. Apply tasks in dependency order; update a checkbox only after its named validation.
5. Run phase acceptance, migration, runtime, OpenAPI, and quality gates.
6. Regenerate `frontend/src/lib/api/schema.d.ts` when the public contract changes.
7. Update `README.md` and `CHANGELOG.md` with delivered behavior and limitations.
8. Synchronize delta specs, verify the merge, and archive the phase change.
9. Record the phase result in the roadmap task before unlocking the next phase.

Alternative rejected: keep all nine phase changes active simultaneously. That makes
the active source of truth ambiguous and permits cross-phase task leakage.

### Backend architecture invariants

All phase designs preserve API → Service → Repository → SQLAlchemy/DB flow:

- API modules own parsing, dependencies, authentication hooks, OpenAPI metadata,
  status codes, cookie/header handling, and serialization.
- Services own business rules, resource authorization, transaction boundaries,
  Activity/Notification orchestration, and storage coordination.
- Repositories own persistence, pagination, allowlisted filtering/sorting, aggregate
  queries, and intentional eager loading; they do not decide business permissions.
- SQLAlchemy models own UUID keys, explicit constraints/indexes, relationships, and
  UTC timestamps. Public Pydantic schemas never expose password/token hashes or
  sensitive session metadata.

Compound operations named in `docs/engineering-rules.md` execute in one service-owned
transaction. Request-scoped `AsyncSession` instances do not commit inside
repositories. SQLite foreign keys are enabled, transactions stay short, and designs
avoid SQLite-only behavior that blocks PostgreSQL migration.

### Migrations and runtime database behavior

Every schema change has an Alembic revision with upgrade and downgrade logic.
Application startup never substitutes `create_all()` for migrations. Each phase
tests upgrade from an empty disposable database, expected constraints/indexes,
downgrade/upgrade round trips where safe, and startup against the migrated schema.
Commands must resolve an explicit test database before destructive migration checks.

Alternative rejected: automatic schema creation at startup. It hides migration drift
and makes production rollback unverifiable.

### Public API and OpenAPI contract

`/health` remains operational at the root; product routes live under `/api/v1`.
Single and list success envelopes and the standard error envelope remain authoritative.
The OAuth2 token endpoint is the documented exception: it returns top-level
`access_token` and `token_type` so Swagger Password Flow can authorize correctly.
Every operation has summary, description, response model, status code, tags, examples,
and important error responses.

OpenAPI changes are verified through `/api/v1/openapi.json`, Swagger, ReDoc, and
`pnpm generate:api`. Generated TypeScript output may change; handwritten frontend
features may not.

### Phase 1 security baseline

Phase 1 artifacts use these defaults unless current official documentation proves
an incompatibility:

- Registration returns `201` with public user data and does not create a login
  session; `/auth/token` remains the explicit OAuth2 form login.
- Emails are normalized before uniqueness checks. Passwords require at least ten
  characters, use `pwdlib[argon2]`, and use dummy verification for unknown users.
- Access tokens are 30-minute HS256 JWTs with `sub`, `iat`, `exp`, and `jti`;
  decoding pins the algorithm and maps expiry/invalidity to safe errors.
- Refresh credentials are random opaque seven-day values in environment-aware
  `HttpOnly` cookies. Only hashes are stored. Every refresh rotates the session;
  logout revokes it, and replay revokes the affected replacement chain.
- Refresh/logout validate the configured origin boundary in addition to
  `SameSite`, `Secure`, path, CORS, and credential settings.
- Register/login rate limiting is injected behind a testable interface. The MVP
  single-process implementation and its multi-worker limitation are documented;
  Redis or another external service is not introduced by this roadmap.

Alternative rejected: storing refresh JWTs or opaque refresh values directly. A
database leak would expose reusable credentials.

### Authorization and resource disclosure

Authentication and resource-level authorization are enforced in backend dependencies
and services using the sequence current user → workspace membership/role → project
membership/management → task permission. Tests cover `401`, `403`, and enumeration-
safe `404` behavior. UI visibility is never treated as permission enforcement.

### Observability and completion evidence

Structured logs retain request IDs but exclude credentials, tokens, hashes, and
private payloads. Expected domain failures use stable error codes; unexpected `500`
responses expose only a request ID. Each phase completion record includes the current
checkpoint, files changed, commands and results, remaining work, and exact blockers.

## Risks / Trade-offs

- [The roadmap can be mistaken for permission to skip phase artifacts] → The master
  prompt requires a phase-specific validated change before any runtime edit.
- [Phase 0 Docker remains externally blocked] → Roadmap artifacts may exist, but the
  master prompt stops before Phase 1 code and records task 4.2 as incomplete.
- [Later PRD details become stale] → Detailed decisions are made only when their
  phase is unlocked and after current documentation is fetched.
- [SQLite write contention] → Use short explicit transactions, targeted indexes,
  bounded queries, and PostgreSQL-portable SQLAlchemy patterns.
- [Permission or OpenAPI drift] → Central dependencies/services, negative matrix
  tests, schema regeneration, and strict per-phase gates.
- [Archiving loses or duplicates requirements] → Compare delta and main specs,
  synchronize once, verify the merged requirements, then archive.

## Migration Plan

1. Create and strictly validate this roadmap and master prompt while Phase 0 remains
   active.
2. After the user resolves Docker, verify Phase 0 task 4.2, rerun all Phase 0 gates,
   synchronize its specs, and archive it.
3. Execute the nine backend phase lifecycles in the fixed order above.
4. After Phase 9, audit Backend PRD traceability, full migrations, OpenAPI, HTTP
   flows, seed idempotency, security, and quality gates.
5. Synchronize the `backend-delivery-program` spec and archive this roadmap only when
   every phase record is complete.

Rollback is phase-local: stop progression, keep the failed task unchecked, revert
only the affected phase files through a reviewed change, and use that phase's tested
Alembic downgrade only against an explicitly disposable or approved database.
