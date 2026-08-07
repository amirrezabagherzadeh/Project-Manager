.PHONY: backend-sync backend-dev backend-quality backend-migrations-check frontend-install frontend-dev frontend-quality generate-api quality migrate seed

backend-sync:
	cd backend && uv sync

backend-dev:
	cd backend && uv run fastapi dev app/main.py

backend-quality:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	cd backend && uv run mypy app
	cd backend && uv run pytest

backend-migrations-check:
	cd backend && uv run alembic heads

frontend-install:
	cd frontend && pnpm install

frontend-dev:
	cd frontend && pnpm dev

frontend-quality:
	cd frontend && pnpm lint
	cd frontend && pnpm test
	cd frontend && pnpm build
	cd frontend && pnpm e2e

generate-api:
	cd frontend && pnpm generate:api

quality: backend-quality frontend-quality
	openspec validate --all --strict

migrate:
	cd backend && uv run alembic upgrade head

seed:
	@echo "Development seed data begins in a later phase; no Phase 0 seed is available."
	@exit 1
