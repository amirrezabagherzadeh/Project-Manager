## Why

Phase 0 established an observable FastAPI shell, but Backend PRD 1.1 cannot progress
to Workspace or project behavior without a migrated async database foundation and a
secure identity/session boundary. Phase 1 delivers the residual BE-FR-01 database
work and BE-FR-02 authentication flow required by UC-01, while preserving the
existing health and documentation contract.

## What Changes

- Add SQLAlchemy 2 async engine/session infrastructure for SQLite with enforced
  foreign keys, service-owned transactions, UTC/UUID model conventions, and an
  Alembic revision for `User` and `RefreshSession`.
- Add registration, OAuth2 password-form login, access JWT validation, refresh-token
  rotation/replay revocation, logout, and authenticated identity endpoints under
  `/api/v1`.
- Add injected single-process rate limiting for register/login and configured-origin,
  CORS, and environment-aware refresh-cookie safeguards.
- Extend the stable success/error envelopes and OpenAPI metadata so Swagger Authorize
  can exercise the complete UC-01 flow.
- Add unit, integration, migration, runtime HTTP, and contract tests; regenerate the
  frontend OpenAPI schema and document the development limitations.

Goals:

- Satisfy Backend PRD 1.1 BE-FR-01 residual database acceptance and BE-FR-02
  register/login/me/refresh/logout acceptance for UC-01.
- Store only password hashes and refresh-token hashes, return generic credential
  failures, and keep access JWTs short-lived and algorithm-pinned.
- Make an empty database upgradeable and downgradeable through Alembic with no
  application `create_all()` fallback.

Non-goals:

- Profile editing/avatar support, which remains in Phase 8.
- Workspace/RBAC, Project, Task, Notification, or reporting behavior.
- Distributed rate limiting, external session stores, password reset, email
  verification, MFA, SSO, or frontend authentication UI.

Dependencies:

- Verified and archived Phase 0 foundation.
- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async, aiosqlite, Alembic,
  PyJWT, and `pwdlib[argon2]`.

Risks and rollback:

- Authentication mistakes can expose reusable credentials; hashes, cookie policy,
  origin validation, rotation/replay tests, and log-response audits control this.
- SQLite concurrency and migration drift are controlled with short transactions,
  explicit constraints, disposable upgrade/downgrade tests, and PostgreSQL-portable
  ORM patterns.
- Rollback removes the Phase 1 API/modules/dependencies and applies the tested
  Alembic downgrade only to an explicitly disposable or approved database.

## Capabilities

### New Capabilities

- `backend-database-foundation`: Async SQLAlchemy/session lifecycle, SQLite integrity,
  common UUID/UTC persistence conventions, and the first Alembic domain revision
  (Backend PRD 1.1 BE-FR-01; prerequisite for UC-01).
- `backend-auth-session`: Registration, OAuth2 login, access JWT authentication,
  rotating refresh sessions, logout, `/auth/me`, rate limiting, and safe public
  contracts (Backend PRD 1.1 BE-FR-02; UC-01).

### Modified Capabilities

None.

## Impact

- Backend: `app/core`, `app/api/v1`, identity models/schemas/repositories/services,
  migrations, tests, `pyproject.toml`, and `uv.lock`.
- Public API: new `/api/v1/auth/register`, `/auth/token`, `/auth/refresh`,
  `/auth/logout`, and `/auth/me` operations; `/health` remains at the root.
- Contract/docs: generated `frontend/src/lib/api/schema.d.ts`, `README.md`, and
  `CHANGELOG.md`.
- Runtime configuration: database URL, JWT secret/algorithm and lifetimes,
  refresh-cookie settings, trusted origins, and rate-limit settings.
