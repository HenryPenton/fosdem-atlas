# Agent Instructions

Rules and conventions for AI agents working in this repository.

---

## Project Overview

FOSDEM Explorer is a DuckDB-powered web app for browsing the FOSDEM conference
schedule. Stack: Python + FastAPI + DuckDB + HTMX + Jinja2. See
[ROADMAP.md](ROADMAP.md) for feature phases and [README.md](README.md) for
setup.

---

## Architecture

```
src/
  domain/        # Pure domain models and port interfaces (no I/O)
  application/   # Use-case services (depend only on domain ports)
  adapters/
    persistence/ # DuckDB repository implementation
    scraper/     # FOSDEM XML scraper
    web/         # FastAPI app + Jinja2 routes
  config.py      # Pydantic settings
  main.py        # App entry point
templates/       # Jinja2 HTML templates
static/          # CSS and JS assets
tests/           # pytest test suite
```

The architecture follows ports-and-adapters (hexagonal). Keep domain and
application layers free of framework or I/O imports.

---

## Development Setup

```bash
make dev       # Create venv, install deps, install pre-commit hooks
make run       # Run dev server on :8001
make test      # Run pytest
make lint      # ruff + mypy
make format    # ruff --fix + ruff format
```

DuckDB is single-process. Do not run multiple app workers against the same
database file.

---

## Coding Conventions

- **Python 3.11+** — use modern syntax (`X | Y` unions, `match`, etc.)
- **Type annotations** on all public functions and methods
- **Strict mypy** — do not add `# type: ignore` without a comment explaining
  why
- **ruff** handles linting and formatting (`line-length = 100`)
- Domain models live in `src/domain/models.py` as dataclasses
- Port interfaces live in `src/domain/ports.py` as abstract base classes
- New dependencies go in `pyproject.toml`; run `pip install -e ".[dev]"` to
  sync

---

## Testing

- All new features must have corresponding tests in `tests/`
- Use `pytest` with `pytest-asyncio` for async tests
- Mock external I/O (HTTP calls, filesystem) — do not hit the real FOSDEM API
  in tests
- Run `make test` before marking work complete and ensure all tests pass

---

## Git Commits

All commits **must** follow the [Conventional Commits](https://www.conventionalcommits.org/) spec.
The `commit-msg` pre-commit hook enforces this — non-conforming commits will
be rejected.

**Format:**

```
<type>(<optional scope>): <short description>

[optional body]

[optional footer]
```

**Types:**

| Type | When to use |
|------|-------------|
| `feat` | New feature visible to users |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, whitespace (no logic change) |
| `refactor` | Code restructure with no behaviour change |
| `test` | Adding or fixing tests |
| `chore` | Build scripts, deps, CI config, tooling |
| `perf` | Performance improvement |

**Breaking changes:** append `!` after the type (`feat!:`) and add a
`BREAKING CHANGE:` footer.

**Examples:**

```
feat(search): add full-text search on abstracts
fix(scraper): handle missing duration field in XML
chore(deps): add commitizen to dev dependencies
docs: update setup instructions in README
```

Use `make commit` for an interactive prompt that builds the message for you.

---

## Versioning & Releases

- Versions follow [SemVer](https://semver.org/)
- Run `make bump` to let commitizen determine the next version from conventional
  commits, update `CHANGELOG.md`, and create the git tag
- Push the tag (`git push --tags`) to trigger the Docker release workflow
- Do not manually edit `version` in `pyproject.toml` or `CHANGELOG.md`

---

## What Not to Do

- Do not commit directly to `main` — use feature branches and PRs
- Do not add docstrings or comments to code you did not change
- Do not add error handling for scenarios that cannot occur
- Do not over-engineer: solve the current task, not hypothetical future ones
- Do not use `--no-verify` to bypass pre-commit hooks
- Do not introduce new dependencies without justification
