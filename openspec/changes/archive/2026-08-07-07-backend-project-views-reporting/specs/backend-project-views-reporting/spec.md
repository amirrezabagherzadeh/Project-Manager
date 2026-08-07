## Purpose

Provide permission-scoped, bounded project reporting views over canonical Task data.

## ADDED Requirements

### Requirement: Project dashboard returns accurate aggregates
The system SHALL return authorized project metrics for completion, overdue,
due-soon, unassigned, column, priority, and assignee groups, including zero totals.

#### Scenario: Empty project dashboard
- **WHEN** an authorized user requests a project with no Tasks
- **THEN** every aggregate is zero and the response is successful

### Requirement: Timeline and calendar are range-scoped
The system SHALL return only authorized project Tasks whose relevant timestamps are
within the supplied UTC range, using bounded pagination.

#### Scenario: Unauthorized reporting request
- **WHEN** a user without project access requests a view
- **THEN** the API returns an enumeration-safe denial

### Requirement: Recent project activity is safe
The system SHALL return a bounded recent activity feed without sensitive metadata.

#### Scenario: Activity request
- **WHEN** an authorized user requests project activity
- **THEN** actions are ordered newest first and storage paths are absent
