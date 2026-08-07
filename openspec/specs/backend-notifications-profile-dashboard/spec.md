# backend-notifications-profile-dashboard Specification

## Purpose
Expose safe, personal notifications, profile controls, and cross-project summaries.
## Requirements
### Requirement: Notifications are user-scoped and mutable
The system SHALL list, count, mark read, and mark all read only for the current user.

#### Scenario: Foreign notification mutation
- **WHEN** a user marks another user's notification read
- **THEN** the API returns an enumeration-safe denial

### Requirement: Profile supports safe avatar lifecycle
The system SHALL let a user update name/timezone and upload/delete a validated avatar
without exposing storage paths.

#### Scenario: Avatar replacement
- **WHEN** a user replaces an avatar
- **THEN** the old local file is cleaned up after persistence succeeds

### Requirement: Global dashboard is visibility-scoped
The system SHALL return only projects and Tasks accessible to the current user.

#### Scenario: Global dashboard request
- **WHEN** a user requests their dashboard
- **THEN** aggregates omit inaccessible workspace data

