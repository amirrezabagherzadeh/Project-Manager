## Purpose

Provide a secure tenant boundary with atomic ownership, role-based membership,
invitation acceptance, and durable collaboration side effects.

## ADDED Requirements

### Requirement: Workspace creation is atomic
An authenticated user SHALL be able to create a Workspace, and the API SHALL create
exactly one OWNER membership for that creator in the same transaction.

#### Scenario: Workspace creation succeeds
- **GIVEN** an authenticated user and valid name and description
- **WHEN** the user posts to `/api/v1/workspaces`
- **THEN** the API returns `201` with the Workspace and creator OWNER membership
- **AND** the Workspace, membership, and creation activity commit atomically

#### Scenario: Workspace input is invalid
- **GIVEN** a blank or oversized Workspace name
- **WHEN** creation is requested
- **THEN** the API returns `422 validation_error` and persists no partial records

#### Scenario: Workspace creation is unauthenticated
- **GIVEN** no valid access token
- **WHEN** Workspace creation is requested
- **THEN** the API returns `401 authentication_required`

### Requirement: Workspace lifecycle is member scoped
The API SHALL list only Workspaces in which the current user is a member, SHALL allow
members to read their Workspace, SHALL allow OWNER/ADMIN to update/archive/restore,
and SHALL allow only OWNER to delete.

#### Scenario: Member lists and reads Workspaces
- **GIVEN** a user belongs to one of multiple Workspaces
- **WHEN** the user lists or reads Workspaces
- **THEN** only authorized Workspace data is returned with bounded pagination

#### Scenario: Member attempts administrative lifecycle action
- **GIVEN** a MEMBER or PROJECT_MANAGER membership
- **WHEN** update, archive, restore, or delete is requested
- **THEN** the API returns `403 permission_denied`

#### Scenario: Non-member requests a Workspace
- **GIVEN** an authenticated user has no membership in the requested Workspace
- **WHEN** the resource is read or mutated
- **THEN** the API returns enumeration-safe `404 resource_not_found`

#### Scenario: Admin attempts deletion
- **GIVEN** an ADMIN membership
- **WHEN** permanent Workspace deletion is requested
- **THEN** the API returns `403 permission_denied`

### Requirement: Workspace roles are enforced
Workspace roles SHALL be OWNER, ADMIN, PROJECT_MANAGER, and MEMBER; permissions SHALL
be enforced by backend dependencies and rechecked by services for each resource.

#### Scenario: Admin manages non-owner membership
- **GIVEN** an ADMIN and a non-owner target membership
- **WHEN** the admin adds, changes, or removes the target within allowed roles
- **THEN** the mutation succeeds atomically

#### Scenario: Member attempts role management
- **GIVEN** a MEMBER
- **WHEN** the member attempts to add, change, or remove another membership
- **THEN** the API returns `403 permission_denied`

#### Scenario: Admin attempts owner mutation
- **GIVEN** an ADMIN
- **WHEN** the admin attempts to change/remove OWNER or assign OWNER
- **THEN** the API returns `403 permission_denied`

### Requirement: Membership and ownership invariants
The API SHALL add only existing users as direct members, SHALL reject duplicate
membership, and SHALL preserve exactly one OWNER through atomic ownership transfer.

#### Scenario: Existing user is added
- **GIVEN** OWNER/ADMIN supplies an existing user's email and a non-owner role
- **WHEN** member creation is requested
- **THEN** the API returns `201`, records activity, and notifies the added user unless actor and target are the same

#### Scenario: Direct member email is unknown
- **GIVEN** no user exists for the supplied email
- **WHEN** direct member creation is requested
- **THEN** the API returns `404 resource_not_found` without disclosing unrelated account data

#### Scenario: Membership is duplicated
- **GIVEN** the user already belongs to the Workspace
- **WHEN** the user is added again
- **THEN** the API returns `409 resource_conflict`

#### Scenario: Owner transfers ownership
- **GIVEN** OWNER selects an existing non-owner Workspace member
- **WHEN** that member's role is changed to OWNER
- **THEN** the target becomes OWNER, the prior owner becomes ADMIN, and `owner_id` changes in one transaction

#### Scenario: Owner is removed without transfer
- **GIVEN** a target membership is the current OWNER
- **WHEN** removal or a non-transfer demotion is requested
- **THEN** the API returns `409 invalid_operation`

### Requirement: Invitations are secure and atomic
OWNER/ADMIN SHALL be able to create, list, and revoke invitations for normalized
emails and non-owner roles; a matching authenticated user SHALL accept a valid,
unexpired, unrevoked invitation exactly once.

#### Scenario: Invitation is created
- **GIVEN** an authorized actor supplies an email not already represented by a member
- **WHEN** invitation creation is requested
- **THEN** the API returns `201` with public metadata and the raw acceptance token once
- **AND** only the token hash is stored

#### Scenario: Invitation conflicts
- **GIVEN** an active invitation or membership already exists for the normalized email
- **WHEN** another invitation is requested
- **THEN** the API returns `409 resource_conflict`

#### Scenario: Matching user accepts invitation
- **GIVEN** the authenticated user's email matches a valid invitation token
- **WHEN** `/api/v1/invitations/{token}/accept` is requested
- **THEN** membership creation, invitation acceptance, activity, and notification commit atomically

#### Scenario: Invitation cannot be accepted
- **GIVEN** the token is unknown, expired, revoked, accepted, or belongs to another email
- **WHEN** acceptance is requested
- **THEN** the API returns a safe `404` or `409` and creates no membership

### Requirement: Workspace side effects are durable and private
Successful Workspace, membership, ownership, and invitation mutations SHALL create
durable activity records; membership notifications SHALL suppress self-notification,
and neither record SHALL expose credentials or token hashes.

#### Scenario: Compound mutation fails
- **GIVEN** a Workspace mutation has staged domain and side-effect records
- **WHEN** any required write fails
- **THEN** the Workspace mutation, activity, and notification all roll back

#### Scenario: Side effects are inspected
- **GIVEN** successful membership and invitation flows
- **WHEN** stored activity/notification and public responses are inspected
- **THEN** they contain navigation metadata but no access, refresh, password, or invitation token hash

### Requirement: Workspace OpenAPI contract is complete
Every Workspace, member, and invitation operation SHALL declare summaries,
descriptions, tags, response models/statuses, important errors, and examples; list
responses SHALL use page/page_size/total with defaults 20 and maximum 100.

#### Scenario: Developer inspects Workspace Swagger operations
- **GIVEN** documentation is enabled
- **WHEN** the OpenAPI document is inspected
- **THEN** all Phase 2 operations and security requirements are present without private fields

#### Scenario: Frontend contract is regenerated
- **GIVEN** the Phase 2 API is running
- **WHEN** the API generation command runs
- **THEN** the committed TypeScript schema includes Phase 2 contracts without unexplained drift

