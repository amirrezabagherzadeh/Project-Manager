# backend-project-board-foundation Specification

## Purpose
Provide project-scoped work partitioning with atomic creator-manager membership, five
default board columns, private-project access control, and column ordering under
workspace authorization.
## Requirements
### Requirement: Project creation is atomic
An authenticated workspace OWNER, ADMIN, or PROJECT_MANAGER SHALL be able to create a
Project in a workspace, and the API SHALL create the Project, the creator as `manager`
ProjectMember, five default BoardColumns, and creation activity in one transaction.

#### Scenario: Project creation succeeds
- **GIVEN** an authenticated workspace OWNER/ADMIN/PROJECT_MANAGER and valid name and key
- **WHEN** the user posts to `/api/v1/workspaces/{workspace_id}/projects`
- **THEN** the API returns `201` with the Project, a `manager` membership for the creator,
  and exactly five default columns `backlog`, `todo`, `doing`, `review`, `done`
- **AND** only the `done` column has `is_done=true`
- **AND** the Project, membership, columns, and activity commit atomically

#### Scenario: Project input is invalid
- **GIVEN** a blank or oversized name, blank key, or invalid key format
- **WHEN** creation is requested
- **THEN** the API returns `422 validation_error` and persists no partial records

#### Scenario: Project creation is unauthenticated
- **GIVEN** no valid access token
- **WHEN** Project creation is requested
- **THEN** the API returns `401 authentication_required`

#### Scenario: Workspace Member creates a Project
- **GIVEN** a workspace MEMBER without PROJECT_MANAGER role
- **WHEN** Project creation is requested
- **THEN** the API returns `403 permission_denied`

### Requirement: Project keys are workspace-unique
A Project key SHALL be unique within its workspace, and duplicate keys SHALL be rejected
without leaking unrelated project existence.

#### Scenario: Duplicate key is rejected
- **GIVEN** a Project already exists with key `PM` in a workspace
- **WHEN** another Project with key `PM` is created in the same workspace
- **THEN** the API returns `409 resource_conflict` and persists no duplicate

#### Scenario: Same key in different workspaces is allowed
- **GIVEN** two distinct workspaces each have a Project with key `PM`
- **WHEN** the projects are listed
- **THEN** both coexist without conflict

### Requirement: Project lifecycle is permission scoped
The API SHALL list only Projects a user may access, SHALL allow workspace members to read
non-private Projects, SHALL allow OWNER/ADMIN/PROJECT_MANAGER to update/archive/restore,
and SHALL enforce private-project access in the backend.

#### Scenario: Workspace member reads a public Project
- **GIVEN** a workspace member and a non-private Project they are not a project member of
- **WHEN** the member reads the Project
- **THEN** the API returns the Project data

#### Scenario: Workspace member cannot read a private Project
- **GIVEN** a workspace member who is not a ProjectMember of a private Project
- **WHEN** the member reads or mutates the Project
- **THEN** the API returns enumeration-safe `404 resource_not_found`

#### Scenario: Project manager updates their Project
- **GIVEN** a PROJECT_MANAGER who created the Project or is a `manager` member
- **WHEN** update, archive, or restore is requested
- **THEN** the mutation succeeds atomically with activity recorded

#### Scenario: Workspace Member attempts administrative action
- **GIVEN** a workspace MEMBER
- **WHEN** update, archive, or restore is requested
- **THEN** the API returns `403 permission_denied`

#### Scenario: Non-member requests a Project
- **GIVEN** an authenticated user has no workspace membership in the owning workspace
- **WHEN** the Project is read or mutated
- **THEN** the API returns enumeration-safe `404 resource_not_found`

### Requirement: Project membership is controlled
Project membership SHALL have `manager` and `member` roles, SHALL accept only existing
workspace members as project members, SHALL reject duplicate project membership, and
SHALL be managed by OWNER/ADMIN/PROJECT_MANAGER.

#### Scenario: Existing workspace member is added
- **GIVEN** an authorized actor and an existing workspace member's user id
- **WHEN** project member creation is requested
- **THEN** the API returns `201`, records activity, and notifies the added user unless actor
  and target are the same

