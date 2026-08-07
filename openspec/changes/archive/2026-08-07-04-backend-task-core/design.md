## Context

See proposal.md and backend-task-core spec. Phase 3 supplies Projects, membership,
and active columns, but no Task tables or route module exists. Phase 5 owns all
atomic changes of a Task's column position and optimistic conflict response.

## Goals / Non-Goals

**Goals:**

- Add PostgreSQL-portable Task, relationship, and Label schema through Alembic.
- Preserve API → service → repository boundaries and resource-level project access.
- Make query behavior bounded and detail loading intentional.

**Non-Goals:**

- Board move/reorder, checklist/comment/attachment/activity timelines, notification
  delivery, reporting, profile features, or frontend feature work.

## Decisions

### Task schema and completion

Task stores a project ID, column ID, parent ID, priority, due/completion/archive
timestamps, integer position/version, and explicit indexes. Many-to-many assignees
and labels use constrained association tables; `parent_id` is validated by the
service as same project because portable SQL constraints cannot express it. A done
column determines completion and Phase 4 creates Tasks in a requested active column
without offering column mutation. This keeps Phase 5 as the sole owner of move
transaction semantics.

Alternative rejected: deriving completion only at response time. Persisting
`completed_at` provides stable reporting and audit behavior after Phase 5 sync.

### Service authorization and transactions

Routes parse schemas and serialize envelopes. The TaskService resolves Project,
Workspace membership, private-project access, active status, and mutation role
inside short `AsyncSession.begin()` transactions. Repositories own select builders,
allowlisted sorting, counts, `selectinload`, and flushes but do not commit.

Alternative rejected: filtering permissions in the route or trusting a client
project ID; both permit IDOR and break the established architecture.

### Query contract and public types

The list endpoint constructs SQL only from typed filters and a static sort mapping;
task detail uses targeted select-in loading, while list data omits deep graphs.
Every route declares documented errors/models and regenerates the OpenAPI client.

## Risks / Trade-offs

- [Cross-project references] → service ownership checks plus FK/index constraints and rollback tests.
- [N+1 detail/list expansion] → separate list/detail repository paths and query-count tests.
- [SQLite concurrent writes] → one short service transaction and no move/reorder in this phase.
- [Completion semantics change in Phase 5] → version/position fields are introduced now; only Phase 5 mutates positions.

## Migration Plan

1. Add the Phase 4 Alembic revision after `20260729_0003` with explicit upgrade and downgrade.
2. Upgrade an empty disposable database; test constraints and downgrade/re-upgrade.
3. Deploy the API and regenerate `frontend/src/lib/api/schema.d.ts` from its OpenAPI.
4. Roll back only against a disposable database with the revision downgrade; it removes Phase 4 Task data and tables.
