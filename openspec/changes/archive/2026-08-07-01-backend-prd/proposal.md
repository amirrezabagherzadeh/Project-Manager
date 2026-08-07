## Why

Backend PRD 1.1 defines a complete FastAPI API, but the repository currently stops at
Phase 0 and has no controlled program for delivering BE-FR-01 through BE-FR-09. This
change establishes the master, phase-gated delivery contract needed to implement and
verify the complete backend without mixing phases or bypassing the unfinished Phase 0
Compose gate (UC-01 through UC-12).

## What Changes

- Add a backend delivery program that turns Backend PRD 1.1 into nine sequential
  OpenSpec implementation changes: Auth/Database, Workspace/RBAC, Projects/Board
  foundation, Tasks, Board Move, Collaboration, Project Views, Dashboard/
  Notifications/Profile, and Hardening/Delivery.
- Require Phase 0 task 4.2 and the complete Phase 0 quality gate to pass before any
  Phase 1 implementation begins.
- Require every phase to create its own proposal, delta specifications, design, and
  independently verifiable tasks before code changes start.
- Require each phase to pass its acceptance scenarios, migrations, OpenAPI contract,
  quality gates, documentation, and changelog work before its specifications are
  synchronized, the change is archived, and the next phase is created.
- Add a copy-ready master implementation prompt that can drive the complete backend
  program while preserving the OpenSpec apply and archive workflows.

Goals:

- Deliver all backend requirements in BE-FR-01 through BE-FR-09 and support the
  backend portions of UC-01 through UC-12.
- Preserve API → Service → Repository boundaries, backend authorization, Alembic-only
  schema changes, UTC timestamps, and SQLite-to-PostgreSQL portability.
- Make completion evidence-based: no task is complete until its named validation
  succeeds.

Non-goals:

- Frontend feature implementation; only generated OpenAPI contract updates required
  by backend API changes are included.
- WebSocket/SSE, external workers, real email/push, SSO/LDAP, billing, public API keys,
  webhooks, PostgreSQL provisioning, S3, or other Backend PRD 1.1 exclusions.
- Creating all phase-specific implementation artifacts in advance. They are created
  only when the preceding phase gate has passed.

## Capabilities

### New Capabilities

- `backend-delivery-program`: Orchestrates sequential, verifiable delivery of the
  complete FastAPI backend defined by BE-FR-01 through BE-FR-09 and the backend
  acceptance flows in UC-01 through UC-12.

### Modified Capabilities

None.

## Impact

- Affected planning paths: `openspec/changes/01-backend-prd/`, later phase-specific
  changes under `openspec/changes/`, and synchronized main specifications under
  `openspec/specs/`.
- Future implementation paths: `backend/app/`, `backend/migrations/`,
  `backend/tests/`, backend dependency/configuration files, generated
  `frontend/src/lib/api/schema.d.ts`, `README.md`, and `CHANGELOG.md`.
- Public API impact: the future phase changes add the REST/JSON surface under
  `/api/v1` defined by Backend PRD 1.1 while preserving `/health` and the documented
  OpenAPI paths.
- Dependencies: the completed Phase 0 gate, Python 3.12/uv, SQLite, Alembic,
  FastAPI, Pydantic v2, SQLAlchemy 2 async, and phase-approved security/storage
  dependencies reviewed against current documentation.
- Risks: oversized scope, phase leakage, permission drift, schema rollback failure,
  SQLite contention, OpenAPI drift, and false completion. Controls are hard phase
  gates, per-phase OpenSpec artifacts, negative tests, disposable migration checks,
  and exact quality commands.
- Rollback: the roadmap itself is planning-only and can be removed without changing
  runtime behavior. Each implementation phase owns its reversible Alembic downgrade
  and file-level rollback plan; no later phase starts until the current phase is
  independently recoverable and verified.