#### Scenario: Non-workspace member is added
- **GIVEN** the target user is not a workspace member
- **WHEN** project member creation is requested
- **THEN** the API returns `404 resource_not_found` without disclosing unrelated account data

#### Scenario: Project membership is duplicated
- **GIVEN** the user already belongs to the Project
- **WHEN** the user is added again
- **THEN** the API returns `409 resource_conflict`

#### Scenario: Workspace Member manages project membership
- **GIVEN** a workspace MEMBER who is not a project `manager`
- **WHEN** the member attempts to add, change, or remove a project member
- **THEN** the API returns `403 permission_denied`

### Requirement: Board columns are created and ordered atomically
Project creation SHALL create exactly five default columns with explicit positions; the
API SHALL allow OWNER/ADMIN/PROJECT_MANAGER to create, archive, reorder, and update
columns, and SHALL preserve gap-free ordering through atomic position normalization.

#### Scenario: Default columns exist
- **GIVEN** a newly created Project
- **WHEN** the columns are listed
- **THEN** exactly `backlog`, `todo`, `doing`, `review`, `done` columns exist in that order
  with only `done` marked `is_done=true`

#### Scenario: Column is created
- **GIVEN** an authorized actor
- **WHEN** a new column is created on a non-archived Project
- **THEN** the API returns `201` with the column appended at the next position

#### Scenario: Columns are reordered
- **GIVEN** an authorized actor supplies a full ordered list of active column ids
- **WHEN** the reorder endpoint is called
- **THEN** the API rewrites positions atomically so the stored order matches the request

#### Scenario: Reorder is rejected for invalid input
- **GIVEN** a reorder request missing a column, adding a foreign column, archiving one, or
  duplicating an id
- **WHEN** the reorder endpoint is called
- **THEN** the API returns `409`/`422` and leaves all positions unchanged

#### Scenario: Unauthorized column mutation
- **GIVEN** a workspace MEMBER who is not a project `manager`
- **WHEN** create, update, archive, or reorder is requested
- **THEN** the API returns `403 permission_denied`

### Requirement: Archive is preferred over delete
Project and BoardColumn mutations SHALL archive rather than destructively delete; archived
Projects SHALL be restorable by an authorized actor and SHALL be excluded from active lists.

#### Scenario: Project is archived and restored
- **GIVEN** an authorized actor
- **WHEN** archive then restore is requested
- **THEN** `archived_at` is set and cleared, the Project is excluded from then returned to
  active lists, and no child rows are lost

#### Scenario: Column is archived
- **GIVEN** an authorized actor
- **WHEN** a column is archived
- **THEN** the column is excluded from active column lists and `archived_at` is set

#### Scenario: Archived Project is excluded
- **GIVEN** a workspace member listing projects
- **WHEN** an archived Project exists
- **THEN** the archived Project is not included unless archived state is explicitly requested

### Requirement: Project side effects are durable and private
Successful Project, membership, and column mutations SHALL create durable activity records;
membership notifications SHALL suppress self-notification, and no record or public response
SHALL expose credentials or token hashes.

#### Scenario: Compound mutation fails
- **GIVEN** a Project mutation has staged domain and side-effect records
- **WHEN** any required write fails
- **THEN** the Project mutation, activity, and notification all roll back

#### Scenario: Side effects are inspected
- **GIVEN** successful project membership and column flows
- **WHEN** stored activity/notification and public responses are inspected
- **THEN** they contain navigation metadata but no access, refresh, password, or invitation
  token hash

### Requirement: Project OpenAPI contract is complete
Every Project, member, and column operation SHALL declare summaries, descriptions, tags,
response models/statuses, important errors, and examples; list responses SHALL use
page/page_size/total with defaults 20 and maximum 100.

#### Scenario: Developer inspects Project Swagger operations
- **GIVEN** documentation is enabled
- **WHEN** the OpenAPI document is inspected
- **THEN** all Phase 3 operations and security requirements are present without private fields

#### Scenario: Frontend contract is regenerated
- **GIVEN** the Phase 3 API is running
- **WHEN** the API generation command runs
- **THEN** the committed TypeScript schema includes Phase 3 contracts without unexplained drift

