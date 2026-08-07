## Context

Task Core and atomic board movement are archived. Existing workspace ActivityLog is
reused as durable context, while Phase 6 adds task-specific collaboration records.

## Goals / Non-Goals

**Goals:** permission-scoped CRUD, safe local storage, physical cleanup, ordered
checklists, ownership rules, activity records, and portable migrations.

**Non-Goals:** external storage, malware scanning, realtime updates, notifications,
or rich-text comments.

## Decisions

StorageService owns generated filenames and path containment. Services authorize the
Task before coordinating storage and database transactions; public responses expose
original metadata only. Comments/checklists use service transactions; attachment
file writes are cleaned up if metadata persistence fails.

## Risks / Trade-offs

- [Path traversal/file abuse] → UUID storage names, MIME/size/name checks, containment tests.
- [Orphan files] → service cleanup on metadata deletion and persistence failure.
- [Comment IDOR] → Task access plus author/manager enforcement.

## Migration Plan

Add reversible tables after Phase 4 schema; no changes to move semantics.
