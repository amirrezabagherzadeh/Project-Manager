## Why

Project users need read-optimized views of existing Task data for planning and
status review. Phase 7 implements the project-scoped reporting required by
BE-FR-08 and UC-05/UC-08.

## What Changes

- Add authorized project overview metrics, dashboard groups, activity, timeline,
  and calendar queries with well-defined UTC boundaries.
- Add fixture-based query and permission tests, API documentation, and generated
  contract updates.

## Capabilities

### New Capabilities

- `backend-project-views-reporting`: Project-scoped planning and reporting read views.

### Modified Capabilities

None.

## Impact

Adds read-model service/repository/API modules only; Task write semantics and
notifications remain unchanged.
