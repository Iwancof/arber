.PHONY: help fmt lint typecheck test test-unit test-integration test-contract test-ui db-migrate db-verify api-validate plugin-build compose-up compose-down

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Development environment ---
compose-up:  ## Start all services (PostgreSQL, Redis, Grafana)
	docker compose up -d

compose-down:  ## Stop all services
	docker compose down

compose-logs:  ## Tail service logs
	docker compose logs -f

# --- Code quality ---
fmt:  ## Format code with ruff
	ruff format backend/ tests/

lint:  ## Lint code with ruff
	ruff check backend/ tests/

lint-fix:  ## Lint and auto-fix
	ruff check --fix backend/ tests/

typecheck:  ## Type-check with mypy
	mypy backend/

# --- Testing ---
test:  ## Run all tests
	pytest tests/ -v

test-unit:  ## Run unit tests
	pytest tests/unit/ -v

test-integration:  ## Run integration tests (requires running services)
	pytest tests/integration/ -v -m integration

test-contract:  ## Run contract tests
	pytest tests/contract/ -v -m contract

test-ui:  ## Run UI tests (placeholder)
	@echo "UI tests not yet implemented"

test-cov:  ## Run tests with coverage
	pytest tests/ --cov=backend --cov-report=html --cov-report=term

# --- Database ---
db-migrate:  ## Apply database migrations
	alembic upgrade head

db-rollback:  ## Rollback last migration
	alembic downgrade -1

db-verify:  ## Verify database schema
	python -m backend.db.verify

db-seed:  ## Seed reference data
	python -m backend.db.seed

# --- API ---
api-validate:  ## Validate OpenAPI spec (placeholder)
	@echo "OpenAPI validation not yet implemented"

dev:  ## Run development server
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# --- Grafana ---
plugin-build:  ## Build Grafana plugins (placeholder)
	@echo "Plugin build not yet implemented"
