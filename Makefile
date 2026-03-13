.PHONY: help venv dev install run test lint format clean

PYTHON := python3.13
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

run: ## Run the application
	$(BIN)/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

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

docker-build: ## Build Docker image
	docker build -t fosdem-explorer:latest -f docker/Dockerfile .

docker-run: ## Run Docker container
	docker run -p 8000:8000 -v $(PWD)/data:/app/data fosdem-explorer:latest
