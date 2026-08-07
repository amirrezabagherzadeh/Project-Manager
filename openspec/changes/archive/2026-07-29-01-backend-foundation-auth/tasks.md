## 1. Configuration and Dependencies

- [x] 1.1 Update `backend/pyproject.toml`, `uv.lock`, environment examples, and
  `app/core/config.py` for reviewed PyJWT, `pwdlib[argon2]`, database, JWT,
  refresh-cookie, trusted-origin, and independent auth rate-limit settings; validate
  production secret and cookie invariants with focused settings tests
  (`backend-auth-session`: Access token security, Refresh sessions rotate and resist
  replay, Authentication rate limiting; `cd backend && uv run pytest
  tests/unit/test_config.py`).
- [x] 1.2 Add the versioned API/router and package boundaries for models, schemas,
  repositories, and services without business queries in routes or commits in
  repositories; verify imports with `cd backend && uv run mypy app`
  (`backend-database-foundation`: Service-owned atomic transactions).

## 2. Async Persistence and Migration

- [x] 2.1 Implement `app/core/database.py` and focused base/UUID/UTC model
  conventions with request-scoped `AsyncSession`, SQLite foreign keys, rollback on
  dependency failure, and lifespan engine disposal; test session isolation,
  foreign-key enforcement, UTC round trips, and absence of startup `create_all()`
  (`backend-database-foundation`: Async database lifecycle, Portable identity and
  time conventions; `cd backend && uv run pytest tests/unit/test_database.py`).
- [x] 2.2 Implement `User` and `RefreshSession` SQLAlchemy models with explicit
  relationships, normalized-email/token-hash uniqueness, indexes, UTC timestamps,
  user cascade rules, and bounded replacement links; run focused model metadata tests
  (`backend-auth-session`: Sensitive authentication data stays private;
  `cd backend && uv run pytest tests/unit/test_models.py`).
- [x] 2.3 Add the first reversible Alembic revision for `users` and
  `refresh_sessions`, wire Alembic metadata/config without application schema
  creation, and test empty disposable upgrade, schema constraints/indexes/foreign
  keys, downgrade, and re-upgrade (`backend-database-foundation`: Alembic is the
  schema authority; `cd backend && uv run pytest tests/integration/test_migrations.py`).

## 3. Security and Request Boundaries

- [x] 3.1 Implement password hashing/verification with pwdlib recommended Argon2
  settings, off-event-loop execution, email normalization, and dummy verification
  for missing users; test valid/invalid hashes, unknown-user verification, and
  password-hash privacy (`backend-auth-session`: User registration,
  Swagger-compatible OAuth2 login; `cd backend && uv run pytest
  tests/unit/test_security.py -k password`).
- [x] 3.2 Implement HS256 access-token issue/decode with configured 30-minute
  lifetime, required `sub`/`iat`/`exp`/unique `jti`, pinned algorithm, and safe
  expired/invalid mappings; test tampering, wrong algorithm, missing claims,
  expiration, and unique token IDs (`backend-auth-session`: Access token security;
  `cd backend && uv run pytest tests/unit/test_security.py -k token`).
- [x] 3.3 Implement opaque refresh generation/SHA-256 hashing, symmetric
  environment-aware set/delete cookie helpers, and present-Origin validation;
  test entropy/one-way storage, cookie attributes, allowed/absent/untrusted origins,
  and invalid cookie configuration (`backend-auth-session`: Refresh sessions rotate
  and resist replay, Logout revokes the refresh session; `cd backend && uv run
  pytest tests/unit/test_auth_boundaries.py`).
- [x] 3.4 Implement the injected limiter protocol and deterministic locked
  single-process fixed-window implementation with independent register/login
  settings; test key/window/reset behavior and `429` decisions without sleeps
  (`backend-auth-session`: Authentication rate limiting; `cd backend && uv run
  pytest tests/unit/test_rate_limit.py`).

## 4. Identity Repositories and Services

- [x] 4.1 Implement user and refresh-session repositories for normalized lookup,
  create/flush, hashed-session lookup, replacement linking, bounded user-scoped
  chain traversal, and revocation without repository commits; verify query results
  and transaction rollback in focused repository tests
  (`backend-database-foundation`: Service-owned atomic transactions;
  `cd backend && uv run pytest tests/integration/test_auth_repositories.py`).
