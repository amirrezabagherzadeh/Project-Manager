## 1. Collaboration foundation

- [x] 1.1 Add checklist/item, comment, attachment models and Alembic migration with indexes/FKs; verify upgrade/downgrade. (BE-FR-06)
- [x] 1.2 Add StorageService local adapter with generated filenames, containment, name/MIME/10MB validation and cleanup; verify abuse tests. (BE-FR-06)

## 2. Collaboration behavior

- [x] 2.1 Add repository/service CRUD for ordered checklist/items and progress, comments with ownership, attachment metadata/file lifecycle, and activity. (UC-07)
- [x] 2.2 Add documented REST/multipart/download endpoints with Task authorization and public schemas. (BE-FR-06)
- [x] 2.3 Add integration tests for success, 401/403/404, ownership, reorder, size/MIME/traversal, cleanup, and activity. (BE-FR-06)

## 3. Contract and phase gate

- [x] 3.1 Regenerate API schema and update README/CHANGELOG. (BE-FR-06)
- [x] 3.2 Run backend quality/OpenSpec gates and archive after verified completion. (Phase 6 gate)
