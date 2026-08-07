## Why

Backend PRD 1.1 is implemented across authentication, RBAC, project/task management, collaboration, reporting, notifications and profile, while the frontend exposes only demo login and a minimal board. Users need the complete Persian RTL product surface and every usable backend capability needs a permission-aware frontend path.

## What Changes

- Expand PRD 1.2 with an explicit endpoint-to-UI coverage matrix and Trello-derived visual direction.
- Replace demo-only entry with registration, login, refresh bootstrap, identity, route guard and logout.
- Add a Trello-like application shell, workspace/project navigation, settings and member/invitation management.
- Add task detail editing, labels, assignees, archive, comments, checklists, attachments and activity.
- Add Board, List, Timeline, Calendar, project/global dashboards, notifications and profile/timezone/avatar.
- Centralize authenticated API calls with single-flight refresh and generated OpenAPI types.
- Add permission-aware controls, error states, responsive/keyboard behavior and live backend validation.

## Impact

- Affected frontend: app entry, API client, product components, centralized Persian messages, styles and tests.
- Affected documentation: PRD 1.2, OpenSpec design/spec/tasks and changelog.
- Backend API shapes remain unchanged; only already-documented PRD 1.1 endpoints are consumed.
