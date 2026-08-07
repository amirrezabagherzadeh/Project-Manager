## 1. Contract and product design

- [x] 1.1 Audit all PRD 1.1 endpoints and add the mandatory frontend coverage matrix to PRD 1.2.
- [x] 1.2 Analyze supplied Trello workspace, board and task-detail references and document the independent RTL visual system.
- [x] 1.3 Replace the board-only proposal/design/spec with complete session, RBAC, task, reporting, notification and profile requirements.

## 2. Session and shell

- [x] 2.1 Implement typed authenticated client, single-flight refresh, identity bootstrap and normalized errors.
- [x] 2.2 Implement register/login/logout, private guard and Trello-style responsive application shell.

## 3. Workspace and project

- [x] 3.1 Implement workspace create/edit/archive/restore, member roles and invitation management.
- [x] 3.2 Implement project create/edit/archive/restore, member roles, columns and overview/settings.

## 4. Task and collaboration

- [x] 4.1 Implement Board/List task create, detail/edit/move/archive/restore, labels and assignees.
- [x] 4.2 Implement comments, checklists/items, attachments, subtasks and activity in two-pane task detail.

## 5. Views, reporting and account

- [x] 5.1 Implement Timeline, Calendar, project dashboard/activity and global dashboard.
- [x] 5.2 Implement notification bell/page/read flows and profile/timezone/avatar settings.
- [x] 5.3 Apply role-derived controls, loading/empty/error/permission states, RTL responsiveness and keyboard access.

## 6. Verification

- [x] 6.1 Regenerate OpenAPI types and run strict OpenSpec validation. (15 specifications passed.)
- [x] 6.2 Run frontend lint, 4 component tests, production build and 2 desktop/mobile Playwright critical flows.
- [x] 6.3 Run backend migrations/seed, 138 tests and live browser validation against the real database with no failed API response or console error.
