## Context

See `proposal.md` for motivation and the two Phase 1 delta specs for observable
behavior. The repository has a FastAPI factory and Alembic environment but no domain
revision, database lifecycle, versioned API router, identity model, or authentication
dependency. Phase 0 is verified and archived. Current primary documentation confirms
FastAPI's OAuth2 password flow and response cookie APIs, SQLAlchemy 2's async session
and explicit transaction patterns, and PyJWT's algorithm pinning, required claims,
and expiration exception.

## Goals / Non-Goals

**Goals:**

- Introduce the smallest reusable persistence conventions needed by later domains.
- Keep API parsing/cookies/OpenAPI, service rules/transactions, repository queries,
  and model constraints in separate layers.
- Make Swagger login work without weakening refresh-cookie or origin protections.
- Make security and time-dependent behavior deterministic under tests.
- Preserve SQLite MVP operation and PostgreSQL-portable model/query semantics.

**Non-Goals:**

- A generic repository framework, unit-of-work abstraction, or dependency-injection
  container.
- Profile mutation/avatar, RBAC, audit activity, notification, or frontend auth UX.
- Distributed rate limiting or cross-process session caching.

## Decisions

### Request sessions and service transaction ownership

`app/core/database.py` constructs one `AsyncEngine` and
`async_sessionmaker(expire_on_commit=False, autoflush=False)` per application
settings instance. A FastAPI dependency yields one `AsyncSession` per request and
rolls back any still-active failed transaction before closing. Write services use
`async with session.begin()`; repositories only select/add/flush and never commit.
The application lifespan disposes the engine.

For SQLite connections a connect event enables `PRAGMA foreign_keys=ON`. Tests create
an explicit temporary database and apply Alembic before application startup.
Application startup never calls `create_all()`.

Alternative rejected: commit in each repository method. It prevents atomic compound
operations and makes later Workspace/Project transactions unreliable.

### Portable UUID and UTC model base

Models use SQLAlchemy `Uuid(as_uuid=True)` identifiers. A focused UTC-aware datetime
type normalizes values on bind and restores UTC awareness on result so SQLite's
timezone loss does not leak into domain behavior; migrations declare timezone-aware
datetime columns and explicit indexes/constraints. A shared declarative base and
timestamp mixin are intentionally small.

Alternative rejected: SQLite string IDs and naive timestamps interpreted at route
serialization. That spreads engine-specific behavior and risks a later PostgreSQL
migration.

### User and refresh-session schema

`users` contains UUID id, normalized unique indexed email, display name,
`password_hash`, active flag, and created/updated UTC timestamps.
`refresh_sessions` contains UUID id/user foreign key, unique indexed SHA-256 token
hash, created/expires/revoked timestamps, nullable self-referencing
`replaced_by_id`, and optional replay-detection timestamp. Public schemas never map
private hash fields.

The refresh credential is at least 256 random bits encoded URL-safely. SHA-256 is
appropriate for storage because the input is uniformly random and non-guessable;
passwords use Argon2 through `PasswordHash.recommended()`. Password hash/verify work
runs off the async event loop. A precomputed dummy Argon2 hash is verified for
unknown emails.

Alternative rejected: refresh JWTs or plaintext opaque tokens in the database.
Either complicates immediate revocation or turns a database disclosure into reusable
credentials.

### Access JWT contract

`app/core/security.py` issues HS256 access JWTs for 30 minutes with string UUID
`sub`, UTC `iat`/`exp`, and random UUID `jti`. Decode supplies
`algorithms=["HS256"]` and requires all four claims. Expiration maps to
`token_expired`; all other decoding/subject/user failures map to the generic
authentication error and Bearer challenge.

The application has an explicitly labeled insecure development-only signing default
to keep Phase 0 zero-to-running behavior. Production validation rejects a missing,
short, or development-default secret. Tests always inject a test-only secret.

Alternative rejected: choosing the decode algorithm from the token header, which
permits algorithm confusion.

### Refresh rotation and replay handling

Login creates one refresh row and sets the raw credential only in the response
cookie. Refresh hashes the submitted cookie and selects its session and user in the
service transaction:

1. Unknown, expired, or revoked-without-replacement credentials fail and clear the
   cookie.
2. An active credential is revoked, a replacement row is linked, a new cookie and
   access JWT are issued, and the transaction commits atomically.
3. A revoked credential with a replacement is treated as replay. The service walks
   the bounded replacement chain for that user, revokes active descendants, records
   replay detection, commits that defensive revocation, clears the cookie, and then
   returns the safe authentication error.

