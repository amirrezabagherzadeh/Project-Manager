## Why

The repository currently contains product memory and planning artifacts but no runnable application foundation. Phase 0 must establish a reproducible Backend and Frontend baseline before Authentication or domain behavior can be implemented (Backend PRD 1.1 BE-FR-01, Frontend PRD 1.2 FE-FR-01; prerequisite for UC-01 through UC-12).

## What Changes

- Create the root repository structure, environment examples, ignore/editor rules, Makefile, Docker baseline, and zero-to-running README.
- Bootstrap the Python 3.12 FastAPI application with dependency management, quality commands, `/health`, Swagger, ReDoc, and versioned OpenAPI.
- Bootstrap the Next.js App Router application with TypeScript strict mode, Tailwind CSS, shadcn/ui, Persian locale, true RTL, semantic themes, and a responsive application shell.
- Establish backend and frontend test/build gates and a contract-generation script placeholder that becomes active when the API schema is available.
- Record only Phase 0 work; Authentication, database domain models, RBAC, and product features remain out of scope.

## Capabilities

### New Capabilities

- `repository-foundation`: A reproducible monorepo-style development and delivery baseline with documented commands and environment boundaries.
- `backend-foundation`: A runnable FastAPI service exposing health and API documentation with initial quality gates.
- `frontend-foundation`: A runnable Persian RTL Next.js shell with responsive, themed, accessible baseline states.

### Modified Capabilities

None.

## Impact

- Affected paths: repository root, `backend/`, `frontend/`, and delivery documentation.
- Dependencies: Node.js/pnpm, Python 3.12/uv, Docker for the optional container path.
- Public surface added: ports 3000/8000, `/health`, `/docs`, `/redoc`, `/api/v1/openapi.json`.
- Risks: framework-version drift, Windows/Linux command differences, RTL gaps, and premature coupling between the two applications.
- Rollback: remove the newly bootstrapped application directories and root tooling files; the durable PRDs/docs and OpenSpec configuration remain valid.
