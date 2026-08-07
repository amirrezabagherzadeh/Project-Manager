## Context

See `proposal.md` and the Phase 2 delta specification. Phase 1 provides authenticated
Users, request-scoped async sessions, service-owned transactions, safe errors, and
UUID/UTC conventions. Phase 2 is the first tenant/resource authorization boundary and
must be stable before private Projects exist.

## Goals / Non-Goals

**Goals:**

- Centralize Workspace role semantics and enumeration-safe membership lookup.
- Keep compound Workspace/member/invitation writes and side effects atomic.
- Persist only hashed invitation credentials and expose raw tokens once to an
  authorized creator.
- Add minimal durable activity/notification records needed by UC-02/UC-03 without
  implementing later listing/timeline behavior.

**Non-Goals:**

- Project membership or permissions.
- Email transport, notification polling endpoints, or activity timeline endpoints.
- Generic policy engines or event buses.

## Decisions

### Data model and ownership invariant

`Workspace` has UUID id, name/description, explicit `owner_id`, archive and UTC
timestamps. `WorkspaceMember` has UUID id, workspace/user foreign keys, string enum
role and joined timestamp with unique `(workspace_id,user_id)`. The service creates
Workspace, owner membership, and activity in one transaction.

Ownership transfer locks the logical operation inside one short transaction: validate
the actor as current owner, load target membership, set target OWNER, demote prior
owner to ADMIN, and update `owner_id`. SQLite serializes writes; PostgreSQL can later
add row locking without changing the service contract.

Alternative rejected: infer owner from the first OWNER membership only. An explicit
owner foreign key makes deletion/transfer checks and migrations auditable.

### Invitations

Invitation rows contain normalized email, non-owner role, SHA-256 hash of a
cryptographically random token, inviter, expiry, accepted/revoked timestamps, and
unique `(workspace_id,email)`. A revoked/expired row may be explicitly replaced by a
new credential only after service validation; active duplicates return `409`.
Acceptance compares the authenticated normalized email, creates membership and side
effects, and marks acceptance in one transaction.

Alternative rejected: store raw invitation tokens or reveal whether arbitrary emails
have accounts.

### Permission flow and disclosure

API dependencies establish current user and parse resources. Services perform the
final membership/role check using shared role predicates:

- OWNER: every Workspace/member/invitation action, delete, ownership transfer.
- ADMIN: Workspace update/archive/restore and non-owner member/invitation management.
- PROJECT_MANAGER/MEMBER: read/list only in Phase 2.

Non-members receive `404`; authenticated members lacking a role receive `403`.
Services recheck permissions even when a dependency has loaded membership.

Alternative rejected: role checks only in routes or frontend controls.

### Repository and query boundaries

Repositories own scoped selects, eager loading, pagination, normalized email lookup,
and CRUD/flush primitives; they never commit or decide role policy. Lists default to
20 and cap at 100. Services own transactions and conflict translation.

### Durable activity and notifications

Phase 2 introduces minimal shared `ActivityLog` and `Notification` tables because
UC-02/UC-03 require those side effects now. Activity records store actor, workspace,
entity/action, safe JSON metadata, and timestamp. Notification records store target,
type, title/body, entity/navigation metadata, read timestamp, optional logical
dedupe key, and creation time. No Phase 2 public list endpoint is added.

The Workspace service writes side effects in the same session. Self-notification is
suppressed. Later Collaboration/Notification phases extend schemas/services without
recreating these foundations.

Alternative rejected: no-op hooks or in-memory events, which would claim acceptance
without durable behavior and lose events on restart.

### Migration, API, and tests

Revision `20260729_0002` creates Workspace/member/invitation/activity/notification
tables with named constraints and indexes and reverses them in dependency order.
Tests apply the chain from empty, inspect constraints, downgrade one revision, and
re-upgrade.

Routes remain thin and use standard envelopes, safe domain errors, complete OpenAPI
metadata, and generated TypeScript schema. Integration tests cover the permission
matrix, IDOR-safe `404`, atomic rollback, ownership, invitations, side effects, and
pagination.

## Risks / Trade-offs

- [Concurrent duplicate membership/invitation] → named unique constraints plus
  service conflict translation.
- [Two owners during transfer] → explicit owner and membership changes in one write
  transaction with post-commit invariant tests.
- [Early engagement tables constrain later phases] → keep fields minimal but aligned
  with the stable architecture/PRD model and extend through later migrations.
- [Sensitive invitation data leaks] → raw token returned once only to authorized
  creator; hashes excluded from schemas/logs.

## Migration Plan

1. Add models and reversible migration; verify empty-chain and one-step rollback.
2. Add repositories, role helpers, service transactions, and side-effect writes.
3. Add dependencies/schemas/routes and focused permission/invitation tests.
4. Run HTTP/OpenAPI/client-generation and exact quality gates.
5. Update documentation/changelog, sync the capability, and archive Phase 2.

Rollback removes Phase 2 routes and downgrades `20260729_0002` only on an explicitly
approved database; all Workspace and related engagement data is deleted.
