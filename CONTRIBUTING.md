# Contributing to FOSDEM Explorer

Thanks for your interest in contributing! This guide covers everything you need to get started.

## Getting Started

1. Fork the repository
2. Clone your fork and create a branch:
   ```bash
   git clone https://github.com/<your-user>/fosdem-explorer.git
   cd fosdem-explorer
   git checkout -b feat/your-feature
   ```
3. Install dev dependencies (creates a virtualenv automatically):
   ```bash
   make dev
   ```
4. Run the app locally to verify everything works:
   ```bash
   make run        # Dev server on :8001 with auto-reload
   make test       # Run the test suite
   make lint       # Linting + type checking
   ```

## Architecture

The project follows a **ports-and-adapters (hexagonal)** architecture:

| Layer | Location | Rule |
|-------|----------|------|
| **Domain** | `src/domain/` | Pure models and abstract port interfaces — no I/O or framework imports |
| **Application** | `src/application/` | Use-case services — depend only on domain ports |
| **Adapters** | `src/adapters/` | Concrete implementations (DuckDB repos, scraper, FastAPI web) |

When adding a new feature, start with the domain model and port, then the application service, then the adapter.

## Code Standards

- **Python 3.11+** — use modern syntax (`X | Y` unions, `match`, etc.)
- **Type annotations** required on all public functions and methods
- **Strict mypy** — do not add `# type: ignore` without an explanatory comment
- **ruff** handles linting and formatting (`line-length = 100`)
- Run `make lint` and `make test` before pushing

## Testing

- All new features must have corresponding tests in `tests/`
- Use `pytest` with `pytest-asyncio` for async tests
- Mock external I/O (HTTP calls, filesystem) — do not hit the real FOSDEM API in tests
- Run `make test` to execute the full suite

## Commit Messages

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) spec.
The `commit-msg` pre-commit hook enforces this. Use `make commit` for an interactive prompt.

**Format:** `<type>(<optional scope>): <short description>`

| Type       | When to use                              |
|------------|------------------------------------------|
| `feat`     | New feature visible to users             |
| `fix`      | Bug fix                                  |
| `docs`     | Documentation only                       |
| `style`    | Formatting, whitespace (no logic change) |
| `refactor` | Code restructure with no behaviour change |
| `test`     | Adding or fixing tests                   |
| `chore`    | Build scripts, deps, CI config, tooling  |
| `perf`     | Performance improvement                  |

**Examples:**
```
feat(search): add full-text search on abstracts
fix(scraper): handle missing duration field in XML
chore(deps): add commitizen to dev dependencies
```

## Pull Request Process

1. Open a PR against `main`
2. Ensure all CI checks pass (`make lint` and `make test`)
3. One approving review required before merge
4. Do not use `--no-verify` to bypass pre-commit hooks
