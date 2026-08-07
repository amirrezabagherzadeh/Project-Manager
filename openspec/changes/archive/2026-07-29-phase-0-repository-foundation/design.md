## Context

See `proposal.md` for motivation. The repository starts documentation-first and must now gain two independently runnable applications without pulling later domain work into Foundation. Windows is a current development environment, while the resulting repository must remain portable to Linux containers. The technical constraints come from Backend PRD 1.1 BE-FR-01 and Frontend PRD 1.2 FE-FR-01.

## Goals / Non-Goals

**Goals:**

- Establish explicit root, Backend, and Frontend boundaries.
- Make each application independently installable and verifiable.
- Prove API observability through health and OpenAPI.
- Prove UI direction, theme, responsiveness, and accessibility through a minimal shell.
- Create canonical quality commands that later phases extend.

**Non-Goals:**

- Database domain models or an initial Alembic domain migration
- Authentication, authorization, Workspace, Project, or Task behavior
- Production deployment, PostgreSQL, S3, or realtime infrastructure
- Full application navigation or permanent mock product data

## Decisions

### Separate application dependency roots

`backend/` owns `pyproject.toml` and the uv lock; `frontend/` owns `package.json` and the pnpm lock. Root commands delegate rather than creating a mixed-language dependency graph.

Alternative rejected: a JavaScript monorepo orchestrator in Phase 0. It adds coupling and a dependency before build scale justifies it.

### FastAPI versioned contract from the beginning

The application configures `/api/v1/openapi.json` immediately, while `/health` remains an operational root endpoint. Swagger and ReDoc are enabled in development and driven by configuration.

OpenAPI impact: a valid initial schema is generated. The Frontend client-generation command exists but domain types arrive in later phases.

### Layer-ready Backend without empty abstraction sprawl

Foundation creates the package boundaries defined by architecture, but implements only the minimal app/config/health/error/logging path. Empty repositories and services are not generated merely to mirror the final tree.

Transaction/migration impact: no domain transaction or schema migration is introduced in Phase 0. Alembic infrastructure may be initialized, but the first domain revision belongs to Phase 1.

### Server-first Next.js shell

The root layout owns metadata, language, direction, fonts, and theme bootstrap. Interactive navigation/theme pieces become narrow Client Components. shadcn primitives and semantic Tailwind tokens form the UI base.

Alternative rejected: placing `"use client"` on the root layout, which would unnecessarily expand the client boundary.

### Cross-platform canonical commands

README documents native `uv` and `pnpm` commands. A Makefile provides convenience for Unix-like environments but is not the only executable documentation on Windows.

### Observability baseline

Backend logs are structured and include a request ID. Health responses remain stable and contain no environment secrets. Frontend errors use reusable boundaries and Persian user-facing copy.

## Risks / Trade-offs

- [Latest scaffolding defaults differ from PRDs] → Verify current official documentation, pin resulting versions, and record intentional differences.
- [RTL looks correct only on the landing shell] → Add focused RTL assertions now and retain the per-page checklist for later phases.
- [Docker works while native setup fails, or vice versa] → Verify native commands first and keep containers thin wrappers around the same entry points.
- [A placeholder API client script fails before Backend runs] → Document the Backend prerequisite and separate generation from default install/build.
- [Generated scaffolds introduce broad files] → Review and remove only unnecessary scaffold content before treating Phase 0 as complete.

## Migration Plan

1. Add root safety and documentation files.
2. Bootstrap Backend and verify health/OpenAPI/quality.
3. Bootstrap Frontend and verify RTL shell/quality.
4. Add optional container composition and root convenience commands.
5. Run both native applications and the full Phase 0 gates.

Rollback is file-level: remove the new application/tooling files. No user data or database schema exists in this phase.
