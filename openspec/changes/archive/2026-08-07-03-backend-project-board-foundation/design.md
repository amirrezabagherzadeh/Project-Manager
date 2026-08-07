## Context

See `proposal.md` and the Phase 3 delta specification. Phase 2 provides authenticated
Users, workspace RBAC with OWNER/ADMIN/PROJECT_MANAGER/MEMBER roles, shared
`ActivityLog`/`Notification` tables, request-scoped async sessions, service-owned
transactions, safe errors, and UUID/UTC conventions. Phase 3 is the first project-scoped
resource boundary and must be stable before Tasks exist in Phase 4.

## Goals / Non-Goals

**Goals:**

- Centralize project-scoped permission semantics and enumeration-safe project lookup.
- Keep compound Project/member/column writes and side effects atomic.
- Establish the board column foundation (positions, `is_done`, default five) that Phase 4
  Tasks attach to and Phase 5 moves reorder.
- Enforce private-project access in the backend so UI visibility is not authorization.

**Non-Goals:**

- Task models, assignment, labels, subtasks, or move/version behavior (Phases 4 and 5).
- Project overview/dashboard/timeline/calendar aggregate metrics (Phase 7); Phase 3
  exposes only the Project, member, and column resources named by UC-04/UC-05.
- Notification list/read endpoints or activity timeline endpoints (later phases).
- Ownership transfer or deletion for Projects; archive/restore is the lifecycle primitive.

## Decisions

### Data model and creator-manager invariant

`Project` has UUID id, workspace foreign key, name, workspace-unique `key`, description,
`is_private` flag, color, start/due dates, archive and UTC timestamps with the
`project(workspace_id,key)` unique constraint and `workspace_id`/`archived_at` indexes.
`ProjectMember` has UUID id, project/user foreign keys, `manager`/`member` enum role and
joined timestamp with unique `(project_id,user_id)`. `BoardColumn` has UUID id, project
foreign key, name, integer `position`, `is_done` flag, `archived_at`, and UTC timestamps
with a `(project_id,position)` partial ordering over active columns and a
`(project_id,name)` uniqueness consideration.

The service creates Project, the creator as `manager` ProjectMember, the five default
columns, and activity in one transaction. A non-`PROJECT_MANAGER` workspace MEMBER cannot
create a Project. The creator is always a `manager`; there is no self-removal safeguard
beyond Phase 2's workspace membership continuity requirement.

Alternative rejected: infer manager from a workspace role only. An explicit ProjectMember
makes private-project access and later Phase 4 task assignment auditable independent of
workspace role.

### Default columns

The five default columns are created with fixed slugs/names `backlog`, `todo`, `doing`,
`review`, `done` at positions 0–4; only `done` has `is_done=true`. Column names are
user-editable afterwards; the `is_done` flag is editable so a workspace can later mark a
custom column as done, but the default seed is fixed.

### Private-project access

`Project.is_private` defaults to `false`. When `true`, only `ProjectMember` rows for that
project (plus workspace OWNER/ADMIN, who always act within their workspace authority) may
read or mutate the Project and its children. A workspace MEMBER without a ProjectMember
row receives enumeration-safe `404` for private Projects and their columns/members; for
public Projects they may read but still need `manager` role or workspace
PROJECT_MANAGER/ADMIN/OWNER to mutate.

Authorization flow is current user → workspace membership/role (Phase 2 dependency) →
project membership/private gate (Phase 3) → mutation role check (Phase 3). Services
recheck permissions even when a dependency has loaded membership.

Alternative rejected: rely on workspace role alone for project access. That would violate
UC-04's private-project acceptance and the AGENTS.md resource-level authorization rule.

### Repository and query boundaries

Repositories own scoped selects, eager loading, pagination, workspace-unique key lookup,
active/archived filters, and CRUD/flush primitives; they never commit or decide role
policy. Lists default to 20 and cap at 100. Column reorder is a single service-owned
transaction that rewrites `position` for all active columns of the project. Services own
transactions and conflict/IntegrityError translation.

### Column reorder contract

Reorder takes a full ordered list of active column ids for the project. The service
validates that the set matches the project's active columns exactly (no missing, extra,
foreign, archived, or duplicate ids), then assigns positions 0..N-1 in request order in
one flush. Invalid input returns `409`/`422` and changes nothing. This keeps positions
gap-free and avoids the fractional-position drift that a partial reorder would introduce
under SQLite.

Alternative rejected: move-one-column with relative before/after. It is convenient but
ambiguous under concurrent reorders and harder to verify atomically; Phase 5 will handle
per-task move/reorder, but column order is a structural, low-frequency operation that
benefits from the full-list contract.

### Durable activity and notifications

Phase 3 reuses the Phase 2 `ActivityLog` and `Notification` tables. Activity records store
actor, workspace, project-scoped entity/action, safe JSON metadata, and timestamp.
Notifications fire for project membership addition and suppress self-notification. Column
mutations record activity without notifications (per the architecture doc's notification
event list). No Phase 3 public list endpoint for notifications/activity is added.

### Migration, API, and tests

Revision `20260729_0003` creates Project/member/column tables with named constraints and
indexes and reverses them in dependency order (columns, members, project). Tests apply the
chain from empty, inspect constraints, downgrade one revision, and re-upgrade. Application
startup never substitutes `create_all()` for migrations.

Routes remain thin and use standard success/error envelopes, safe domain errors, complete
OpenAPI metadata, and generated TypeScript schema. Endpoints follow the PRD path layout:
`/workspaces/{workspace_id}/projects`, `/projects/{project_id}`, project member and column
operations under `/projects/{project_id}/...` and `/columns/{column_id}`. Integration tests
cover the permission matrix, private-project IDOR-safe `404`, atomic rollback, reorder
validation, default columns, and pagination.

## Risks / Trade-offs

- [Concurrent duplicate project key] → named unique constraint plus service conflict
  translation.
- [Column position corruption] → full-list reorder contract with atomic position rewrite
  and reject-unchanged-on-invalid.
- [Private-project IDOR] → backend membership gate plus negative tests for read and every
  mutation.
- [Manager lock-out] → creator is always a `manager`; later phases may add safeguards, but
  workspace OWNER/ADMIN retain workspace authority over project mutations.
- [Early engagement reuse] → Phase 3 extends the Phase 2 engagement tables with
  project-scoped entity metadata only, avoiding a second engagement foundation.

## Migration Plan

1. Add Project/ProjectMember/BoardColumn models and reversible migration; verify
   empty-chain and one-step rollback.
2. Add repositories, project permission helpers, service transactions, and side-effect
   writes.
3. Add dependencies/schemas/routes and focused permission/private-access/reorder tests.
4. Run HTTP/OpenAPI/client-generation and exact quality gates.
5. Update documentation/changelog, sync the capability, and archive Phase 3.

Rollback removes Phase 3 routes and downgrades `20260729_0003` only on an explicitly
approved database; all Project, membership, column, and related engagement data is
deleted.
