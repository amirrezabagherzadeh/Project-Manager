## Context

Phase 4 supplies version, position, column, and completion fields but deliberately
does not mutate column/position. See proposal.md and backend-board-move spec.

## Goals / Non-Goals

**Goals:** atomic source/target normalization, optimistic concurrency, completion
sync, resource authorization, and persistence testing.

**Non-Goals:** realtime transport, client optimistic UI, notifications API, or
cross-project moves.

## Decisions

The service owns one transaction: resolve authorized Task and target column, compare
version, fetch active source/target rows, remove the Task, insert at clamped target
index, rewrite affected positions, set completion, and increment version. Repository
queries provide only scoped rows. This portable replacement strategy is chosen over
database-specific rank/window updates for SQLite/PostgreSQL compatibility.

## Risks / Trade-offs

- [Concurrent SQLite writers] → short transaction and version conflict response.
- [Position gaps/duplicates] → normalize complete affected columns before flush.
- [Done-state drift] → completion derives only from target `is_done` within move transaction.

## Migration Plan

No schema migration is required; Phase 4 already added position/version/completion.
Rollback is transactional and the API change can be withdrawn independently.
