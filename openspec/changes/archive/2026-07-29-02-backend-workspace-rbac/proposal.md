## Why

Authenticated users still have no tenant boundary, membership model, or enforceable
roles. Phase 2 delivers Backend PRD 1.1 BE-FR-03 and UC-02/UC-03 so later Projects
can rely on atomic Workspace ownership and resource-level authorization.

## What Changes

- Add Workspace, WorkspaceMember, and WorkspaceInvitation models and a reversible
  Alembic revision with UUID/UTC constraints and query indexes.
- Add Workspace CRUD/list/archive/restore/delete, member management, invitation
  creation/list/revoke/acceptance, and atomic ownership transfer.
- Enforce OWNER, ADMIN, PROJECT_MANAGER, and MEMBER permissions in dependencies and
  services, including enumeration-safe resource access and owner safeguards.
- Record Workspace/member/invitation activity transactionally and create
  self-suppressed membership notifications through minimal durable engagement
  records that later phases extend.
- Add full success, validation, `401`, `403`/safe `404`, `409`, expiry, rollback,
  migration, OpenAPI, and generated-client tests.

Goals:

- Satisfy BE-FR-03 and backend acceptance for UC-02 and UC-03.
- Create Workspace plus exactly one OWNER membership atomically.
- Make member/invitation mutations, ownership transfer, activity, and notification
  side effects atomic and backend-authorized.

Non-goals:

- Project-scoped roles or Project visibility, which belong to Phase 3.
- Notification listing/read endpoints or activity timelines, which belong to later
  phases; Phase 2 only persists the events required by UC-02/UC-03.
- Email delivery, guest accounts, SSO, or frontend Workspace UI.

Dependencies:

- Archived Phase 1 identity/session and database capabilities.

Risks and rollback:

- RBAC drift and IDOR are controlled by one permission matrix, service rechecks, and
  negative tests.
- Ownership mistakes are controlled by an explicit `owner_id`, one OWNER invariant,
  and atomic transfer tests.
- Rollback removes Phase 2 routes/modules and downgrades only an explicitly approved
  database; Workspace and engagement data are lost on downgrade.

## Capabilities

### New Capabilities

- `backend-workspace-rbac`: Workspace lifecycle, membership, roles, invitations,
  ownership safeguards, activity/notification side effects, and resource-level
  authorization (Backend PRD 1.1 BE-FR-03; UC-02 and UC-03).

### Modified Capabilities

None.

## Impact

- Backend Workspace/engagement models, schemas, repositories, services,
  dependencies, versioned endpoints, migrations, and tests.
- Public `/api/v1/workspaces`, `/api/v1/invitations/{token}/accept`, member and
  invitation operations.
- Generated `frontend/src/lib/api/schema.d.ts`, README, and changelog.
