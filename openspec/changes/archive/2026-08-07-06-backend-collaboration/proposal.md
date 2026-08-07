## Why

Tasks need durable collaboration context beyond their core fields. Phase 6 delivers
the checklist, comment, attachment, and activity capabilities required by BE-FR-06
and UC-07 while keeping notification delivery in Phase 8.

## What Changes

- Add checklists/items with ordering and progress, task comments with ownership,
  task attachments through safe local storage, and task activity timeline queries.
- Add the corresponding migrations, permission-scoped REST operations, cleanup, and
  abuse/negative tests.

## Capabilities

### New Capabilities

- `backend-task-collaboration`: Authorized collaboration records and file handling for Tasks.

### Modified Capabilities

None.

## Impact

Adds collaboration models, a storage boundary, service/repository/API modules,
migrations, and generated API contracts. Local files stay outside web root; no S3,
email, or realtime system is added.
