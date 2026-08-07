## Purpose

Provide authorized users with a secure, queryable task core for project work while
keeping atomic board movement and collaboration workflows in later delivery phases.

## ADDED Requirements

### Requirement: Authorized project users can manage task lifecycle
The system SHALL let an authorized project user create, read, update, archive, and
restore Tasks in an active project. A Task SHALL have a title, project, active
board column, priority, UTC timestamps, version, optional description/due date,
and optional same-project parent Task. Archive SHALL preserve the Task and
restore SHALL make it queryable again. Creating or changing a Task to a different
column is reserved for the Phase 5 move contract.

#### Scenario: Create and archive a task
- **WHEN** an authorized project user creates a valid Task in an active project and later archives it
- **THEN** the API returns the public Task, excludes it from the default list, and restores it on request

#### Scenario: Invalid or inaccessible task mutation
- **WHEN** an unauthenticated user, unauthorized user, or malformed request attempts a task mutation
- **THEN** the API returns the standard 401, enumeration-safe 404/403, or validation error envelope without changing data

### Requirement: Tasks support project-scoped assignments, labels, and subtasks
The system SHALL allow authorized project users to add and remove project members
as Task assignees, create/update/archive project Labels, attach/detach Labels to
Tasks, and create same-project subtasks. It SHALL reject duplicate relationships,
cross-project users, labels, columns, or parent Tasks with stable conflict or
validation responses.

#### Scenario: Associate project resources with a task
- **WHEN** an authorized user assigns a project member and adds a project Label to a Task
- **THEN** Task detail returns those public associations without exposing sensitive user fields

#### Scenario: Reject cross-project relationship
- **WHEN** a client associates a user, Label, or parent Task belonging to another project
- **THEN** the API rejects the request and persists no partial association

### Requirement: Task queries are bounded, allowlisted, and permission-scoped
The system SHALL list only Tasks visible to the caller using page-based pagination
with default 20 and maximum 100. It SHALL support bounded search and explicit
filters for column, assignee, label, priority, due range, overdue, completion,
parent, and unassigned state, and only allow sorts by created_at, updated_at,
due_at, priority, title, or position. Completion SHALL reflect membership in a
done column and overdue SHALL mean a past due date on an incomplete Task.

#### Scenario: Filter and paginate visible tasks
- **WHEN** a project user requests a valid filtered and sorted Task list
- **THEN** the API returns the requested page, total, and only matching authorized Tasks in deterministic order

#### Scenario: Reject an unsafe sort field
- **WHEN** a client supplies a sort field or direction outside the documented allowlist
- **THEN** the API returns validation_error and does not interpolate the value into a database query

### Requirement: Task detail avoids unbounded query loading
The system SHALL return concise Task data in lists and intentionally eager-load
the associations required by Task detail to prevent per-item query amplification.

#### Scenario: Read task detail
- **WHEN** an authorized project user retrieves a Task detail resource
- **THEN** the public response includes its column, assignees, labels, and parent/subtask metadata with bounded database loading