- [x] 4.2 Implement `AuthService.register` and login so registration is atomic,
  duplicates map to `409`, valid credentials create hashed refresh sessions, unknown
  and wrong-password failures are generic, and no failed operation persists partial
  data (`backend-auth-session`: User registration, Swagger-compatible OAuth2 login;
  `cd backend && uv run pytest tests/integration/test_auth_service.py -k
  "register or login"`).
- [x] 4.3 Implement authenticated-user resolution, atomic refresh rotation, expired/
  revoked/unknown rejection, replay-chain revocation, and enumeration-safe logout;
  test successful rotation, old-token replay, descendant revocation, expiry,
  rollback, unknown users, and repeated logout (`backend-auth-session`: Access token
  security, Refresh sessions rotate and resist replay, Logout revokes the refresh
  session; `cd backend && uv run pytest tests/integration/test_auth_service.py -k
  "current_user or refresh or replay or logout"`).

## 5. HTTP and OpenAPI Contract

- [x] 5.1 Add central domain-error mapping and authentication dependencies that
  preserve request IDs, Bearer challenges, safe stable error codes, and resource
  privacy; test `401 authentication_required`, `401 token_expired`, `403
  permission_denied`, `409 resource_conflict`, `422 validation_error`, `429
  rate_limited`, and no sensitive details (`backend-auth-session`: Access token
  security, Sensitive authentication data stays private; `cd backend && uv run
  pytest tests/integration/test_auth_errors.py`).
- [x] 5.2 Implement documented `POST /api/v1/auth/register`, form-urlencoded
  `/auth/token`, `/auth/refresh`, `/auth/logout`, and protected `GET /auth/me`
  routes with schemas, examples, cookies, status codes, and OAuth2 password-flow
  metadata; verify success, invalid input, duplicate, unauthenticated, untrusted
  origin, rate-limit, refresh/replay, and logout HTTP scenarios
  (`backend-auth-session`: all Phase 1 API requirements; `cd backend && uv run pytest
  tests/integration/test_auth_api.py`).
- [x] 5.3 Audit `/api/v1/openapi.json`, `/docs`, and `/redoc` for every Phase 1
  operation, declared responses/examples, no private model fields, and a Swagger
  password flow whose token URL is `/api/v1/auth/token`; verify with
  `cd backend && uv run pytest tests/integration/test_openapi.py`
  (`backend-auth-session`: Authentication OpenAPI contract is complete).

## 6. Runtime, Contract, and Documentation

- [x] 6.1 Against an explicitly disposable migrated database, start the application
  and exercise real HTTP Register → OAuth2 Login → `/auth/me` → Refresh → reject
  replay → Logout → reject reuse plus invalid/duplicate/weak/rate-limited/untrusted
  cases; record that `/health`, `/docs`, `/redoc`, and OpenAPI remain available
  (`backend-auth-session`: all acceptance scenarios; automated command
  `cd backend && uv run pytest tests/integration/test_auth_http_flow.py` plus the
  documented runtime smoke command).
- [x] 6.2 Run the backend against the migrated database and execute `cd frontend &&
  pnpm generate:api`; inspect and commit only the generated
  `src/lib/api/schema.d.ts` contract with no unexplained private fields or drift
  (`backend-auth-session`: Authentication OpenAPI contract is complete).
- [x] 6.3 Update `README.md` and `CHANGELOG.md` with Phase 1 behavior, migration and
  startup commands, Swagger/Postman auth flow, required/production configuration,
  cookie/origin policy, generated-contract evidence, rollback, and the single-process
  rate-limit/SQLite concurrency limitations.

## 7. Phase 1 Quality Gate

- [x] 7.1 Run exactly `cd backend && uv run ruff check .`, `uv run ruff format
  --check .`, `uv run mypy app`, and `uv run pytest`; fix every failure and leave
  the task unchecked unless all commands exit successfully.
- [x] 7.2 Run `cd frontend && pnpm generate:api`, then from the repository root run
  `openspec validate --all --strict`; confirm the generated contract is current and
  every Phase 1 requirement has passing evidence before synchronization and archival.
