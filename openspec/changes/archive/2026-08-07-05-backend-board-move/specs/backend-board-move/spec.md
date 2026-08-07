## Purpose

Allow authorized project users to persist a board task reorder or column transition
atomically while safely rejecting stale concurrent changes.

## ADDED Requirements

### Requirement: Board moves are atomic and versioned
The system SHALL accept `target_column_id`, `target_index`, and Task `version` for
an authorized active Task move. It SHALL validate target membership and index,
normalize affected source and target positions in one transaction, increment the
Task version, and return the final persisted Task.

#### Scenario: Move within or across columns
- **WHEN** an authorized user submits the current Task version and a valid target position
- **THEN** the Task and every affected position are persisted atomically and remain ordered after refresh

#### Scenario: Stale move is rejected
- **WHEN** a request contains a stale Task version
- **THEN** the API returns `409 version_conflict` and changes no Task position or completion state

### Requirement: Board moves synchronize completion safely
The system SHALL set `completed_at` when a Task enters an active done column and
clear it when it leaves a done column. Unauthorized, archived, inaccessible, or
invalid target moves SHALL not reveal protected resources or create partial changes.

#### Scenario: Move to and from done
- **WHEN** an authorized user moves a Task into a done column and then back to an active non-done column
- **THEN** `completed_at` is set and then cleared in the returned persisted Task
