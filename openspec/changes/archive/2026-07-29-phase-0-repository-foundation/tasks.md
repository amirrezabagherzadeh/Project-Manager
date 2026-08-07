## 1. Root Repository Baseline

- [x] 1.1 Add root `.gitignore`, `.editorconfig`, safe environment examples, and the target directory skeleton; verify ignored paths cover secrets, SQLite files, uploads, caches, dependencies, and builds (`repository-foundation`: Environment and secret boundary).
- [x] 1.2 Add a cross-platform README with prerequisites and zero-to-running native commands for Backend on 8000 and Frontend on 3000; manually follow it from a clean dependency state (`repository-foundation`: Reproducible local setup).
- [x] 1.3 Add root Makefile and/or equivalent documented commands for development, quality, migration, seed, and OpenAPI generation; verify every command delegates to one application dependency root (`repository-foundation`: Phase-zero quality entry points).

## 2. Backend Foundation

- [x] 2.1 Bootstrap `backend/pyproject.toml` for Python 3.12 with FastAPI foundation dependencies and Ruff/MyPy/Pytest development tools; verify `uv sync` succeeds (Backend PRD 1.1 BE-FR-01).
- [x] 2.2 Implement `backend/app/main.py` plus focused config, request-ID/logging, and error-handler modules; verify no domain business logic or secret default is introduced (`backend-foundation`: Backend quality baseline).
- [x] 2.3 Implement `GET /health` with stable response schema and OpenAPI metadata; add success test and verify `uv run pytest` (`backend-foundation`: Backend health).
- [x] 2.4 Configure development Swagger `/docs`, ReDoc `/redoc`, OpenAPI `/api/v1/openapi.json`, and the production docs-disable option; test the schema paths and disabled behavior (`backend-foundation`: API documentation).
- [x] 2.5 Initialize Alembic infrastructure without a domain revision and document that schema changes begin in Phase 1; verify Alembic loads configuration without modifying a database.

## 3. Frontend Foundation

- [x] 3.1 Bootstrap `frontend/` with Next.js App Router, TypeScript strict mode, Tailwind CSS, ESLint, pnpm, `src/`, and `@/*`; verify `pnpm install` and `pnpm build` (Frontend PRD 1.2 FE-FR-01).
- [x] 3.2 Initialize shadcn/ui with RTL and semantic Light/Dark tokens, add the approved Persian font/fallback, and keep framework primitives composable (`frontend-foundation`: Persian RTL document).
- [x] 3.3 Implement the Server Component root layout with `lang="fa"` and `dir="rtl"`, narrow Theme/Query provider boundaries, and a minimal Persian landing/application shell; assert root language/direction in a component test.
- [x] 3.4 Implement accessible desktop-right navigation and mobile overlay navigation with visible focus and no unexpected viewport overflow; verify keyboard behavior at desktop and mobile sizes (`frontend-foundation`: Responsive application shell).
- [x] 3.5 Add reusable Persian loading skeleton, empty, error, and permission-state components with focused tests (`frontend-foundation`: Baseline UI states).
- [x] 3.6 Configure Vitest/Testing Library and Playwright entry points; add one RTL component test and one initial page smoke E2E (`frontend-foundation`: Frontend quality baseline).

## 4. Contract and Delivery Baseline

- [x] 4.1 Add `generate:api` using `openapi-typescript` against `/api/v1/openapi.json`, document the running-Backend prerequisite, and verify the generated schema from the Phase 0 API.
- [x] 4.2 Add minimal Backend and Frontend Dockerfiles plus root Compose using persistent Backend storage, without introducing production claims; verify both health/page endpoints through Compose.
- [x] 4.3 Update README and `CHANGELOG.md` with actual versions, commands, ports, OpenAPI paths, completed checks, and Phase 0 limitations.

## 5. Phase 0 Quality Gate

- [x] 5.1 Run Backend gates exactly: `cd backend && uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app`, and `uv run pytest`; fix all failures before continuing.
- [x] 5.2 Run Frontend gates exactly: `cd frontend && pnpm lint`, `pnpm test`, `pnpm build`, and `pnpm e2e`; fix all failures before continuing.
- [x] 5.3 Run `cd frontend && pnpm generate:api`, confirm the generated client matches the current OpenAPI schema, and ensure generated output policy is documented.
- [x] 5.4 Run `openspec validate --all --strict`, manually verify `/health`, `/docs`, and the Persian RTL page, then record the commands and results in the completion report.
