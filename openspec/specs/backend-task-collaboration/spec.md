# backend-task-collaboration Specification

## Purpose
Provide resource-authorized task collaboration through checklists, comments,
attachments, and an activity history without exposing files or records across projects.
## Requirements
### Requirement: Task checklists and items are ordered and measurable
The system SHALL let authorized project users create, update, delete, and reorder
Task checklists/items and SHALL return completion progress based on completed items.

#### Scenario: Complete checklist work
- **WHEN** an authorized user completes a checklist item
- **THEN** the Task checklist response reports correct completed and total counts

### Requirement: Comments enforce author ownership
The system SHALL allow an authorized user to create a Task comment and only its
author or an authorized project manager to edit or delete it.

#### Scenario: Another member edits a comment
- **WHEN** a non-author member without management permission edits a comment
- **THEN** the API returns permission_denied and preserves the original body

### Requirement: Attachments are validated and permission-scoped
The system SHALL accept allowed multipart attachments up to 10MB, store them under
a generated server filename outside public paths, and allow download/delete only to
authorized task users. Unsupported MIME, oversize, and traversal attempts SHALL fail safely.

#### Scenario: Unauthorized attachment download
- **WHEN** a user without Task access downloads an attachment
- **THEN** the API returns an enumeration-safe denial and does not expose file bytes

### Requirement: Task activity is retrievable
The system SHALL record and return a bounded task activity timeline for relevant
collaboration mutations without logging sensitive file content.

#### Scenario: Review activity
- **WHEN** an authorized user requests a Task activity timeline
- **THEN** the API returns ordered public actions without sensitive storage paths