Repository helpers are user-scoped and chain traversal is bounded to prevent corrupt
data from causing unbounded work. Concurrent refreshes rely on the first committed
rotation plus the unique token hash; integration tests cover the observable single
success and replay outcome supported by SQLite.

Alternative rejected: simply reject an old credential without revoking its
replacement; a stolen rotated credential could remain usable.

### Cookie, CORS, and origin boundary

The refresh cookie defaults to path `/api/v1/auth`, `HttpOnly`, `SameSite=Lax`, and a
seven-day max age; production requires `Secure`. Domain, name, path, Secure, and
SameSite are configurable with validation (`SameSite=None` requires Secure).
Clearing uses the same name/path/domain/SameSite/Secure attributes.

Refresh and logout validate `Origin` when the header is present against the same
configured trusted-origin allowlist used for credentialed CORS. An absent Origin is
accepted for Swagger, Postman, CLI, and other non-browser clients; a present
untrusted or malformed Origin is rejected before session mutation.

Alternative rejected: requiring Origin on every request, which breaks legitimate
non-browser clients and Swagger tooling without adding browser CSRF protection.

### Injected single-process rate limiter

Routes depend on a small limiter protocol. The development implementation uses a
locked, monotonic-clock fixed window keyed by endpoint plus client address;
login additionally incorporates normalized email without logging it. Tests inject a
fake clock/limiter. Register and login limits/windows are independently configured.

This limiter is intentionally documented as single-process and non-shared across
workers. Redis is deferred until deployment topology requires it.

Alternative rejected: module-global decorators with real sleeps, which are hard to
test and hide behavior outside application dependencies.

### API, errors, and OpenAPI

A versioned router includes `auth` endpoints. Routes own form/body parsing, response
cookies, response status, and metadata; `AuthService` owns identity rules and
transactions; `UserRepository` and `RefreshSessionRepository` own persistence.
Registration and `/auth/me` use the standard single-success envelope. Token and
refresh return OAuth-compatible top-level bearer fields. Logout returns `204`.

Domain exceptions carry stable code/status/safe details and the existing central
handler renders them with request ID. FastAPI validation is already normalized.
Every endpoint declares success and important error responses/examples. The
`OAuth2PasswordBearer` token URL is the absolute API path, so Swagger Authorize posts
form data to the correct operation.

After runtime verification, `pnpm generate:api` refreshes the committed TypeScript
schema. No handwritten frontend feature changes are permitted.

### Test and observability strategy

Unit tests cover password hashing/dummy verification, JWT required claims and expiry,
cookie configuration, origin validation, rate limiter time windows, and replay-chain
revocation. Integration tests use migrated disposable SQLite files and cover
register/token/me/refresh/logout plus `401`, `403`, `409`, `422`, `429`, rotation,
replay, rollback, and sensitive response/log audits. Migration tests inspect required
tables, foreign keys, unique constraints, and indexes and perform a safe
downgrade/upgrade round trip.

Structured request logs retain method/path/status/request ID only. Authentication
services do not log request bodies, credentials, tokens, or hash values.

## Risks / Trade-offs

- [Argon2 work can exhaust request capacity] → run hash/verify outside the event
  loop, rate-limit entry points, and keep parameters at pwdlib's reviewed defaults.
- [SQLite cannot provide production-grade concurrent refresh locking] → keep the
  transaction short, enforce unique hashes, test concurrency outcomes, and document
  that production scale requires PostgreSQL review.
- [Single-process rate limits reset on restart and diverge across workers] → state
  the limitation in README/CHANGELOG and keep the protocol replaceable.
- [Development signing default may be copied to production] → production settings
  explicitly reject it and startup tests cover rejection.
- [Cookie settings can become internally inconsistent] → validate SameSite/Secure/
  domain/path combinations at settings load and test set/delete symmetry.

## Migration Plan

1. Add reviewed dependencies/configuration and database/security primitives.
2. Add models and an explicit first Alembic revision.
3. On an empty disposable database run upgrade, inspect schema, downgrade, and
   re-upgrade.
4. Add repositories/services/dependencies/routes and focused tests.
5. Run the backend quality gate and real HTTP auth flow against the migrated
   disposable database.
6. Regenerate the frontend OpenAPI schema, update README/CHANGELOG, and run strict
   OpenSpec validation.
7. Synchronize the two delta specs and archive only after all evidence is green.

Rollback removes Phase 1 routes/modules and applies the tested Phase 1 downgrade only
to an explicitly disposable or operator-approved database. Any issued access tokens
are invalidated by changing the signing key; stored refresh sessions disappear with
the downgraded schema.
