## Why

The PRD 1.1 backend is broadly implemented, but the PRD 1.2 frontend still lacks reachable workflows for several existing operations. Three small backend read-contract gaps—archived workspace discovery, member identity, and avatar retrieval—also prevent complete frontend behavior.

## What Changes

- Complete invitation acceptance/deep links, archive discovery/restore, workspace deletion, member identity and notification navigation.
- Add accessible reorder controls, task drag-and-drop, edit flows, authenticated attachment download, persisted avatar display and date-accurate timeline rendering.
- Add guarded App Router entry routes and consistent mutation permission/error states.
- Extend backend reads only where required: `include_archived` for workspaces, nested public member identity, and authenticated current-avatar download.
- Expand automated tests across every completed domain and negative permission/session behavior.

## Impact

- Backend public response schemas gain member identity and a current-avatar read endpoint; workspace list gains an optional query parameter.
- Frontend API types are regenerated from OpenAPI and product routes/actions become fully reachable.
- Existing endpoint semantics and authorization remain backward compatible.
