## ADDED Requirements

### Requirement: Every backend operation has a reachable frontend workflow
The frontend SHALL expose a permission-aware workflow for every PRD 1.1 product operation, including archive restoration, reordering, invitation acceptance, editing and binary retrieval.

#### Scenario: Owner completes administration
- **WHEN** an owner opens workspace or project settings
- **THEN** all permitted member, invitation, archive, restore, reorder and deletion operations are reachable
- **AND** successful mutations reconcile all dependent views

### Requirement: Deep links survive authentication
Invitation and notification links SHALL preserve their target through session bootstrap and continue after authentication.

#### Scenario: Anonymous invite recipient opens a link
- **WHEN** an anonymous user opens an invitation URL
- **THEN** the application requests authentication
- **AND** accepts the invitation after the matching account authenticates

### Requirement: Human identity and persisted media are displayed
Member lists SHALL show backend-provided names/emails and the profile SHALL display the persisted authenticated avatar when present.

#### Scenario: Uploaded avatar survives reload
- **WHEN** a user uploads a valid avatar and reloads
- **THEN** the frontend retrieves the authenticated avatar endpoint and displays it

### Requirement: Board and timeline interactions are data-correct
Board drag/drop SHALL persist through the versioned move endpoint with rollback, and timeline geometry SHALL derive from UTC task dates within the selected range.

#### Scenario: Task is dragged between columns
- **WHEN** an authorized user drags a task card onto another column
- **THEN** the interface updates optimistically
- **AND** the persisted task remains in the target column after reload
