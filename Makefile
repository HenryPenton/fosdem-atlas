.PHONY: help venv dev install run test lint format clean commit bump patch minor major smoke-test load-test rate-limit-test cy-install cy-open cy-run cy-smoke cy-a11y

PYTHON := python3
VENV := venv
BIN := $(VENV)/bin

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

venv: $(VENV)/bin/activate ## Create virtual environment

install: venv ## Install production dependencies
	$(BIN)/pip install .

dev: venv ## Install development dependencies
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install
	$(BIN)/pre-commit install --hook-type commit-msg

run: ## Run the application
	$(BIN)/uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

run-prod: ## Run in production mode (single worker — DuckDB is single-process)
	$(BIN)/uvicorn src.main:app --host 0.0.0.0 --port 8000

test: ## Run tests
	$(BIN)/pytest

lint: ## Run linting
	$(BIN)/ruff check src tests
	$(BIN)/ruff format --check src tests
	$(BIN)/mypy src

format: ## Format code
	$(BIN)/ruff check --fix src tests
	$(BIN)/ruff format src tests

clean: ## Clean up
	rm -rf $(VENV) __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

commit: ## Create a conventional commit interactively
	$(BIN)/cz commit

# Determine optional increment level from goal (e.g. make bump patch)
_BUMP_LEVEL := $(filter patch minor major,$(MAKECMDGOALS))
_BUMP_FLAG  := $(if $(_BUMP_LEVEL),--increment $(shell echo $(_BUMP_LEVEL) | tr a-z A-Z),)

bump: ## Bump version, update CHANGELOG.md, and tag (e.g. make bump [patch|minor|major])
	$(BIN)/cz bump $(_BUMP_FLAG)

patch minor major: ## Increment level selector for use with bump (e.g. make bump patch)
	@true

docker-build: ## Build Docker image
	docker build -t fosdem-explorer:latest -f docker/Dockerfile .

docker-run: ## Run Docker container
	docker run -p 8000:8000 -v $(PWD)/data:/app/data fosdem-explorer:latest

BASE_URL ?= http://localhost:8001

smoke-test: ## Run k6 smoke test (requires k6; server must be running at BASE_URL)
	@curl -sf $(BASE_URL)/health -o /dev/null || \
	  { echo "ERROR: No server responding at $(BASE_URL) — start it first (e.g. make run)"; exit 1; }
	k6 run -e BASE_URL=$(BASE_URL) tests/load/smoke.js

load-test: ## Run k6 load test (requires k6; server must be running at BASE_URL)
	k6 run -e BASE_URL=$(BASE_URL) tests/load/load.js

rate-limit-test: ## Run k6 rate-limit test — fires 250 requests and asserts 429s are returned
	@curl -sf $(BASE_URL)/health -o /dev/null || \
	  { echo "ERROR: No server responding at $(BASE_URL) — start it first (e.g. make run)"; exit 1; }
	k6 run -e BASE_URL=$(BASE_URL) tests/load/rate_limit.js

cy-install: ## Install Cypress and dependencies
	cd cypress && npm install

cy-open: cy-install ## Open Cypress interactive runner (server must be running)
	cd cypress && npx cypress open

cy-run: cy-install ## Run all Cypress tests headlessly (server must be running)
	@curl -sf $(BASE_URL)/health -o /dev/null || \
	  { echo "ERROR: No server responding at $(BASE_URL) — start it first (e.g. make run)"; exit 1; }
	cd cypress && npx cypress run

cy-smoke: cy-install ## Run Cypress smoke tests only (server must be running)
	@curl -sf $(BASE_URL)/health -o /dev/null || \
	  { echo "ERROR: No server responding at $(BASE_URL) — start it first (e.g. make run)"; exit 1; }
	cd cypress && npx cypress run --spec 'e2e/smoke.cy.js'

cy-a11y: cy-install ## Run Cypress accessibility tests only (server must be running)
	@curl -sf $(BASE_URL)/health -o /dev/null || \
	  { echo "ERROR: No server responding at $(BASE_URL) — start it first (e.g. make run)"; exit 1; }
	cd cypress && npx cypress run --spec 'e2e/accessibility.cy.js'
