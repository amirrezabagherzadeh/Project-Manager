## ADDED Requirements

### Requirement: Complete session lifecycle
The frontend SHALL provide register, login, refresh bootstrap, current identity, private route guarding and logout against the real authentication API.

#### Scenario: Reload restores a session
- **WHEN** an authenticated user reloads the application
- **THEN** one refresh request restores an in-memory access token
- **AND** protected content remains guarded until identity resolves

### Requirement: Permission-aware workspace and project administration
The frontend SHALL expose workspace/project CRUD, archive/restore, members, roles, invitations, columns and settings while respecting current membership roles.

#### Scenario: Read-only member opens settings
- **WHEN** a member without management permission opens a settings surface
- **THEN** management controls are unavailable
- **AND** any backend `403` is rendered as a permission state

### Requirement: Complete task and collaboration workflow
The frontend SHALL expose task creation, detail, update, move, archive/restore, subtasks, labels, assignees, comments, checklists, attachments and activity through real endpoints.

#### Scenario: User collaborates in task detail
- **WHEN** an authorized user edits fields, comments, adds checklist items or uploads an attachment
- **THEN** the corresponding backend mutation is invoked
- **AND** focused task and board caches reconcile to server responses

### Requirement: Shared-data project views
Board, List, Timeline and Calendar SHALL represent the same project tasks; dashboard and activity SHALL use backend reporting endpoints.

#### Scenario: View changes
- **WHEN** a user switches the active project view
- **THEN** the URL reflects that view
- **AND** no permanent mock dataset is substituted for backend task data

### Requirement: Notifications and profile
The frontend SHALL expose notification list/count/read operations and profile name, timezone and avatar operations.

#### Scenario: Notification is read
- **WHEN** a user marks a notification read
- **THEN** notification data and unread badge are refreshed

### Requirement: Trello-derived Persian responsive interface
The application SHALL use a compact dark workspace shell, horizontal board lists and two-pane task detail inspired by supplied references while retaining independent branding, Persian text and RTL behavior.

#### Scenario: Responsive task detail
- **WHEN** task detail opens on desktop or mobile
- **THEN** focus is contained and restorable
- **AND** content/activity remain usable in two panes or a full-screen mobile layout
