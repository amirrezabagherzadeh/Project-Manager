## 1. Move contract and persistence

- [x] 1.1 Add validated Move request/response contract and `version_conflict` error mapping; verify schema and OpenAPI tests. (BE-FR-05, UC-06)
- [x] 1.2 Add scoped repository primitives for ordered active Tasks and implement one service transaction for intra/inter-column move, position normalization, completion sync, and version increment. (BE-FR-05)

## 2. HTTP behavior and verification

- [x] 2.1 Add documented move route with resource authorization, `409 version_conflict`, and final Task envelope; verify live OpenAPI. (UC-06)
- [x] 2.2 Add integration tests for reorder, cross-column persistence, done synchronization, stale version, invalid target/index, unauthorized/IDOR, and rollback. (BE-FR-05, UC-06)

## 3. Contract and phase gate

- [x] 3.1 Regenerate API schema and update README/CHANGELOG with move semantics and limitation. (BE-FR-05)
- [x] 3.2 Run backend Ruff/format/MyPy/Pytest and strict OpenSpec validation; archive only after all checks pass. (Phase 5 gate)
