## Why

Task Core can create tasks but cannot safely persist board drag-and-drop ordering.
Phase 5 delivers the atomic, versioned move contract required by BE-FR-05 and UC-06.

## What Changes

- Add the version-checked `POST /api/v1/tasks/{task_id}/move` operation.
- Atomically normalize source and target column positions, change column, synchronize
  Done/completed state, increment version, and return the final Task.
- Define stable stale-version conflict behavior and test rollback/persistence.

## Capabilities

### New Capabilities

- `backend-board-move`: Atomic, optimistic-concurrency board task movement.

### Modified Capabilities

None.

## Impact

Touches Task service/repository/schema/API tests and OpenAPI types. It depends on
the archived Task Core schema, keeps transactions short for SQLite portability, and
does not add realtime delivery or frontend behavior. Failed transactions roll back
positions, completion, and version together.
