## Architecture

`ProductApp` owns navigation selection and renders feature-focused surfaces. TanStack Query owns server state. A typed API module aliases generated OpenAPI schemas and exposes authenticated request primitives plus domain methods. Access tokens stay in memory; refresh cookies use `credentials: include`; refresh is single-flight and retries a failed authenticated request once.

The session state machine is `bootstrapping → anonymous | authenticated`. Private product surfaces never render before bootstrap completes. Logout clears the in-memory token and query cache. Errors are normalized from the backend envelope and `401`, `403`, `404`, `409` receive distinct Persian states.

## Product shell and navigation

The desktop shell follows the supplied Trello references: compact global topbar, right-side workspace rail for RTL, project canvas, project view tabs and horizontal board lists. Mobile collapses the rail and turns task detail into a full viewport dialog. View selection and selected task are reflected in query parameters.

## Permission model

The UI derives `canManageWorkspace`, `canManageProject` and `canWriteTasks` from current workspace/project membership. Controls are removed or disabled for read-only roles, while backend `403` remains authoritative. Archive is preferred over destructive delete.

## Data strategy

- Independent shell resources load in parallel with Query observers.
- Query keys follow PRD 1.2 and mutations invalidate the narrowest affected domain.
- Board moves snapshot and optimistically update task position/column, rollback on failure and refetch on `409`.
- Notifications poll every 30 seconds only while the document is visible.
- Timeline/calendar/dashboard consume backend reporting endpoints and never derive timezone-sensitive buckets from formatted Persian strings.

## Visual system

The design is a dark, dense operations desk: graphite chrome, deep blue project canvas, compact ink cards, sky action accent and warm status colors. It borrows Trello’s hierarchy and density, not its brand assets. Persian Vazirmatn typography, RTL order, visible focus, reduced motion and responsive detail panels are first-class constraints.

## Known constraints

Backend member payloads expose IDs and roles but not embedded user names; member administration displays stable IDs where a name lookup contract is unavailable. Timeline is read-only in MVP. Native drag-and-drop remains supplemented by an explicit move menu for accessibility and conflict recovery.
