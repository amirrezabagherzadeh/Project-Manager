## Why

The completed feature phases require reproducible startup, demo data, and a final
security and acceptance audit before delivery.

## What Changes

- Add an idempotent development-only demo seed command and document clean startup.
- Verify migration reversibility, sensitive-data boundaries, API contract, runtime
  health/docs and full HTTP acceptance flow.

## Capabilities

### New Capabilities

- `backend-hardening-seed-delivery`: Reproducible delivery verification and demo seed.

### Modified Capabilities

None.
